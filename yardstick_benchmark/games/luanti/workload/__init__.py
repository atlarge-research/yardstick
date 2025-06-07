from yardstick_benchmark.model import RemoteApplication, Node
from pathlib import Path
from datetime import timedelta

class WalkAround(RemoteApplication):
    def __init__(
        self,
        nodes: list[Node],
        server_host: str,
        duration: timedelta = timedelta(seconds=60),
        spawn_x: int = 0,
        spawn_y: int = 80,
        spawn_z: int = 0,
        box_width: int = 32,
        box_x: int = -16,
        box_z: int = -16,
        bots_join_delay: timedelta = timedelta(seconds=5),
        bots_per_node: int = 1,
    ):
        super().__init__(
            "luanti_walkaround",
            nodes,
            Path(__file__).parent / "walkaround_deploy.yml",
            Path(__file__).parent / "walkaround_start.yml",
            Path(__file__).parent / "walkaround_stop.yml",
            Path(__file__).parent / "walkaround_cleanup.yml",
            extravars={
                "hostnames": [n.host for n in nodes],
                "scripts": [
                    str(Path(__file__).parent / "walkaround.py"),
                ],
                "duration": duration.total_seconds(),
                "luanti_host": server_host,
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

class RustWalkAround(RemoteApplication):
    def __init__(
        self,
        nodes: list[Node],
        server_host: str,
        duration: timedelta = timedelta(seconds=60),
        bots_per_node: int = 1,
        movement_mode: str = "random",
        movement_speed: float = 2.0,
        texmodbot_path: str = "/home/ubuntu/texmodbot",  # Path on remote nodes
    ):
        super().__init__(
            "rust_walkaround",
            nodes,
            Path(__file__).parent / "rust_walkaround_deploy.yml",
            Path(__file__).parent / "rust_walkaround_start.yml",
            Path(__file__).parent / "rust_walkaround_stop.yml",
            Path(__file__).parent / "rust_walkaround_cleanup.yml",
            extravars={
                "hostnames": [n.host for n in nodes],
                "server_host": server_host,
                "server_port": 30000,  # Default Luanti port
                "duration": duration.total_seconds(),
                "bots_per_node": bots_per_node,
                "movement_mode": movement_mode,
                "movement_speed": movement_speed,
                "texmodbot_path": texmodbot_path,
                "texmodbot_source": str(Path(__file__).parent.parent.parent.parent.parent / "bot_components" / "texmodbot"),
            },
        )