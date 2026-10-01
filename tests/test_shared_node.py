"""A node is not ours alone: unique instance names, and no secrets in argv.

Two assumptions used to treat a machine as exclusively ours. Instance names
were fixed strings (``influxdb``, ``telegraf``, ``yardstick-worldgen``), so a
second run on the node -- a parameter sweep, or another user -- collided with
the first, and ``apptainer instance stop <name>`` then stopped whichever
container happened to hold the name. And credentials went to apptainer as
``--env RCON_PASSWORD=...``, which every user of the node can read out of
``ps``.

Both are properties of the arguments a component *would* run, so none of this
needs a container: the fake machine below records the plumbum calls instead of
executing them.
"""

from pathlib import Path

import pytest

from yardstick_benchmark.games.minecraft.server import MinecraftServer
from yardstick_benchmark.games.minecraft.workload import WalkAround, WorldGeneration
from yardstick_benchmark.model import Node
from yardstick_benchmark.monitoring import InfluxDB, InfluxDBInfo, Telegraf
from yardstick_benchmark.util import render_env_file


NODE_WD = "/remote/wd"
RCON_PASSWORD = "s3cret-rcon-pw"
INFLUX_TOKEN = "s3cret-influx-token"


def _node():
    return Node("10.0.0.2", Path(NODE_WD), user="ubi")


class Call:
    """One command the component would have run on the node."""

    def __init__(self, name, args, stdin):
        self.name = name
        self.args = [str(a) for a in args]
        self.stdin = stdin

    def __repr__(self):
        return f"Call({self.name!r}, {self.args!r}, stdin={self.stdin is not None})"


class _FakeCommand:
    def __init__(self, calls, name, args=(), stdin=None):
        self._calls = calls
        self._name = name
        self._args = tuple(args)
        self._stdin = stdin

    def __getitem__(self, args):
        # plumbum accepts `cmd[a, b]`, `cmd[a]` and `cmd[[a, b]]` alike.
        if isinstance(args, (tuple, list)):
            args = tuple(args)
        else:
            args = (args,)
        return _FakeCommand(self._calls, self._name, self._args + args, self._stdin)

    def __lshift__(self, data):
        """plumbum's stdin redirection -- how write_private_file() keeps a
        secret out of the arguments."""
        return _FakeCommand(self._calls, self._name, self._args, data)

    def __call__(self, *args, **kwargs):
        self._calls.append(Call(self._name, self._args + args, self._stdin))
        # MinecraftServer.start() sizes the JVM heap from the node's own RAM.
        return "MemTotal:       16000000 kB\n" if self._name == "cat" else ""

    def run(self, *args, **kwargs):
        self()
        return 0, "", ""

    def popen(self, *args, **kwargs):
        self()
        return _FakeProcess()


class _FakeProcess:
    stdout = None
    stderr = None
    returncode = 0

    def poll(self):
        return 0

    def terminate(self):
        pass

    def wait(self, timeout=None):
        return 0


class _FakePath:
    def __init__(self, path):
        self.path = path

    def exists(self):
        return False

    def is_file(self):
        return False

    def is_dir(self):
        return False


class FakeMachine:
    """Stand-in for the SshMachine `remote()` yields, recording every call.

    Deliberately not a LocalMachine, so `stage()` takes its remote branch.
    """

    def __init__(self):
        self.calls = []

    def __getitem__(self, name):
        return _FakeCommand(self.calls, name)

    def path(self, p):
        return _FakePath(p)

    def upload(self, src, dst):
        self.calls.append(Call("upload", (src, dst), None))

    def close(self):
        pass


@pytest.fixture
def machine(monkeypatch):
    """Route every component's `remote()` at one fake node."""
    from contextlib import contextmanager

    from yardstick_benchmark import monitoring
    from yardstick_benchmark.games.minecraft import server as server_module
    from yardstick_benchmark.games.minecraft.workload import base as workload_base

    fake = FakeMachine()

    @contextmanager
    def fake_remote(host, user=None):
        yield fake

    for module in (monitoring, server_module, workload_base):
        monkeypatch.setattr(module, "remote", fake_remote)
    return fake


def _apptainer_args(calls):
    """Every argument of every apptainer invocation, flattened."""
    args = []
    for call in calls:
        if call.name == "apptainer":
            args += call.args
    return args


# --------------------------------------------------------------------------
# Instance names
# --------------------------------------------------------------------------


def _build(kind, **kwargs):
    """One component of `kind` on a fresh handle to the same node."""
    node = _node()
    if kind == "influxdb":
        return InfluxDB(node, **kwargs)
    if kind == "telegraf":
        return Telegraf(node, **kwargs)
    if kind == "walkaround":
        return WalkAround(node, server_host="10.0.0.1", **kwargs)
    if kind == "worldgen":
        return WorldGeneration(
            node,
            server_host="10.0.0.1",
            influxdb_info=InfluxDBInfo(["http://10.0.0.1:8086"], INFLUX_TOKEN),
            rcon_password=RCON_PASSWORD,
            **kwargs,
        )
    if kind == "minecraft":
        return MinecraftServer(node, **kwargs)
    raise AssertionError(kind)


#: Component kind -> the prefix its generated instance name should carry, so
#: `apptainer instance list` still says what a container is.
KINDS = {
    "influxdb": "influxdb-",
    "telegraf": "telegraf-",
    "walkaround": "yardstick-walkaround-",
    "worldgen": "yardstick-worldgen-",
    "minecraft": "mc-",
}


def _instance_name(component):
    return getattr(component, "instance_name", None) or component.name


@pytest.mark.parametrize("kind", sorted(KINDS))
def test_two_components_of_a_kind_on_one_node_get_different_names(kind):
    """Otherwise the second run's stop() stops the first run's container --
    or a stranger's, on a shared cluster node."""
    first, second = _build(kind), _build(kind)
    assert _instance_name(first) != _instance_name(second)
    assert _instance_name(first).startswith(KINDS[kind])


@pytest.mark.parametrize("kind", sorted(KINDS))
def test_two_components_of_a_kind_on_one_node_get_different_directories(kind):
    """The staged files have to be as separate as the instances: a shared
    working directory means one run's cleanup() deletes the other's."""
    first, second = _build(kind), _build(kind)
    assert first.wd != second.wd
    assert first.wd.startswith(NODE_WD) and second.wd.startswith(NODE_WD)


@pytest.mark.parametrize("kind", sorted(KINDS))
def test_an_explicit_name_is_still_honoured(kind):
    """A predictable name is what you want when attaching to a container by
    hand, or when it outlives the process that made it, so the argument
    stays."""
    assert _instance_name(_build(kind, name="pinned")) == "pinned"


# --------------------------------------------------------------------------
# Secrets
# --------------------------------------------------------------------------


def test_minecraft_server_start_keeps_the_rcon_password_out_of_argv(machine):
    server = MinecraftServer(_node(), rcon_password=RCON_PASSWORD)
    server.start()

    args = _apptainer_args(machine.calls)
    assert RCON_PASSWORD not in " ".join(args)
    assert "--env-file" in args
    assert args[args.index("--env-file") + 1] == server.env_file
    assert server.env_file.startswith(NODE_WD)


def test_minecraft_server_rcon_keeps_the_password_out_of_argv(machine):
    server = MinecraftServer(_node(), rcon_password=RCON_PASSWORD)
    server.rcon("setworldspawn 0 4 0")

    args = _apptainer_args(machine.calls)
    assert RCON_PASSWORD not in " ".join(args)
    assert args[args.index("--env-file") + 1] == server.rcon_env_file


def test_worldgen_keeps_the_rcon_password_and_influx_token_out_of_argv(machine):
    workload = WorldGeneration(
        _node(),
        server_host="10.0.0.1",
        influxdb_info=InfluxDBInfo(["http://10.0.0.1:8086"], INFLUX_TOKEN),
        rcon_password=RCON_PASSWORD,
    )
    workload.start()

    args = _apptainer_args(machine.calls)
    joined = " ".join(args)
    assert RCON_PASSWORD not in joined
    assert INFLUX_TOKEN not in joined
    assert args[args.index("--env-file") + 1] == workload.env_file


def test_influxdb_keeps_its_admin_credentials_out_of_argv(machine):
    influxdb = InfluxDB(_node(), admin_password="pw-hunter2", admin_token=INFLUX_TOKEN)
    influxdb.start()

    joined = " ".join(_apptainer_args(machine.calls))
    assert INFLUX_TOKEN not in joined
    assert "pw-hunter2" not in joined


def test_telegraf_keeps_the_influx_token_out_of_argv(machine):
    telegraf = Telegraf(_node())
    telegraf.set_output_influxdb2(
        InfluxDBInfo(["http://10.0.0.1:8086"], INFLUX_TOKEN),
    )
    telegraf.deploy()

    for call in machine.calls:
        assert INFLUX_TOKEN not in " ".join(call.args), call


def _private_writes(calls):
    """The (path, content) pairs written by util.write_private_file()."""
    writes = []
    for call in calls:
        if call.name == "sh" and call.stdin is not None:
            script = call.args[-1]
            assert "umask 077" in script, script
            writes.append((script, call.stdin))
    return writes


@pytest.mark.parametrize(
    "build, secret",
    [
        (
            lambda: MinecraftServer(_node(), rcon_password=RCON_PASSWORD).start(),
            RCON_PASSWORD,
        ),
        (
            lambda: InfluxDB(_node(), admin_token=INFLUX_TOKEN).start(),
            INFLUX_TOKEN,
        ),
    ],
)
def test_the_secret_lands_in_a_file_written_under_a_restrictive_umask(
    machine, build, secret
):
    """Moving a secret off the command line is only worth anything if the
    file it moves into is not world-readable. scp does not carry a local
    file's mode across, so the file is created on the node instead."""
    build()
    writes = _private_writes(machine.calls)
    assert writes, "nothing was written privately"
    assert any(secret in content for _, content in writes)


def test_write_private_file_never_puts_the_content_in_arguments(machine):
    from yardstick_benchmark.util import write_private_file

    write_private_file(machine, f"{NODE_WD}/x.env", "TOKEN=" + INFLUX_TOKEN)

    for call in machine.calls:
        assert INFLUX_TOKEN not in " ".join(call.args)
    assert any(INFLUX_TOKEN in (c.stdin or "") for c in machine.calls)


# --------------------------------------------------------------------------
# Env-file rendering
# --------------------------------------------------------------------------


def test_env_file_values_are_quoted():
    """apptainer parses an env file as a shell script, so an unquoted value
    containing a space or a `#` is a parse error rather than a value."""
    rendered = render_env_file(
        {"MOTD": "a nice # server", "RCON_PASSWORD": "it's quoted"}
    )
    assert rendered.splitlines() == [
        "MOTD='a nice # server'",
        "RCON_PASSWORD='it'\"'\"'s quoted'",
    ]


def test_env_file_renders_non_string_values():
    assert render_env_file({"PORT": 25565}) == "PORT=25565\n"
