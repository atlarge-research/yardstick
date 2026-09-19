"""End-to-end Yardstick example.

Brings up an InfluxDB + Telegraf + Minecraft server stack on localhost via
apptainer, runs a short WalkAround workload, writes the collected metrics out
as CSV, then tears everything down. Intended as a hands-on smoke test for a
fresh install, and as a starting point for your own experiments.

If all you want is to run a standard benchmark, you don't need to write this
at all -- describe it in a configuration file instead::

    yardstick init experiment.toml
    yardstick run experiment.toml

This file is the other path: composing components yourself, which is what you
do when an experiment needs something the configuration file doesn't cover.
"""

import getpass
from datetime import timedelta
from pathlib import Path

from yardstick_benchmark.deployment import Deployment
from yardstick_benchmark.games.minecraft.server import MinecraftServer
from yardstick_benchmark.games.minecraft.workload import WalkAround
from yardstick_benchmark.model import Node
from yardstick_benchmark.monitoring import InfluxDB, Telegraf

RESULTS = Path("results/example")


def main() -> None:
    # Working dir lives on the shared /tmp, so prefix it with the username:
    # two users on one machine would otherwise collide on a single directory,
    # and whoever creates it first owns it, locking the other out.
    node = Node("localhost", Path(f"/tmp/{getpass.getuser()}-ysat"))

    # Metrics: one InfluxDB instance, one Telegraf agent that scrapes
    # Jolokia and runs the execd minecraft_tick collector.
    influxdb = InfluxDB(node)
    telegraf = Telegraf(node, jolokia=True, execd_minecraft_ticks=True)
    telegraf.set_output_influxdb2(influxdb.get_info())

    # System under test: one Minecraft server, with Jolokia + RCON enabled.
    # Pinning the seed makes every run generate the same world.
    minecraft = MinecraftServer(node, "yardstick-mc", seed="yardstick")

    # Emulated players.
    walkaround = WalkAround(
        node,
        server_host=node.host,
        duration=timedelta(seconds=60),
        bots_per_node=4,
    )

    # Deployment starts these in order and guarantees they're stopped and
    # cleaned up, whatever happens in the block -- including a failure
    # partway through starting one of them. It also waits for each
    # component that knows how to report readiness, so the database is
    # accepting writes before Telegraf starts and the server is ticking
    # before the bots connect.
    with Deployment(influxdb, minecraft, telegraf):
        minecraft.set_world_spawn(0, 0)
        # Abort the workload promptly if the server crashes under load,
        # rather than letting the bots spin against a dead server.
        minecraft.start_health_monitor()

        walkaround.deploy()
        try:
            # run() blocks until the workload's entry script exits, so we
            # learn when it actually finished instead of guessing.
            walkaround.run(health_check=minecraft.assert_healthy)
        finally:
            walkaround.cleanup()

        counts = influxdb.verify_data(
            expected_measurements=["cpu", "mem", "disk", "system", "minecraft_tick"]
        )
        print(f"InfluxDB point counts by measurement: {counts}")

        # Export inside the block: teardown stops the database and removes
        # its storage.
        written = influxdb.export_csv(RESULTS)

    print(f"wrote {len(written)} measurement file(s) to {RESULTS}")


if __name__ == "__main__":
    main()
