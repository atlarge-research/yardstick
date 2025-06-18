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
    """
    RustWalkAround workload uses the texmodbot Rust implementation
    to create realistic bot behavior for Luanti servers.
    """

    def __init__(
        self,
        nodes: list[Node],
        server_host: str,
        duration: timedelta = timedelta(minutes=5),
        bots_per_node: int = 10,
        movement_mode: str = "random",  # "random", "circle", "line"
        movement_speed: float = 2.0,    # seconds between movements
        server_port: int = 30000,
        texmodbot_path: str = None,     # Path on remote nodes - will use working directory if None
    ):
        # If no custom path provided, use working directory
        if texmodbot_path is None:
            texmodbot_path = "texmodbot"  # Relative to working directory
        
        super().__init__(
            "rust_walkaround",
            nodes,
            Path(__file__).parent / "rust_walkaround_deploy.yml",
            Path(__file__).parent / "rust_walkaround_start.yml",
            Path(__file__).parent / "rust_walkaround_stop.yml", 
            Path(__file__).parent / "rust_walkaround_cleanup.yml",
            extravars={
                "server_host": server_host,
                "server_port": server_port,
                "duration_seconds": int(duration.total_seconds()),
                "bots_per_node": bots_per_node,
                "movement_mode": movement_mode,
                "movement_speed": movement_speed,
                "texmodbot_archive": str(Path(__file__).parent.parent.parent.parent.parent / "bot_components" / "texmodbot"),
                "texmodbot_path": texmodbot_path,
            },
        )

    @property
    def duration(self) -> timedelta:
        return timedelta(seconds=self.extravars["duration_seconds"])

    @property
    def bots_per_node(self) -> int:
        return self.extravars["bots_per_node"]

    @property
    def server_host(self) -> str:
        return self.extravars["server_host"]

    @property
    def movement_mode(self) -> str:
        return self.extravars["movement_mode"]