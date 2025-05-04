from yardstick_benchmark.model import RemoteApplication, Node
import os
from pathlib import Path


class LuantiServer(RemoteApplication):
    """
    Luanti engine server implementation for Yardstick benchmarking.
    Supports different game modes including Minetest (default) and Extra Ordinance.
    """
    def __init__(self, nodes: list[Node], game_mode="minetest", custom_game_url=None):
        """
        Initialize a Luanti server with specified game mode
        
        Args:
            nodes: List of nodes to deploy the server on
            game_mode: Game mode to use ('minetest', 'extra_ordinance', or 'custom')
            custom_game_url: URL to a custom game (only used if game_mode='custom')
        """
        extravars = {
            "hostnames": [n.host for n in nodes],
            "luanti_template": str(Path(__file__).parent / "minetest.conf.j2"),
            "game_mode": game_mode
        }
        
        # Add custom game URL if specified
        if game_mode == "custom" and custom_game_url:
            extravars["custom_game_url"] = custom_game_url
        
        # Add Extra Ordinance specific configuration
        if game_mode == "extra_ordinance":
            extravars["extra_ordinance_repo"] = "https://codeberg.org/SumianVoice/ExtraOrdinance.git"
        
        super().__init__(
            "luanti",
            nodes,
            Path(__file__).parent / "luanti_deploy.yml",
            Path(__file__).parent / "luanti_start.yml",
            Path(__file__).parent / "luanti_stop.yml",
            Path(__file__).parent / "luanti_cleanup.yml",
            extravars=extravars,
        ) 