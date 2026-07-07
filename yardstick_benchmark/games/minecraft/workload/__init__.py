from yardstick_benchmark.model import RemoteApplication, Node
from pathlib import Path
import os
from datetime import timedelta


class Workload(RemoteApplication):
    def __init__(
        self,
        nodes: list[Node],
        server_host: str,
        worker_bot_file: str = 'walkaround_worker_bot.js',
        duration: timedelta = timedelta(seconds=60),
        spawn_x: int = 0,
        spawn_y: int = 0,
        box_width: int = 32,
        box_x: int = -16,
        box_z: int = -16,
        bots_join_delay: timedelta = timedelta(seconds=1),
        bots_per_node: int = 1,
    ):
        name = worker_bot_file.replace('_worker_bot.js', '').replace('_bot.js', '')
        super().__init__(
            name,
            nodes,
            Path(__file__).parent / "workload_deploy.yml",
            Path(__file__).parent / "workload_start.yml",
            Path(__file__).parent / "workload_stop.yml",
            Path(__file__).parent / "workload_cleanup.yml",
            extravars={
                "hostnames": [n.host for n in nodes],
                "scripts": [
                    str(Path(__file__).parent / "set_spawn.js"),
                    str(Path(__file__).parent / "workload_bot.js"),
                    str(Path(__file__).parent / worker_bot_file),
                ],
                "worker_bot": worker_bot_file,
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


def WalkAround(nodes, server_host, **kwargs):
    kwargs.setdefault('worker_bot_file', 'walkaround_worker_bot.js')
    return Workload(nodes, server_host, **kwargs)
