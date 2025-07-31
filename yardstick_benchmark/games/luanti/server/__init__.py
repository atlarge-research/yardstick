from yardstick_benchmark.model import RemoteApplication, Node
from pathlib import Path

class LuantiServer(RemoteApplication):
    def __init__(
        self,
        nodes: list[Node],
        game_mode: str = "minetest_game",     # ADD: Support different games
        use_source_build: bool = False,
        enable_luajit: bool = False,
        ipv4_only: bool = True,
    ):
        super().__init__(
            "luanti_server",
            nodes,
            Path(__file__).parent / "luanti_deploy.yml",
            Path(__file__).parent / "luanti_start.yml",
            Path(__file__).parent / "luanti_stop.yml",
            Path(__file__).parent / "luanti_cleanup.yml",
            extravars={
                "game_mode": game_mode,           # ADD: Pass game mode to playbooks
                "use_source_build": use_source_build,
                "enable_luajit": enable_luajit,
                "ipv4_only": ipv4_only,
            },
        )

    @property
    def game_mode(self) -> str:
        return self.extravars["game_mode"]