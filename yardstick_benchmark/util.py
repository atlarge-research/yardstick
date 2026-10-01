import os
import posixpath
import shlex
import socket
import ipaddress
import string
import random
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from typing import Callable, Iterable, Mapping, Optional, TypeVar

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


def unique_instance_name(prefix: str) -> str:
    """An apptainer instance name no concurrent run will also pick.

    Instance names are a flat, per-user namespace on a node, so a fixed
    default like ``telegraf`` makes two runs on one machine -- two people on
    a shared cluster node, or one person's parameter sweep -- fight over a
    single name. Worse, teardown issues ``apptainer instance stop
    <name>``, which then stops whichever container got the name first,
    possibly someone else's. A uuid suffix removes the collision; the
    prefix keeps ``apptainer instance list`` readable.
    """
    return f"{prefix}-{uuid.uuid4()}"


def render_env_file(env: Mapping[str, str]) -> str:
    """Render `env` in the format apptainer's ``--env-file`` expects.

    Apptainer evaluates an env file as a shell script (with command
    execution disabled) and then expands ``$VAR`` references in the
    resulting values -- exactly what it already does to a ``--env
    KEY=VALUE`` argument. So every value is shell-quoted here: without that,
    a value containing a space or a ``#`` is a parse error rather than a
    value. The one behavioural difference from ``--env`` is in our favour:
    apptainer *does* run command substitutions in a ``--env`` argument, and
    refuses to run them in an env file.
    """
    return "".join(f"{key}={shlex.quote(str(value))}\n" for key, value in env.items())


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
    """
    if is_localhost(host):
        yield local
        return
    machine = SshMachine(
        host,
        user=user,
        ssh_opts=_SSH_OPTS,
        scp_opts=_SSH_OPTS,
    )
    try:
        yield machine
    finally:
        machine.close()


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


def write_private_file(machine, dst: str, content: str) -> None:
    """Write `content` to `dst` on `machine` as a file only its owner can read.

    This is how every file holding a credential gets onto a node: the
    apptainer ``--env-file`` carrying the RCON password, and Telegraf's
    rendered config carrying the InfluxDB admin token. Two things matter
    here that :func:`stage` does not give:

    * The content travels on the helper command's *stdin*, never in its
      arguments, so it does not show up in the node's process list -- which
      is the whole reason for moving it off the apptainer command line.
    * The file is created under ``umask 077``, so it is never even briefly
      world-readable. Staging a locally-created mode-0600 file would not do:
      ``scp`` does not carry the source's mode across, so the same file
      lands 0600 on a local node and world-readable on a remote one. An
      existing file is removed first, because a redirect into one keeps
      whatever mode it already had.

    Parent directories are created first, as in :func:`stage`.
    """
    parent = posixpath.dirname(dst)
    if parent:
        machine["mkdir"]["-p", parent]()
    quoted = shlex.quote(dst)
    script = f"umask 077 && rm -f {quoted} && cat > {quoted}"
    (machine["sh"]["-c", script] << content)()
