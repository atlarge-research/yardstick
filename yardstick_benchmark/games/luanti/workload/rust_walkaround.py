from yardstick_benchmark.model import RemoteApplication, Node
from pathlib import Path
from datetime import timedelta

class RustWalkAround(RemoteApplication):
    def __init__(
        self,
        nodes: list[Node],
        server_host: str,
        duration: timedelta = timedelta(seconds=60),
        bots_per_node: int = 1,
        movement_mode: str = "random",
        movement_speed: float = 2.0,
    ):
        # Use working directory from nodes instead of hardcoded path
        texmodbot_path = str(nodes[0].wd / "texmodbot")
        
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
                "duration_seconds": int(duration.total_seconds()),
                "bots_per_node": bots_per_node,
                "movement_mode": movement_mode,
                "movement_speed": movement_speed,
                "texmodbot_path": texmodbot_path,
                "texmodbot_source": str(Path(__file__).parent.parent.parent.parent.parent / "bot_components" / "texmodbot"),
            },
        )
