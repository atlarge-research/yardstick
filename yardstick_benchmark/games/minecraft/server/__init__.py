from yardstick_benchmark.model import RemoteApplication, Node
import os
from pathlib import Path


class PaperMC(RemoteApplication):
    def __init__(self, nodes: list[Node], world_dir_path: str, copy_player_data=False, use_strace=False):
        super().__init__(
            "papermc",
            nodes,
            Path(__file__).parent / "papermc_deploy.yml",
            Path(__file__).parent / "papermc_start.yml",
            Path(__file__).parent / "papermc_stop.yml",
            Path(__file__).parent / "papermc_cleanup.yml",
            extravars={
                "hostnames": [n.host for n in nodes],
                "papermc_template": str(Path(__file__).parent / "server.properties.j2"),
                "use_strace": use_strace,
                "world_dir_path": world_dir_path,
                "copy_player_data": copy_player_data
            },
        )
