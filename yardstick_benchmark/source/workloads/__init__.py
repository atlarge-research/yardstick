from yardstick_benchmark.model import RemoteApplication, Node
from pathlib import Path
import os
from datetime import timedelta


class WalkAround(RemoteApplication):
    def __init__(
        # These spawn coordinates are specific to seed 542282774301782913
        self,
        nodes: list[Node],
        server_host: str,
        duration: timedelta = timedelta(seconds=60),
        spawn_x: int = -30,
        spawn_y: int = 115,
        spawn_z: int = 20,
        box_width: int = 32,
        box_x: int = -16,
        box_z: int = -16,
        bots_join_delay: timedelta = timedelta(seconds=5),
        bots_per_node: int = 1,
    ):
        super().__init__(
            "walkaround",
            nodes,
            Path(__file__).parent / "walkaround/walkaround_deploy.yml",
            Path(__file__).parent / "walkaround/walkaround_start.yml",
            Path(__file__).parent / "walkaround/walkaround_stop.yml",
            Path(__file__).parent / "walkaround/walkaround_cleanup.yml",
            extravars={
                "hostnames": [n.host for n in nodes],
                "scripts": [
                    str(Path(__file__).parent / "set_spawn.js"),
                    str(Path(__file__).parent / "walkaround/walkaround_bot.js"),
                    str(Path(__file__).parent / "walkaround/walkaround_worker_bot.js"),
                ],
                "duration": duration.total_seconds(),
                "mc_host": server_host,
                "spawn_x": spawn_x,
                "spawn_y": spawn_y,
                "spawn_z": spawn_z,
                "box_width": box_width,
                "box_x": box_x,
                "box_z": box_z,
                "bots_join_delay": bots_join_delay.total_seconds(),
                "bots_per_node": bots_per_node,
            },
        )

class ChopWood(RemoteApplication):
    def __init__(
        # These spawn coordinates are specific to seed 542282774301782913
        self,
        nodes: list[Node],
        server_host: str,
        duration: timedelta = timedelta(seconds=60),
        spawn_x: int = -30,
        spawn_y: int = 115,
        spawn_z: int = 20,
        box_width: int = 32,
        box_x: int = -16,
        box_z: int = -16,
        bots_join_delay: timedelta = timedelta(seconds=5),
        bots_per_node: int = 1,
    ):
        super().__init__(
            "chopwood",
            nodes,
            Path(__file__).parent / "chopwood/chopwood_deploy.yml",
            Path(__file__).parent / "chopwood/chopwood_start.yml",
            Path(__file__).parent / "chopwood/chopwood_stop.yml",
            Path(__file__).parent / "chopwood/chopwood_cleanup.yml",
            extravars={
                "hostnames": [n.host for n in nodes],
                "scripts": [
                    str(Path(__file__).parent / "set_spawn.js"),
                    str(Path(__file__).parent / "chopwood/chopwood_bot.js"),
                    str(Path(__file__).parent / "chopwood/chopwood_worker_bot.js"),
                ],
                "duration": duration.total_seconds(),
                "mc_host": server_host,
                "spawn_x": spawn_x,
                "spawn_y": spawn_y,
                "spawn_z": spawn_z,
                "box_width": box_width,
                "box_x": box_x,
                "box_z": box_z,
                "bots_join_delay": bots_join_delay.total_seconds(),
                "bots_per_node": bots_per_node,
            },
        )

class MineOre(RemoteApplication):
    def __init__(
        # These spawn coordinates are specific to seed 542282774301782913
        self,
        nodes: list[Node],
        server_host: str,
        duration: timedelta = timedelta(seconds=60),
        spawn_x: int = -30,
        spawn_y: int = 115,
        spawn_z: int = 20,
        box_width: int = 32,
        box_x: int = -16,
        box_z: int = -16,
        bots_join_delay: timedelta = timedelta(seconds=5),
        bots_per_node: int = 1,
    ):
        super().__init__(
            "mineore",
            nodes,
            Path(__file__).parent / "mineore/mineore_deploy.yml",
            Path(__file__).parent / "mineore/mineore_start.yml",
            Path(__file__).parent / "mineore/mineore_stop.yml",
            Path(__file__).parent / "mineore/mineore_cleanup.yml",
            extravars={
                "hostnames": [n.host for n in nodes],
                "scripts": [
                    str(Path(__file__).parent / "set_spawn.js"),
                    str(Path(__file__).parent / "mineore/mineore_bot.js"),
                    str(Path(__file__).parent / "mineore/mineore_worker_bot.js"),
                ],
                "duration": duration.total_seconds(),
                "mc_host": server_host,
                "spawn_x": spawn_x,
                "spawn_y": spawn_y,
                "spawn_z": spawn_z,
                "box_width": box_width,
                "box_x": box_x,
                "box_z": box_z,
                "bots_join_delay": bots_join_delay.total_seconds(),
                "bots_per_node": bots_per_node,
            },
        )

class Fight(RemoteApplication):
    def __init__(
        # These spawn coordinates are specific to seed 542282774301782913
        self,
        nodes: list[Node],
        server_host: str,
        duration: timedelta = timedelta(seconds=60),
        spawn_x: int = -30,
        spawn_y: int = 115,
        spawn_z: int = 20,
        box_width: int = 32,
        box_x: int = -16,
        box_z: int = -16,
        bots_join_delay: timedelta = timedelta(seconds=5),
        bots_per_node: int = 1,
    ):
        super().__init__(
            "mineore",
            nodes,
            Path(__file__).parent / "fight/fight_deploy.yml",
            Path(__file__).parent / "fight/fight_start.yml",
            Path(__file__).parent / "fight/fight_stop.yml",
            Path(__file__).parent / "fight/fight_cleanup.yml",
            extravars={
                "hostnames": [n.host for n in nodes],
                "scripts": [
                    str(Path(__file__).parent / "set_spawn.js"),
                    str(Path(__file__).parent / "fight/fight_bot.js"),
                    str(Path(__file__).parent / "fight/fight_worker_bot.js"),
                ],
                "duration": duration.total_seconds(),
                "mc_host": server_host,
                "spawn_x": spawn_x,
                "spawn_y": spawn_y,
                "spawn_z": spawn_z,
                "box_width": box_width,
                "box_x": box_x,
                "box_z": box_z,
                "bots_join_delay": bots_join_delay.total_seconds(),
                "bots_per_node": bots_per_node,
            },
        )


class Explore(RemoteApplication):
    def __init__(
        # These spawn coordinates are specific to seed 542282774301782913
        self,
        nodes: list[Node],
        server_host: str,
        duration: timedelta = timedelta(seconds=60),
        spawn_x: int = -30,
        spawn_y: int = 115,
        spawn_z: int = 20,
        box_width: int = 32,
        box_x: int = -16,
        box_z: int = -16,
        bots_join_delay: timedelta = timedelta(seconds=5),
        bots_per_node: int = 1,
    ):
        super().__init__(
            "mineore",
            nodes,
            Path(__file__).parent / "explore/explore_deploy.yml",
            Path(__file__).parent / "explore/explore_start.yml",
            Path(__file__).parent / "explore/explore_stop.yml",
            Path(__file__).parent / "explore/explore_cleanup.yml",
            extravars={
                "hostnames": [n.host for n in nodes],
                "scripts": [
                    str(Path(__file__).parent / "set_spawn.js"),
                    str(Path(__file__).parent / "explore/explore_bot.js"),
                    str(Path(__file__).parent / "explore/explore_worker_bot.js"),
                ],
                "duration": duration.total_seconds(),
                "mc_host": server_host,
                "spawn_x": spawn_x,
                "spawn_y": spawn_y,
                "spawn_z": spawn_z,
                "box_width": box_width,
                "box_x": box_x,
                "box_z": box_z,
                "bots_join_delay": bots_join_delay.total_seconds(),
                "bots_per_node": bots_per_node,
            },
        )
