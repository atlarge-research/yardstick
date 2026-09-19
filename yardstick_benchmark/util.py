import os
import posixpath
import socket
import ipaddress
import string
import random
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from typing import Any, Callable, Iterable, Optional, Tuple, TypeVar

from plumbum import SshMachine, local
from plumbum.machines.local import LocalMachine


T = TypeVar("T")


def is_localhost(host: str) -> bool:
    try:
        # Resolve hostname to all addresses
        infos = socket.getaddrinfo(host, None)
        for info in infos:
            ip = info[4][0]
            if ipaddress.ip_address(ip).is_loopback:
                return True
        return False
    except Exception:
        return False


def random_string(length: int = 8) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choices(alphabet, k=length))


def fan_out(
    items: Iterable[T],
    fn: Callable[[T], None],
    max_workers: Optional[int] = None,
) -> None:
    """Apply `fn` to each item in parallel via ThreadPoolExecutor. Fail-fast:
    re-raises the first exception encountered. The remaining tasks still run
    to completion in their threads, but their results are discarded.
    """
    items = list(items)
    if not items:
        return
    with ThreadPoolExecutor(max_workers=max_workers or max(1, len(items))) as pool:
        futs = [pool.submit(fn, item) for item in items]
        for fut in as_completed(futs):
            fut.result()


def wait_for_tcp(host: str, port: int, timeout_s: float, poll_s: float = 2.0) -> None:
    """Block until a TCP connection to (host, port) succeeds, polling every
    `poll_s` seconds. Useful for waiting for a service to bind its socket
    (e.g. Minecraft on port 25565 after the JVM finishes booting).
    """
    deadline = time.monotonic() + timeout_s
    last_err: Optional[Exception] = None
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return
        except (ConnectionRefusedError, OSError) as exc:
            last_err = exc
        time.sleep(poll_s)
    raise TimeoutError(
        f"{host}:{port} not listening within {timeout_s}s (last error: {last_err!r})"
    )


def wait_for_url(url: str, timeout_s: float, poll_s: float = 1.0) -> None:
    """Block until an HTTP GET on `url` returns 200, polling every `poll_s`
    seconds. Useful for waiting for an HTTP service's health endpoint
    (e.g. InfluxDB's /health) to become reachable after start().
    """
    deadline = time.monotonic() + timeout_s
    last_err: Optional[Exception] = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, ConnectionError, OSError) as exc:
            last_err = exc
        time.sleep(poll_s)
    raise TimeoutError(
        f"{url} was not ready within {timeout_s}s (last error: {last_err!r})"
    )


# SSH options for every remote() connection.
#
# Keep long-lived SSH sessions (e.g. a foreground workload run that streams
# output for minutes) from being dropped during quiet/laggy periods: send a
# keepalive every 15s and only give up after ~8 missed (~2min), and enable
# TCP-level keepalive. BatchMode avoids a dead host hanging on a password
# prompt. The same options are handed to scp (see stage()), which otherwise
# gets none of them and would sit on a password prompt during a file upload.
_SSH_OPTS = [
    "-o",
    "ServerAliveInterval=15",
    "-o",
    "ServerAliveCountMax=8",
    "-o",
    "TCPKeepAlive=yes",
    "-o",
    "BatchMode=yes",
    # A machine provisioned seconds ago has a host key nothing has seen
    # before, and BatchMode means ssh cannot ask about it -- so without this
    # the very first connection to every new node fails. accept-new trusts a
    # key the first time but still refuses a *changed* key, which is the part
    # that actually protects against interception.
    "-o",
    "StrictHostKeyChecking=accept-new",
]


def _connect(host: str, user: Optional[str] = None) -> Tuple[Any, bool]:
    """Open a plumbum machine for `host`.

    Returns ``(machine, owned)``. ``owned`` says whether the caller is
    responsible for closing it: a localhost "connection" is the process-wide
    `local` machine, which is shared and must never be closed.
    """
    if is_localhost(host):
        return local, False
    machine = SshMachine(
        host,
        user=user,
        ssh_opts=_SSH_OPTS,
        scp_opts=_SSH_OPTS,
    )
    return machine, True


@contextmanager
def remote(host: str, user: Optional[str] = None):
    """Yield a plumbum machine for `host`, closing it on exit if it's an SSH
    connection. For localhost, yields the global `local` machine which has
    no per-use lifecycle.

    `user` is the SSH login name. Without it plumbum connects as whoever is
    running Yardstick, which is correct on a cluster where the accounts match
    but wrong for a provisioned VM, where the image decides the login user.

    Remote machines are opened with SSH keepalives so a long foreground
    command (e.g. a workload's run()) doesn't get its connection torn down.

    This is the right tool for a one-off: a deploy step, a cleanup, an RCON
    command. A caller that runs many small commands over a long period (a
    poll loop) should hold a :class:`RemoteSession` instead, which opens one
    connection and keeps it.
    """
    machine, owned = _connect(host, user)
    try:
        yield machine
    finally:
        if owned:
            machine.close()


class RemoteSession:
    """One connection to a node, held open across many commands.

    :func:`remote` opens a connection per use, which is right for a deploy
    step but wasteful in a loop. Worse, plumbum spawns a *second* ``ssh``
    process for every command run on a machine (only path operations reuse
    the machine's own shell session), so a poll that builds a machine and
    runs one command costs two SSH handshakes. A few hundred polls is a few
    hundred handshakes, each one a fresh chance for a network hiccup to look
    like a failure.

    A ``RemoteSession`` connects once, lazily, and runs every command through
    a single plumbum shell session on that connection -- which is what shell
    sessions are for: "they allow us to send multiple commands over a single
    SSH connection". Per-command cost after the first is zero connections.

    Thread safety: connecting is serialised, so several threads sharing one
    session still open only one connection, and plumbum's own shell session
    serialises the commands run on it. :meth:`close` does not hold that lock
    while it tears the connection down, so it can be called from another
    thread to unblock one that is stuck in a remote command.

    Lifecycle: the owner must call :meth:`close`. It is idempotent, and a
    closed session reconnects on next use -- which is also how a caller
    recovers from a dropped connection: close it and carry on.

        conn = RemoteSession(node.host, node.user)
        try:
            while running:
                conn.run(conn.machine["grep"]["-q", "boom", log])
        finally:
            conn.close()
    """

    def __init__(self, host: str, user: Optional[str] = None) -> None:
        self.host = host
        self.user = user
        # Guards connecting only. Held briefly, and never while a command is
        # running, so close() from another thread cannot deadlock on it.
        self._lock = threading.Lock()
        self._machine: Any = None
        self._session: Any = None
        self._owned = False

    def _ensure(self) -> Tuple[Any, Any]:
        with self._lock:
            if self._machine is None:
                self._machine, self._owned = _connect(self.host, self.user)
            if self._session is None:
                self._session = self._machine.session()
            return self._machine, self._session

    @property
    def machine(self) -> Any:
        """The plumbum machine, connecting on first use.

        Use it for path operations (``machine.path(...)``), which plumbum
        already runs over the machine's own connection, and to build the
        command objects handed to :meth:`run`.
        """
        return self._ensure()[0]

    def run(self, cmd, retcode=None):
        """Run a plumbum command object over the held connection.

        Returns plumbum's ``(retcode, stdout, stderr)``. Pass the command as
        an unexecuted plumbum command (``session.machine["grep"][args]``);
        it is shell-quoted by plumbum, not by string formatting here.
        """
        _, session = self._ensure()
        # ShellSession only accepts a command *string*; formulate() is the
        # documented way to get a shell-quoted command line out of a plumbum
        # command object (passing the object itself hits a plumbum bug).
        return session.run(" ".join(cmd.formulate(1)), retcode=retcode)

    def close(self) -> None:
        """Tear the connection down. Idempotent; the next use reconnects."""
        with self._lock:
            machine, session, owned = self._machine, self._session, self._owned
            self._machine = self._session = None
            self._owned = False
        # Outside the lock: closing kills the underlying ssh processes, which
        # is what unblocks a thread waiting on a command that will never
        # answer -- and that thread may want the lock on its way out.
        if session is not None:
            try:
                session.close()
            except Exception:
                pass
        if machine is not None and owned:
            try:
                machine.close()
            except Exception:
                pass

    def __enter__(self) -> "RemoteSession":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def stage(machine, src, dst: str) -> None:
    """Copy the local file `src` onto `machine` at path `dst`.

    Works for either kind of machine yielded by :func:`remote`: a local node
    gets a plain filesystem copy, a genuinely remote one an ``scp`` upload
    via plumbum's ``machine.upload()``. (``LocalPath.copy()`` cannot be used
    for the remote case -- it rejects a ``RemotePath`` destination outright,
    with a ``TypeError`` from deep inside plumbum.)

    The destination's parent directories are created first, on whichever side
    the destination lives. Callers stage into paths such as
    ``{node.wd}/walkaround-ab12cd34/walkaround/main.js`` whose intermediate
    directories do not exist yet, and ``scp`` will not create them.

    An executable `src` is staged as an executable: ``scp`` does not reliably
    carry the mode across (OpenSSH's SFTP-backed scp drops it unless given
    ``-p``), and the Go collector staged by ``Telegraf.deploy()`` has to be
    runnable on the node.
    """
    src_path = local.path(src)
    if not src_path.is_file():
        raise FileNotFoundError(f"cannot stage {src_path}: not a readable file")

    parent = posixpath.dirname(dst)
    if parent:
        machine["mkdir"]["-p", parent]()

    if isinstance(machine, LocalMachine):
        # shutil-backed, and already mode-preserving.
        src_path.copy(machine.path(dst))
    else:
        machine.upload(str(src_path), dst)

    if os.access(str(src_path), os.X_OK):
        machine["chmod"]["+x", dst]()
