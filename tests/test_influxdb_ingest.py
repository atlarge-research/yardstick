"""Integration tests: InfluxDB ingest over apptainer on localhost.

These tests are slow (they pull images, start apptainer instances, and wait
for metrics to flush). Marked ``slow`` and skipped automatically when
apptainer is not on PATH.

Run with::

    pytest -m slow tests/test_influxdb_ingest.py -s
"""

import shutil
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Optional

import pytest
from plumbum import local

from yardstick_benchmark.games.minecraft.server import MinecraftServer
from yardstick_benchmark.model import Node
from yardstick_benchmark.monitoring import InfluxDB, Telegraf


APPTAINER_PATH = shutil.which("apptainer")
REPO_ROOT = Path(__file__).resolve().parent.parent
MC_SERVER_SIF = (
    REPO_ROOT
    / "yardstick_benchmark/games/minecraft/server/minecraft-server-java25-jolokia.sif"
)
CUSTOM_TELEGRAF_IMAGE = "telegraf:1.37"

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(APPTAINER_PATH is None, reason="apptainer not on PATH"),
]


def _stop_instance(name: str) -> None:
    local["apptainer"]["instance", "stop", name].run(retcode=None)


def _docker_image_present(image: str) -> bool:
    if shutil.which("docker") is None:
        return False
    return local["docker"]["image", "inspect", image].run(retcode=None)[0] == 0


def _wait_for_url(url: str, timeout_s: float, poll_s: float = 1.0) -> None:
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


def _wait_for_tcp(host: str, port: int, timeout_s: float) -> None:
    deadline = time.monotonic() + timeout_s
    last_err: Optional[Exception] = None
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return
        except (ConnectionRefusedError, OSError) as exc:
            last_err = exc
        time.sleep(2)
    raise TimeoutError(
        f"{host}:{port} not listening within {timeout_s}s (last error: {last_err!r})"
    )


@pytest.fixture
def apptainer_cleanup():
    """Yields a mutable list of apptainer instance names to stop before and
    after the test. Tests may append their own instance names to the list.
    """
    names: List[str] = ["telegraf", "influxdb"]
    for name in list(names):
        _stop_instance(name)
    yield names
    for name in names:
        _stop_instance(name)


def test_telegraf_ingests_into_influxdb(tmp_path, apptainer_cleanup):
    node = Node("localhost", tmp_path)
    nodes = [node]

    influxdb = InfluxDB(nodes)
    telegraf = Telegraf(nodes)
    telegraf.set_output_influxdb2(influxdb.get_info(nodes))

    try:
        influxdb.deploy()
        influxdb.start()
        _wait_for_url(f"http://{node.host}:8086/health", timeout_s=60)

        telegraf.deploy()
        telegraf.start()

        # Telegraf flush_interval is 10s; allow two flush windows plus margin.
        time.sleep(25)

        expected = ["cpu", "mem", "disk", "system"]
        counts = influxdb.verify_data(expected_measurements=expected)
        for measurement in expected:
            assert counts.get(measurement, 0) > 0, (
                f"no points for {measurement}; counts={counts}"
            )
    finally:
        try:
            telegraf.stop()
        except Exception:
            pass
        try:
            influxdb.stop()
        except Exception:
            pass


@pytest.mark.skipif(
    not MC_SERVER_SIF.exists(),
    reason=f"Minecraft server SIF missing at {MC_SERVER_SIF}",
)
@pytest.mark.skipif(
    not _docker_image_present(CUSTOM_TELEGRAF_IMAGE),
    reason=(
        f"custom '{CUSTOM_TELEGRAF_IMAGE}' image (with "
        "/opt/jolokia_get_minecraft_tick baked in) not present in docker daemon"
    ),
)
def test_minecraft_tick_ingests_into_influxdb(tmp_path, apptainer_cleanup):
    """End-to-end: a running Minecraft server's tick metric reaches InfluxDB
    via Telegraf's execd input + /opt/jolokia_get_minecraft_tick.
    """
    node = Node("localhost", tmp_path)
    nodes = [node]

    mc_instance = "yardstick-test-mc"
    apptainer_cleanup.append(mc_instance)

    influxdb = InfluxDB(nodes)
    # Custom Telegraf image bakes in /opt/jolokia_get_minecraft_tick, which is
    # required by the execd input configured by add_input_execd_minecraft_ticks.
    telegraf = Telegraf(
        nodes, image_url=f"docker-daemon:{CUSTOM_TELEGRAF_IMAGE}"
    )
    telegraf.set_output_influxdb2(influxdb.get_info(nodes))
    telegraf.add_input_jolokia_agent(node)
    telegraf.add_input_execd_minecraft_ticks(node)

    minecraft = MinecraftServer(name=mc_instance)
    # Point at the locally-committed SIF instead of the private registry so
    # this test is self-contained.
    minecraft.container_name = str(MC_SERVER_SIF)

    try:
        influxdb.deploy()
        influxdb.start()
        _wait_for_url(f"http://{node.host}:8086/health", timeout_s=60)

        minecraft.start()
        # Wait for the server to finish booting (game port listening) before
        # starting Telegraf so the execd Go binary finds a ticking server.
        _wait_for_tcp("localhost", 25565, timeout_s=180)

        telegraf.deploy()
        telegraf.start()

        # The Go binary needs one full collection window (1s) plus Telegraf
        # needs to flush (10s). Give it margin.
        time.sleep(30)

        counts = influxdb.verify_data(expected_measurements=["minecraft_tick"])
        assert counts["minecraft_tick"] > 0, (
            f"no minecraft_tick points; counts={counts}"
        )
    finally:
        for stop_fn in (telegraf.stop, minecraft.stop, influxdb.stop):
            try:
                stop_fn()
            except Exception:
                pass
