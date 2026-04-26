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
from typing import List, Optional

import pytest
from plumbum import local

from yardstick_benchmark.games.minecraft.server import MinecraftServer
from yardstick_benchmark.model import Node
from yardstick_benchmark.monitoring import InfluxDB, Telegraf


APPTAINER_PATH = shutil.which("apptainer")

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(APPTAINER_PATH is None, reason="apptainer not on PATH"),
]


def _stop_instance(name: str) -> None:
    local["apptainer"]["instance", "stop", name].run(retcode=None)


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

    influxdb = InfluxDB(node)
    telegraf = Telegraf(node)
    telegraf.set_output_influxdb2(influxdb.get_info())

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
