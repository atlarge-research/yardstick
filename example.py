"""End-to-end Yardstick example.

Brings up an InfluxDB + Telegraf + Minecraft server stack on localhost via
apptainer, runs it for a fixed window, asserts that some metrics arrived,
then tears everything down. Intended as a hands-on smoke test for a fresh
`uv add yardstick-benchmark` install.

For a multi-node setup on a DAS-style cluster, provision Nodes via
`yardstick_benchmark.provisioning.Das` and construct one InfluxDB /
Telegraf / WalkAround per node, fanning out via `util.fan_out`.
"""

from pathlib import Path
from time import sleep

import yardstick_benchmark
from yardstick_benchmark.games.minecraft.server import MinecraftServer
from yardstick_benchmark.model import Node
from yardstick_benchmark.monitoring import InfluxDB, Telegraf
from yardstick_benchmark.util import wait_for_tcp, wait_for_url


def main() -> None:
    node = Node("localhost", Path("/tmp/ysat"))

    # Wipe any leftover state from a previous run.
    yardstick_benchmark.clean([node])

    # Metrics: one InfluxDB instance, one Telegraf agent that scrapes
    # Jolokia and runs the execd minecraft_tick collector.
    influxdb = InfluxDB(node)
    telegraf = Telegraf(node, jolokia=True, execd_minecraft_ticks=True)
    telegraf.set_output_influxdb2(influxdb.get_info())

    # System under test: one Minecraft server, with Jolokia + RCON enabled.
    minecraft = MinecraftServer("yardstick-mc")

    try:
        influxdb.deploy()
        influxdb.start()
        # Wait for InfluxDB before starting Telegraf so the first batch
        # doesn't fail to write.
        wait_for_url(f"{influxdb.url}/health", timeout_s=60)

        minecraft.start()
        # Wait for the server to finish booting (game port listening) so the
        # execd minecraft_tick collector finds a ticking server when Telegraf
        # starts it.
        wait_for_tcp("localhost", 25565, timeout_s=180)

        telegraf.deploy()
        telegraf.start()

        # Give Telegraf time to flush at least one batch (flush_interval is
        # 10s) and the Go tick collector time to produce a window of data.
        run_for_s = 30
        print(f"running for {run_for_s} seconds...")
        sleep(run_for_s)

        counts = influxdb.verify_data(
            expected_measurements=["cpu", "mem", "disk", "system", "minecraft_tick"]
        )
        print(f"InfluxDB point counts by measurement: {counts}")
    finally:
        for stop_fn in (minecraft.stop, telegraf.stop, influxdb.stop):
            try:
                stop_fn()
            except Exception:
                pass


if __name__ == "__main__":
    main()
