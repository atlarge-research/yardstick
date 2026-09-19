"""Collecting node-side artifacts before the nodes are torn down.

A run's CSVs say what happened; the node's ``latest.log`` and its
``crash-reports/`` say why. Both ``Deployment`` teardown and cloud-mode
release destroy them, so they have to be copied into the results directory
first -- and that copy must never be the thing that fails a run.

These tests drive the real rsync against a fake node working directory on
localhost: no containers, no SSH, no deployment. Only
``_stage_instance_logs`` is faked where a test isn't about it, because it
reads the *real* ``~/.apptainer`` of whoever runs the suite.
"""

from pathlib import Path

import pytest
from plumbum import local

import yardstick_benchmark
from yardstick_benchmark import collect_node_artifacts, fetch
from yardstick_benchmark.model import Node


def _make_node_wd(tmp_path: Path) -> Node:
    """A working directory shaped like one a real run leaves behind."""
    wd = tmp_path / "wd"
    files = {
        # The Minecraft server: console log, crash report, effective config,
        # the world, and the agent jar staged in by deploy().
        "mc-1/data/logs/latest.log": "[12:00:00] [Server thread/INFO]: Done\n",
        "mc-1/data/logs/2026-09-19-1.log.gz": "rotated",
        "mc-1/data/crash-reports/crash-2026-09-19_12.00.00-server.txt": (
            "---- Minecraft Crash Report ----\n"
        ),
        "mc-1/data/server.properties": "view-distance=10\n",
        "mc-1/data/world/level.dat": "nbt",
        "mc-1/data/world/region/r.0.0.mca": "region data" * 100,
        "mc-1/data/world_nether/region/r.0.0.mca": "region data",
        "mc-1/jolokia.jar": "PK\x03\x04 pretend jar",
        # The metrics stack: the rendered config is worth keeping, the
        # database's storage and the compiled collector are not.
        "telegraf-ab12cd34/telegraf.conf": "[[outputs.influxdb_v2]]\n",
        "telegraf-ab12cd34/jolokia_get_minecraft_tick": "ELF binary",
        "influxdb/data/engine/data/000001.tsm": "tsm",
        # Apptainer instance logs, as _stage_instance_logs() leaves them.
        "apptainer-instance-logs/node01/jesse/mc-1.out": "server stdout\n",
        "apptainer-instance-logs/node01/jesse/mc-1.err": "server stderr\n",
    }
    for relpath, content in files.items():
        path = wd / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return Node("localhost", wd)


@pytest.fixture
def no_instance_logs(monkeypatch):
    """Don't touch the real ~/.apptainer of whoever runs the tests."""
    monkeypatch.setattr(yardstick_benchmark, "_stage_instance_logs", lambda node: None)


def _collected(dest: Path, host: str = "localhost") -> set:
    root = dest / host
    return {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}


def test_fetch_puts_each_host_in_its_own_directory(tmp_path):
    """Every node in a deployment has the same working directory *path*;
    without the host in the destination they would land on top of each
    other."""
    node = _make_node_wd(tmp_path)
    dest = tmp_path / "results" / "nodes"
    fetch(dest, [node])
    assert (dest / "localhost" / "mc-1" / "data" / "logs" / "latest.log").is_file()
    # Unfiltered, fetch() is still "the whole working directory".
    assert (dest / "localhost" / "mc-1" / "jolokia.jar").is_file()


def test_fetch_applies_include_and_exclude_rules(tmp_path):
    node = _make_node_wd(tmp_path)
    dest = tmp_path / "results" / "nodes"
    fetch(dest, [node], include=("*/", "*.log"), exclude=("*",))
    assert _collected(dest) == {"mc-1/data/logs/latest.log"}
    # Directories that nothing was kept from are pruned, rather than the
    # whole tree being recreated to hold one file.
    assert not (dest / "localhost" / "influxdb").exists()


def test_collect_keeps_the_evidence_and_leaves_the_bulk_behind(
    tmp_path, no_instance_logs
):
    dest = tmp_path / "results" / "nodes"
    hosts = collect_node_artifacts(dest, [_make_node_wd(tmp_path)])

    assert hosts == ["localhost"]
    assert _collected(dest) == {
        "mc-1/data/logs/latest.log",
        "mc-1/data/logs/2026-09-19-1.log.gz",
        "mc-1/data/crash-reports/crash-2026-09-19_12.00.00-server.txt",
        "mc-1/data/server.properties",
        "telegraf-ab12cd34/telegraf.conf",
        "apptainer-instance-logs/node01/jesse/mc-1.out",
        "apptainer-instance-logs/node01/jesse/mc-1.err",
    }
    # The world and the metrics database's raw storage stay on the node: a
    # world-generation run produces gigabytes of region files, and the
    # measurements have already been exported as CSV.
    assert not (dest / "localhost" / "mc-1" / "data" / "world").exists()
    assert not (dest / "localhost" / "influxdb").exists()


def test_collect_takes_the_world_when_asked(tmp_path, no_instance_logs):
    dest = tmp_path / "results" / "nodes"
    collect_node_artifacts(dest, [_make_node_wd(tmp_path)], keep_world=True)
    world = dest / "localhost" / "mc-1" / "data" / "world"
    assert (world / "region" / "r.0.0.mca").is_file()
    assert (world / "level.dat").is_file()
    # The other dimensions are part of the same world.
    nether = dest / "localhost" / "mc-1" / "data" / "world_nether"
    assert (nether / "region" / "r.0.0.mca").is_file()
    # ...and the logs still come along.
    assert (dest / "localhost" / "mc-1" / "data" / "logs" / "latest.log").is_file()


def test_collect_follows_the_configured_level_name(tmp_path, no_instance_logs):
    node = _make_node_wd(tmp_path)
    (node.wd / "mc-1" / "data" / "arena" / "region").mkdir(parents=True)
    (node.wd / "mc-1" / "data" / "arena" / "region" / "r.0.0.mca").write_text("x")
    dest = tmp_path / "results" / "nodes"
    collect_node_artifacts(dest, [node], keep_world=True, level_name="arena")
    assert (dest / "localhost" / "mc-1" / "data" / "arena" / "region").is_dir()
    assert not (dest / "localhost" / "mc-1" / "data" / "world").exists()


def test_collect_reports_a_node_it_could_not_read_instead_of_raising(
    tmp_path, no_instance_logs, caplog
):
    """A run that otherwise succeeded must not fail because a node went away
    -- and the exception from a run that failed must not be replaced by
    this one."""
    gone = Node("localhost", tmp_path / "never-existed")
    dest = tmp_path / "results" / "nodes"
    assert collect_node_artifacts(dest, [gone]) == []
    assert "could not collect artifacts" in caplog.text


def test_collect_survives_a_node_it_cannot_reach_at_all(tmp_path, monkeypatch):
    def unreachable(node):
        raise OSError("connection refused")

    monkeypatch.setattr(yardstick_benchmark, "_stage_instance_logs", unreachable)
    dest = tmp_path / "results" / "nodes"
    assert collect_node_artifacts(dest, [_make_node_wd(tmp_path)]) == []


def test_instance_logs_are_staged_into_the_working_directory(tmp_path):
    """`apptainer instance run` writes each container's stdout and stderr
    under ~/.apptainer, outside the directory fetch() pulls."""
    home = tmp_path / "home"
    logs = home / ".apptainer" / "instances" / "logs" / "node01" / "jesse"
    logs.mkdir(parents=True)
    (logs / "mc-1.out").write_text("server stdout\n")
    node = Node("localhost", tmp_path / "wd")
    node.wd.mkdir()

    with local.env(HOME=str(home)):
        yardstick_benchmark._stage_instance_logs(node)

    staged = node.wd / yardstick_benchmark.INSTANCE_LOG_DIR
    assert (staged / "node01" / "jesse" / "mc-1.out").read_text() == "server stdout\n"


def test_staging_instance_logs_is_a_no_op_without_any(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    node = Node("localhost", tmp_path / "wd")
    node.wd.mkdir()

    with local.env(HOME=str(home)):
        yardstick_benchmark._stage_instance_logs(node)

    assert not (node.wd / yardstick_benchmark.INSTANCE_LOG_DIR).exists()
