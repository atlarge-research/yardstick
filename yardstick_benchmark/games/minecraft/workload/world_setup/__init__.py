from yardstick_benchmark.model import RemoteApplication, Node
from pathlib import Path
import os
from datetime import timedelta

class WorldSetup(RemoteApplication):
    def __init__(
            self,
            nodes: list[Node],
            num_players: 10,
            global_spread: 1000,
    ):
        super().__init__(
            "world_setup",
            nodes,
            Path(__file__).parent / "world_setup_deploy.yml",
            Path(__file__).parent / "world_setup_start.yml",
            Path(__file__).parent / "world_setup_stop.yml",
            Path(__file__).parent / "world_setup_cleanup.yml",
            extravars={
                "hostnames": [n.host for n in nodes],
                "scripts": [
                    str(Path(__file__).parent / "generate_spawnpoints.js")
                ],
                "num_players": num_players,
                "global_spread": global_spread
            },
        )
    