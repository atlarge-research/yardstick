from yardstick_benchmark.model import RemoteApplication, Node
from pathlib import Path
import os
from datetime import timedelta


class WalkAround(RemoteApplication):
    def __init__(
        self,
        nodes: list[Node],
        server_host: str,
        duration: timedelta = timedelta(seconds=60),
        spawn_x: int = 0,
        spawn_y: int = 0,
        box_width: int = 32,
        box_x: int = -16,
        box_z: int = -16,
        bots_join_delay: timedelta = timedelta(seconds=5),
        bots_per_node: int = 1,
    ):
        super().__init__(
            "walkaround",
            nodes,
            Path(__file__).parent / "walkaround_deploy.yml",
            Path(__file__).parent / "walkaround_start.yml",
            Path(__file__).parent / "walkaround_stop.yml",
            Path(__file__).parent / "walkaround_cleanup.yml",
            extravars={
                "hostnames": [n.host for n in nodes],
                "scripts": [
                    str(Path(__file__).parent / "set_spawn.js"),
                    str(Path(__file__).parent / "walkaround_bot.js"),
                    str(Path(__file__).parent / "walkaround_worker_bot.js"),
                ],
                "duration": duration.total_seconds(),
                "mc_host": server_host,
                "spawn_x": spawn_x,
                "spawn_y": spawn_y,
                "box_width": box_width,
                "box_x": box_x,
                "box_z": box_z,
                "bots_join_delay": bots_join_delay.total_seconds(),
                "bots_per_node": bots_per_node,
            },
        )
