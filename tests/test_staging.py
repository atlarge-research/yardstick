"""Staging files onto a node, local or remote.

``util.stage()`` is the one place that copies a locally-produced file (a
rendered Telegraf config, the compiled Go collector, a workload's ``.js``
files) onto the node that will use it. The remote half used to be missing
entirely -- plumbum's ``LocalPath.copy()`` refuses a ``RemotePath``
destination -- so these tests pin down the behaviour that replaced it.

The remote cases run against a fake machine rather than a second host: the
things worth asserting are *which* plumbum calls stage() makes and in what
order, and `is_localhost()` treats loopback addresses as local, so there is no
way to reach the remote branch by naming a loopback host. A real end-to-end
upload is covered only by the ``slow`` SSH test at the bottom.
"""

import os
import stat
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path

import pytest
from plumbum import local

from yardstick_benchmark.model import Node
from yardstick_benchmark.util import stage


class _FakeCommand:
    """A plumbum-style bound command that logs instead of executing."""

    def __init__(self, log, name, args=()):
        self._log = log
        self._name = name
        self._args = tuple(args)

    def __getitem__(self, args):
        if not isinstance(args, tuple):
            args = (args,)
        return _FakeCommand(self._log, self._name, self._args + args)

    def __call__(self, *args):
        self._log.append((self._name,) + tuple(str(a) for a in self._args + args))
        return ""


class FakeRemoteMachine:
    """Stand-in for the SshMachine that `remote()` yields for a real node.

    Deliberately *not* a LocalMachine, so stage() takes its remote branch.
    Records every command run and every upload into one ordered log, which is
    what lets a test assert that the parent directory is created *before* the
    file lands in it.
    """

    def __init__(self):
        self.calls = []

    def __getitem__(self, name):
        return _FakeCommand(self.calls, name)

    def upload(self, src, dst):
        self.calls.append(("upload", str(src), str(dst)))

    def close(self):
        pass


@pytest.fixture
def src_file(tmp_path):
    path = tmp_path / "telegraf.conf"
    path.write_text("[agent]\n")
    return path


def test_remote_stage_creates_parent_before_uploading(src_file):
    machine = FakeRemoteMachine()

    stage(machine, src_file, "/node/wd/telegraf-ab12cd34/telegraf.conf")

    assert machine.calls == [
        ("mkdir", "-p", "/node/wd/telegraf-ab12cd34"),
        ("upload", str(src_file), "/node/wd/telegraf-ab12cd34/telegraf.conf"),
    ]


def test_remote_stage_creates_every_missing_level(src_file):
    """Workloads stage into `{wd}/walkaround-ab12cd34/walkaround/main.js`;
    several levels of that do not exist yet, and scp creates none of them."""
    machine = FakeRemoteMachine()

    stage(machine, src_file, "/node/wd/walkaround-ab12cd34/walkaround/main.js")

    mkdirs = [c for c in machine.calls if c[0] == "mkdir"]
    assert mkdirs == [("mkdir", "-p", "/node/wd/walkaround-ab12cd34/walkaround")]
    # `mkdir -p` is what makes this one call enough for a multi-level path.
    assert "-p" in mkdirs[0]


def test_remote_stage_makes_an_executable_source_executable(tmp_path):
    """scp does not reliably carry the mode across -- OpenSSH's SFTP-backed
    scp drops it without -p -- so stage() restores it itself."""
    binary = tmp_path / "jolokia_get_minecraft_tick"
    binary.write_bytes(b"\x7fELF")
    binary.chmod(0o755)
    machine = FakeRemoteMachine()

    stage(machine, binary, "/node/wd/telegraf-ab12cd34/jolokia_get_minecraft_tick")

    assert machine.calls == [
        ("mkdir", "-p", "/node/wd/telegraf-ab12cd34"),
        (
            "upload",
            str(binary),
            "/node/wd/telegraf-ab12cd34/jolokia_get_minecraft_tick",
        ),
        ("chmod", "+x", "/node/wd/telegraf-ab12cd34/jolokia_get_minecraft_tick"),
    ]


def test_remote_stage_leaves_a_plain_file_alone(src_file):
    machine = FakeRemoteMachine()

    stage(machine, src_file, "/node/wd/telegraf-ab12cd34/telegraf.conf")

    assert not [c for c in machine.calls if c[0] == "chmod"]


def test_stage_rejects_a_missing_source(tmp_path):
    machine = FakeRemoteMachine()

    with pytest.raises(FileNotFoundError):
        stage(machine, tmp_path / "nope.js", "/node/wd/nope.js")

    assert machine.calls == []


def test_local_stage_copies_content_and_creates_parents(src_file, tmp_path):
    dst = tmp_path / "wd" / "telegraf-ab12cd34" / "telegraf.conf"

    stage(local, src_file, str(dst))

    assert dst.read_text() == "[agent]\n"


def test_local_stage_keeps_the_executable_bit(tmp_path):
    binary = tmp_path / "jolokia_get_minecraft_tick"
    binary.write_bytes(b"\x7fELF")
    binary.chmod(0o755)
    dst = tmp_path / "wd" / "telegraf-ab12cd34" / "jolokia_get_minecraft_tick"

    stage(local, binary, str(dst))

    assert dst.stat().st_mode & stat.S_IXUSR


@contextmanager
def _yield(machine):
    yield machine


def _patch_remote(monkeypatch, module, machine):
    monkeypatch.setattr(module, "remote", lambda host, user=None: _yield(machine))


def test_workload_deploy_stages_every_file_to_a_remote_node(monkeypatch):
    """The MineflayerWorkload call site, end to end against a fake node."""
    from yardstick_benchmark.games.minecraft.workload import base as workload_base
    from yardstick_benchmark.games.minecraft.workload.walkaround import WalkAround

    machine = FakeRemoteMachine()
    _patch_remote(monkeypatch, workload_base, machine)

    workload = WalkAround(
        Node("node001", Path("/var/scratch/jesse")),
        server_host="node002",
        duration=timedelta(seconds=1),
    )
    workload.deploy()

    uploaded = [c[2] for c in machine.calls if c[0] == "upload"]
    assert uploaded == [f"{workload.wd}/{relpath}" for relpath in WalkAround.FILES]
    # Each upload is preceded by the mkdir for its own directory.
    for i, call in enumerate(machine.calls):
        if call[0] == "upload":
            assert machine.calls[i - 1][0] == "mkdir"
            assert call[2].startswith(machine.calls[i - 1][2] + "/")


def test_telegraf_deploy_stages_an_executable_collector_to_a_remote_node(monkeypatch):
    """The other call site: the Go binary must arrive runnable."""
    from yardstick_benchmark import monitoring
    from yardstick_benchmark.monitoring import InfluxDBInfo, Telegraf

    machine = FakeRemoteMachine()
    _patch_remote(monkeypatch, monitoring, machine)

    telegraf = Telegraf(
        Node("node001", Path("/var/scratch/jesse")),
        execd_minecraft_ticks=True,
    )
    telegraf.set_output_influxdb2(InfluxDBInfo(["http://node002:8086"], "token"))
    telegraf.deploy()

    binary_src = Path(monitoring.__file__).parent / "jolokia_get_minecraft_tick"
    binary_dst = f"{telegraf.wd}/jolokia_get_minecraft_tick"
    assert ("upload", str(binary_src), binary_dst) in machine.calls
    assert ("chmod", "+x", binary_dst) in machine.calls
    # The rendered config goes up too, and is not made executable.
    config_uploads = [
        c for c in machine.calls if c[0] == "upload" and c[2].endswith("telegraf.conf")
    ]
    assert len(config_uploads) == 1
    assert ("chmod", "+x", f"{telegraf.wd}/telegraf.conf") not in machine.calls


@pytest.mark.slow
def test_stage_over_real_ssh_to_localhost(tmp_path):
    """The only test that exercises a genuine scp upload.

    Marked slow, and skipped unless sshd is reachable with key-based auth --
    `is_localhost()` sends "localhost" down the *local* branch, so this has to
    build an SshMachine by hand to reach the remote one.
    """
    from plumbum import SshMachine
    from yardstick_benchmark.util import _SSH_KEEPALIVE_OPTS

    try:
        machine = SshMachine(
            "localhost",
            ssh_opts=_SSH_KEEPALIVE_OPTS,
            scp_opts=_SSH_KEEPALIVE_OPTS,
        )
    except Exception as exc:
        pytest.skip(f"no key-based SSH to localhost: {exc!r}")

    binary = tmp_path / "collector"
    binary.write_text("#!/bin/sh\nexit 0\n")
    binary.chmod(0o755)
    dst = tmp_path / "wd" / "telegraf-ab12cd34" / "collector"

    try:
        stage(machine, binary, str(dst))
    finally:
        machine.close()

    assert dst.read_text() == "#!/bin/sh\nexit 0\n"
    assert os.access(str(dst), os.X_OK)
