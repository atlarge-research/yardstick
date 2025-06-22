from yardstick_benchmark.model import RemoteApplication, Node
from pathlib import Path
from datetime import timedelta

class EnhancedRustBots(RemoteApplication):
    """Enhanced Rust bot workload supporting both walkbots and blockbots"""
    
    def __init__(
        self,
        nodes: list[Node],
        server_host: str,
        duration: timedelta = timedelta(seconds=60),
        bots_per_node: int = 1,
        bot_type: str = "walkbot",  # "walkbot" or "blockbot"
        movement_mode: str = "random",  # For walkbots
        building_pattern: str = "tower",  # For blockbots
        movement_speed: float = 2.0,
        spawn_area: tuple = None,  # (x, y, z) for spawn area positioning
        max_blocks_per_bot: int = 200,  # For blockbots
    ):
        # Use working directory from nodes instead of hardcoded path
        texmodbot_path = str(nodes[0].wd / "texmodbot")
        
        # Calculate spawn area coordinates if provided
        extravars = {
            "hostnames": [n.host for n in nodes],
            "server_host": server_host,
            "server_port": 30000,  # Default Luanti port
            "duration": duration.total_seconds(),
            "duration_seconds": int(duration.total_seconds()),
            "bots_per_node": bots_per_node,
            "bot_type": bot_type,
            "movement_mode": movement_mode,
            "building_pattern": building_pattern,
            "movement_speed": movement_speed,
            "max_blocks_per_bot": max_blocks_per_bot,
            "texmodbot_path": texmodbot_path,
            "texmodbot_source": str(Path(__file__).parent.parent.parent.parent.parent / "bot_components" / "texmodbot"),
        }
        
        # Add spawn area positioning if provided
        if spawn_area:
            spawn_x, spawn_y, spawn_z = spawn_area
            extravars.update({
                "use_spawn_area": True,
                "spawn_x": spawn_x,
                "spawn_y": spawn_y,
                "spawn_z": spawn_z,
            })
        else:
            extravars["use_spawn_area"] = False
        
        super().__init__(
            f"enhanced_rust_{bot_type}s",
            nodes,
            Path(__file__).parent / "enhanced_rust_deploy.yml",
            Path(__file__).parent / "enhanced_rust_start.yml",
            Path(__file__).parent / "enhanced_rust_stop.yml",
            Path(__file__).parent / "enhanced_rust_cleanup.yml",
            extravars=extravars,
        ) 