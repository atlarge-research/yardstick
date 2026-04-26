"""Integration tests: InfluxDB ingest over apptainer on localhost.

These tests are slow (they pull images, start apptainer instances, and wait
for metrics to flush). Marked ``slow`` and skipped automatically when
apptainer is not on PATH.

Run with::

    pytest -m slow tests/test_influxdb_ingest.py -s
"""

import shutil
import time
from typing import List

import pytest
from plumbum import local

from yardstick_benchmark.games.minecraft.server import MinecraftServer
from yardstick_benchmark.model import Node
from yardstick_benchmark.monitoring import InfluxDB, Telegraf
from yardstick_benchmark.util import wait_for_url


APPTAINER_PATH = shutil.which("apptainer")

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(APPTAINER_PATH is None, reason="apptainer not on PATH"),
]


def _stop_instance(name: str) -> None:
    local["apptainer"]["instance", "stop", name].run(retcode=None)


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

    influxdb = InfluxDB(node)
    telegraf = Telegraf(node)
    telegraf.set_output_influxdb2(influxdb.get_info())

    try:
        influxdb.deploy()
        influxdb.start()
        wait_for_url(f"http://{node.host}:8086/health", timeout_s=60)

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


def test_minecraft_tick_ingests_into_influxdb(tmp_path, apptainer_cleanup):
    """End-to-end: a running Minecraft server's tick metric reaches InfluxDB
    via Telegraf's execd input + /opt/jolokia_get_minecraft_tick.
    """
    node = Node("localhost", tmp_path)

    mc_instance = "yardstick-test-mc"
    apptainer_cleanup.append(mc_instance)

    influxdb = InfluxDB(node)
    telegraf = Telegraf(node, jolokia=True, execd_minecraft_ticks=True)
    telegraf.set_output_influxdb2(influxdb.get_info())

    minecraft = MinecraftServer(name=mc_instance)

    try:
        influxdb.deploy()
        influxdb.start()
        wait_for_url(f"http://{node.host}:8086/health", timeout_s=60)

        minecraft.start()
        # Wait for the server to be fully ready (RCON port up, "Done!"
        # logged) before starting Telegraf so the execd Go binary finds a
        # ticking server.
        minecraft.wait_until_ready()

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


def test_minecraft_set_world_spawn(apptainer_cleanup):
    """Exercise MinecraftServer.rcon() (via set_world_spawn): verifies the
    `apptainer exec instance://...` path works against a running MC server.
    """
    mc_instance = "yardstick-test-mc-rcon"
    apptainer_cleanup.append(mc_instance)

    minecraft = MinecraftServer(name=mc_instance)
    try:
        minecraft.start()
        minecraft.wait_until_ready()
        # rcon-cli exits non-zero if the command fails or RCON refuses; a
        # successful setworldspawn returns "Set the world spawn point to ...".
        # plumbum raises ProcessExecutionError on non-zero, so passing here
        # means the round-trip worked.
        minecraft.set_world_spawn(7, 8)
    finally:
        try:
            minecraft.stop()
        except Exception:
            pass
