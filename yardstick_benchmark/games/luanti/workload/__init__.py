from yardstick_benchmark.model import RemoteApplication, Node
from pathlib import Path
from datetime import timedelta

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
        spawn_radius: int = 0,
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
                "texmodbot_source": "/var/scratch/aco237/luantick/bot_components/texmodbot",
                "spawn_radius": spawn_radius
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

class RustBlockBot(RemoteApplication):
    """
    RustBlockBot workload uses the texmodbot Rust blockbot implementation
    to create block-placing bot behavior for Luanti servers.
    """

    def __init__(
        self,
        nodes: list[Node],
        server_host: str,
        duration: timedelta = timedelta(minutes=5),
        bots_per_node: int = 5,
        building_pattern: str = "tower",  # "tower", "wall", "platform", "random", "spiral", "house"
        building_speed: float = 1.0,      # seconds between block placements
        max_blocks: int = 100,            # maximum blocks per bot
        destructive_mode: bool = False,   # whether to also dig blocks
        server_port: int = 30000,
        texmodbot_path: str = None,       # Path on remote nodes
        start_x: float = 0.0,             # Starting X coordinate for building
        start_y: float = 8.0,             # Starting Y coordinate for building  
        start_z: float = 0.0,             # Starting Z coordinate for building
        spawn_radius: int = 0,
    ):
        # If no custom path provided, use working directory
        if texmodbot_path is None:
            texmodbot_path = "texmodbot"  # Relative to working directory
        
        super().__init__(
            "rust_blockbot",
            nodes,
            Path(__file__).parent / "blockbot" / "rust_blockbot_deploy.yml",
            Path(__file__).parent / "blockbot" / "rust_blockbot_start.yml",
            Path(__file__).parent / "blockbot" / "rust_blockbot_stop.yml",
            Path(__file__).parent / "blockbot" / "rust_blockbot_cleanup.yml",
            extravars={
                "server_host": server_host,
                "server_port": server_port,
                "duration_seconds": int(duration.total_seconds()),
                "bots_per_node": bots_per_node,
                "building_pattern": building_pattern,
                "building_speed": building_speed,
                "max_blocks": max_blocks,
                "destructive_mode": destructive_mode,
                "start_x": start_x,
                "start_y": start_y,
                "start_z": start_z,
                "texmodbot_archive": str(Path(__file__).parent.parent.parent.parent.parent / "bot_components" / "texmodbot"),
                "texmodbot_path": texmodbot_path,
                "texmodbot_source": "/var/scratch/aco237/luantick/bot_components/texmodbot",
                "spawn_radius": spawn_radius
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
    def building_pattern(self) -> str:
        return self.extravars["building_pattern"]