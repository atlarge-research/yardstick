"""One connection per poll loop, not one per poll.

``remote()`` opens and closes a connection per use. That is right for a
deploy step, but the Minecraft health monitor polls every five seconds for
the length of a run -- hundreds of connections to ask a question whose
answer is almost always "no", each one a chance for a network hiccup to look
like a crash. :class:`RemoteSession` holds one connection instead.

These run against a fake machine: what is worth pinning is *how many*
connections a caller opens and whether it closes them, which is exactly what
a real SSH connection makes impossible to observe.
"""

import threading
import time
from contextlib import contextmanager

import pytest

import yardstick_benchmark.util as util
from yardstick_benchmark.games.minecraft.server import (
    MinecraftServer,
    MinecraftServerCrashed,
)
from yardstick_benchmark.model import Node
from yardstick_benchmark.util import RemoteSession


class FakeCommand:
    """A plumbum-style bound command that only knows how to spell itself."""

    def __init__(self, name, args=()):
        self.name = name
        self.args = tuple(args)

    def __getitem__(self, args):
        if not isinstance(args, tuple):
            args = (args,)
        return FakeCommand(self.name, self.args + args)

    def formulate(self, level=0, args=()):
        return [self.name, *(str(a) for a in self.args)]


class FakePath:
    def __init__(self, machine, path):
        self._machine = machine
        self._path = str(path)

    def __str__(self):
        return self._path

    def is_dir(self):
        return self._path in self._machine.dirs

    def is_file(self):
        return self._path in self._machine.files

    def __floordiv__(self, pattern):
        return [
            FakePath(self._machine, p) for p in self._machine.dirs.get(self._path, ())
        ]


class FakeSession:
    """Stands in for plumbum's ShellSession: commands run over one pipe."""

    def __init__(self, machine):
        self._machine = machine
        self.closed = False

    def run(self, cmd, retcode=None):
        if self.closed:
            raise RuntimeError("shell session has already been closed")
        return self._machine._run(cmd, retcode)

    def close(self):
        self.closed = True


class FakeMachine:
    """Stands in for the SshMachine ``remote()`` yields for a real node."""

    def __init__(self, responses=None, files=(), dirs=None):
        self.commands = []
        self.sessions = []
        self.closed = False
        self.files = set(files)
        self.dirs = dict(dirs or {})
        # name -> (retcode, stdout) or an exception to raise.
        self.responses = dict(responses or {})

    def __getitem__(self, name):
        return FakeCommand(name)

    def path(self, p):
        return FakePath(self, p)

    def session(self):
        session = FakeSession(self)
        self.sessions.append(session)
        return session

    def close(self):
        self.closed = True

    def _run(self, cmd, retcode):
        self.commands.append(cmd)
        name = cmd.split()[0]
        answer = self.responses.get(name, (1, ""))
        if isinstance(answer, Exception):
            raise answer
        code, out = answer
        if retcode is not None and code != retcode:
            raise RuntimeError(f"{name} exited with {code}")
        return code, out, ""


@pytest.fixture
def connections(monkeypatch):
    """Record every connection RemoteSession opens, and hand out fakes.

    Append a FakeMachine to ``connections.queue`` to control what the *next*
    connection answers; otherwise a default one is made.
    """

    class Recorder:
        def __init__(self):
            self.opened = []
            self.queue = []

        def _connect(self, host, user=None):
            machine = self.queue.pop(0) if self.queue else FakeMachine()
            machine.host, machine.user = host, user
            self.opened.append(machine)
            return machine, True

    recorder = Recorder()
    monkeypatch.setattr(util, "_connect", recorder._connect)
    return recorder


# --------------------------------------------------------------------------
# RemoteSession itself
# --------------------------------------------------------------------------


def test_many_commands_share_one_connection(connections):
    conn = RemoteSession("node-1", "ubi")
    for _ in range(10):
        conn.run(conn.machine["true"])
    conn.close()

    assert len(connections.opened) == 1
    machine = connections.opened[0]
    assert len(machine.sessions) == 1
    assert len(machine.commands) == 10


def test_nothing_is_connected_until_it_is_used(connections):
    RemoteSession("node-1")
    assert connections.opened == []


def test_close_tears_down_the_connection(connections):
    conn = RemoteSession("node-1")
    conn.run(conn.machine["true"])
    conn.close()

    machine = connections.opened[0]
    assert machine.closed
    assert machine.sessions[0].closed


def test_close_is_idempotent(connections):
    conn = RemoteSession("node-1")
    conn.run(conn.machine["true"])
    conn.close()
    conn.close()
    assert len(connections.opened) == 1


def test_use_after_close_reconnects(connections):
    """How a caller recovers from a dropped connection: close, carry on."""
    conn = RemoteSession("node-1")
    conn.run(conn.machine["true"])
    conn.close()
    conn.run(conn.machine["true"])
    conn.close()

    assert len(connections.opened) == 2
    assert all(m.closed for m in connections.opened)


def test_the_local_machine_is_never_closed(monkeypatch):
    """`local` is process-wide and shared; closing it would break every other
    component in the run."""
    sentinel = FakeMachine()
    monkeypatch.setattr(util, "_connect", lambda host, user=None: (sentinel, False))

    conn = RemoteSession("localhost")
    conn.run(conn.machine["true"])
    conn.close()

    assert not sentinel.closed
    assert sentinel.sessions[0].closed


def test_concurrent_first_use_opens_one_connection(connections):
    """Machines are provisioned concurrently and the health monitor runs on
    its own thread, so a session can be raced into existence."""
    conn = RemoteSession("node-1")
    start = threading.Barrier(8)
    errors = []

    def worker():
        try:
            start.wait(timeout=5)
            for _ in range(20):
                conn.run(conn.machine["true"])
        except Exception as exc:  # pragma: no cover - only on a real race
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    conn.close()

    assert errors == []
    assert len(connections.opened) == 1
    assert len(connections.opened[0].sessions) == 1
    assert len(connections.opened[0].commands) == 8 * 20


def test_close_from_another_thread_does_not_wait_for_a_stuck_command(connections):
    """A command against a node that stopped answering must not make close()
    -- the thing that unblocks it -- hang too."""
    release = threading.Event()

    class BlockingMachine(FakeMachine):
        def _run(self, cmd, retcode):
            release.wait(timeout=10)
            return super()._run(cmd, retcode)

    connections.queue.append(BlockingMachine())
    conn = RemoteSession("node-1")
    stuck = threading.Thread(target=lambda: conn.run(conn.machine["sleep"]))
    stuck.start()
    time.sleep(0.05)

    closed = threading.Event()

    def closer():
        conn.close()
        closed.set()

    threading.Thread(target=closer).start()
    assert closed.wait(timeout=5), "close() blocked behind the running command"

    release.set()
    stuck.join(timeout=5)


# --------------------------------------------------------------------------
# The health monitor, which is what prompted all this
# --------------------------------------------------------------------------


LOG = "/wd/mc-test/data/logs/latest.log"


def _server():
    return MinecraftServer(Node("node-1", "/wd", user="ubi"), name="mc-test")


def _healthy_machine():
    return FakeMachine(files=[LOG], responses={"grep": (1, "")})


def _crashed_machine():
    return FakeMachine(
        files=[LOG],
        responses={"grep": (0, "java.lang.OutOfMemoryError\n")},
    )


def _wait_for(predicate, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


@contextmanager
def _monitoring(server, interval_s=0.01):
    """Run the health monitor for the body, and always stop it -- a leaked
    monitor thread would go on polling into the next test."""
    server.start_health_monitor(interval_s=interval_s)
    try:
        yield
    finally:
        server.stop_health_monitor()


def _polled(connections, times):
    """True once the monitor's first connection has run `times` commands."""
    return lambda: (
        bool(connections.opened) and len(connections.opened[0].commands) >= times
    )


def test_polling_many_times_opens_one_connection(connections):
    connections.queue.append(_healthy_machine())
    server = _server()
    with _monitoring(server):
        assert _wait_for(_polled(connections, 10))

    assert len(connections.opened) == 1
    assert len(connections.opened[0].sessions) == 1
    server.assert_healthy()


def test_stopping_the_monitor_closes_its_connection(connections):
    connections.queue.append(_healthy_machine())
    server = _server()
    with _monitoring(server):
        assert _wait_for(_polled(connections, 2))

    machine = connections.opened[0]
    assert machine.closed
    assert all(s.closed for s in machine.sessions)


def test_a_crash_still_stops_the_monitor_and_closes_up(connections):
    connections.queue.append(_crashed_machine())
    server = _server()
    with _monitoring(server):
        assert _wait_for(lambda: server._crash is not None)
        assert _wait_for(lambda: connections.opened[0].closed)
        with pytest.raises(MinecraftServerCrashed, match="OutOfMemoryError"):
            server.assert_healthy()


def test_a_broken_connection_is_dropped_and_the_monitor_reconnects(connections):
    """A node that goes away for a moment must not blind the monitor for the
    rest of the run -- the point of reusing a connection is lost if a dead
    one is reused."""
    broken = FakeMachine(files=[LOG], responses={"grep": OSError("connection lost")})
    connections.queue.append(broken)
    connections.queue.append(_crashed_machine())

    server = _server()
    with _monitoring(server):
        assert _wait_for(lambda: server._crash is not None), (
            "monitor never recovered from the broken connection"
        )

    assert len(connections.opened) == 2
    assert broken.closed
    with pytest.raises(MinecraftServerCrashed):
        server.assert_healthy()


def test_a_one_off_check_closes_its_connection(connections):
    """raise_if_crashed() is still a self-contained one-off for callers that
    just want to ask once."""
    connections.queue.append(_healthy_machine())
    _server().raise_if_crashed()

    assert len(connections.opened) == 1
    assert connections.opened[0].closed


def test_stop_without_start_is_harmless(connections):
    _server().stop_health_monitor()
    assert connections.opened == []
