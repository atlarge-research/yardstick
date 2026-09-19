"""Fast checks on the Python <-> JavaScript workload contract.

The workload classes pass their configuration to the Mineflayer container
purely as environment variables, so a renamed variable on either side fails
silently at run time: the bots just read `undefined` and misbehave. These
tests parse the env names out of the .js sources and assert they match what
the Python side sends. No containers, no network -- they run by default.
"""

import re
from datetime import timedelta
from pathlib import Path

import pytest

from yardstick_benchmark.games.minecraft.workload import WalkAround, WorldGeneration
from yardstick_benchmark.games.minecraft.workload.base import (
    WORKLOAD_ROOT,
    MineflayerWorkload,
)
from yardstick_benchmark.model import Node
from yardstick_benchmark.monitoring import InfluxDBInfo


ENV_RE = re.compile(r"process\.env\.([A-Z_][A-Z0-9_]*)")

INFLUX = InfluxDBInfo(["http://localhost:8086"], "token")


def _js_env_names(workload: MineflayerWorkload) -> set:
    """Every process.env.X name read by this workload's staged .js files."""
    names = set()
    for relpath in workload.FILES:
        names |= set(ENV_RE.findall((WORKLOAD_ROOT / relpath).read_text()))
    return names


def _workloads(node: Node):
    return [
        WalkAround(node, server_host="localhost", bots_per_node=3),
        WorldGeneration(
            node,
            server_host="localhost",
            influxdb_info=INFLUX,
            rcon_password="secret",
            bots_per_node=3,
        ),
    ]


@pytest.mark.parametrize("workload_index", [0, 1])
def test_js_env_vars_are_all_supplied(tmp_path, workload_index):
    workload = _workloads(Node("localhost", tmp_path))[workload_index]
    missing = _js_env_names(workload) - set(workload._env())
    assert not missing, (
        f"{type(workload).__name__} does not set {sorted(missing)}, but its "
        f"JavaScript reads them"
    )


@pytest.mark.parametrize("workload_index", [0, 1])
def test_no_env_vars_are_sent_unread(tmp_path, workload_index):
    """The mirror of the test above: an env var the Python side sets but no
    .js file reads is either a leftover from a removed feature or a typo on
    the Python side, and both look like working configuration."""
    workload = _workloads(Node("localhost", tmp_path))[workload_index]
    # NODE_OPTIONS is read by the node runtime itself, not by our scripts.
    unread = set(workload._env()) - _js_env_names(workload) - {"NODE_OPTIONS"}
    assert not unread, (
        f"{type(workload).__name__} sets {sorted(unread)}, which no staged "
        f"JavaScript reads"
    )


@pytest.mark.parametrize("workload_index", [0, 1])
def test_env_values_are_all_strings(tmp_path, workload_index):
    """apptainer --env takes KEY=VALUE strings; a stray int or timedelta here
    would be str()'d somewhere unhelpful (e.g. "0:01:00" for a timedelta)."""
    workload = _workloads(Node("localhost", tmp_path))[workload_index]
    bad = {k: v for k, v in workload._env().items() if not isinstance(v, str)}
    assert not bad, f"non-string env values: {bad}"


@pytest.mark.parametrize("workload_index", [0, 1])
def test_staged_files_exist(tmp_path, workload_index):
    """FILES are staged onto the node by path; a typo is only caught at
    deploy() time, on a real node, minutes into a run."""
    workload = _workloads(Node("localhost", tmp_path))[workload_index]
    for relpath in workload.FILES:
        assert (WORKLOAD_ROOT / relpath).is_file(), f"missing {relpath}"


@pytest.mark.parametrize("workload_index", [0, 1])
def test_entry_script_is_staged(tmp_path, workload_index):
    """The entry script must be among the files we copy over, or the
    container starts and immediately fails on a missing module."""
    workload = _workloads(Node("localhost", tmp_path))[workload_index]
    assert workload.ENTRY in workload.FILES


def test_durations_are_rendered_as_whole_seconds(tmp_path):
    node = Node("localhost", tmp_path)
    workload = WalkAround(
        node,
        server_host="localhost",
        duration=timedelta(minutes=2),
        bots_join_delay=timedelta(seconds=5),
    )
    env = workload._env()
    assert env["DURATION"] == "120"
    assert env["BOTS_JOIN_DELAY"] == "5"


def test_walkaround_timeout_covers_duration_and_joins(tmp_path):
    """A run() that times out before the workload's own duration elapses
    would kill every WalkAround run just as the last bots joined."""
    node = Node("localhost", tmp_path)
    workload = WalkAround(
        node,
        server_host="localhost",
        duration=timedelta(seconds=300),
        bots_per_node=10,
        bots_join_delay=timedelta(seconds=5),
    )
    joins = 5 * 9
    assert workload.timeout.total_seconds() > 300 + joins


def test_workloads_get_distinct_working_directories(tmp_path):
    """Two workloads on one node must not stage into the same directory, or
    cleanup() of one pulls the scripts out from under the other."""
    node = Node("localhost", tmp_path)
    a = WalkAround(node, server_host="localhost")
    b = WalkAround(node, server_host="localhost")
    assert a.wd != b.wd


def test_walkaround_needs_no_creative_mode(tmp_path):
    """WalkAround must run against a default (survival) server.

    Its entry script used to fly a bot to the box with `bot.creative.flyTo`,
    and hang the loop that starts every emulated player off that flight's
    promise. On the survival server this repo deploys by default the flight
    always failed, so no player ever joined and the run silently measured an
    idle server. Nothing in this workload may depend on creative mode again.
    """
    node = Node("localhost", tmp_path)
    workload = WalkAround(node, server_host="localhost")
    for relpath in workload.FILES:
        source = (WORKLOAD_ROOT / relpath).read_text()
        # Skip the comment that explains why this is banned.
        code = "\n".join(
            line for line in source.splitlines() if not line.lstrip().startswith("//")
        )
        assert ".creative" not in code, f"{relpath} uses the creative-mode API"


def test_walkaround_requires_no_rcon(tmp_path):
    """WalkAround deliberately needs no server-side privileges at all: the
    players just walk. If that ever changes, the RCON password has to be
    threaded through __init__ and config.py's runner context, so make the
    change deliberate rather than a silently missing env var."""
    node = Node("localhost", tmp_path)
    workload = WalkAround(node, server_host="localhost")
    assert not [name for name in _js_env_names(workload) if name.startswith("RCON")]


def _normalise(relpath: str, target: str) -> Path:
    """Resolve a require() target relative to the requiring file, textually.

    e.g. ("walkaround/main.js", "../lib.js") -> Path("lib.js")
    """
    parts: list = []
    for part in (Path(relpath).parent / target).parts:
        if part == "..":
            if parts:
                parts.pop()
        elif part != ".":
            parts.append(part)
    return Path(*parts)


def test_js_sources_have_no_unstaged_local_requires(tmp_path):
    """Every relative require() in a staged .js file must itself be staged,
    otherwise the container dies on a missing module."""
    node = Node("localhost", tmp_path)
    require_re = re.compile(r"require\(['\"](\.[^'\"]+)['\"]\)")
    for workload in _workloads(node):
        staged = {Path(f) for f in workload.FILES}
        for relpath in workload.FILES:
            src = WORKLOAD_ROOT / relpath
            for target in require_re.findall(src.read_text()):
                normalised = _normalise(relpath, target)
                assert normalised in staged, (
                    f"{relpath} requires {target} ({normalised}), which "
                    f"{type(workload).__name__} does not stage"
                )
