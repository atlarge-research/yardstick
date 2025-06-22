from yardstick_benchmark.model import RemoteApplication, Node
from pathlib import Path


class LuantiServer(RemoteApplication):
    def __init__(self, nodes: list[Node], game_mode="minetest_game", use_ppa=True):
        # Choose deployment method based on use_ppa flag
        deploy_yml = "luanti_ppa_deploy.yml" if use_ppa else "luanti_deploy.yml"
        
        super().__init__(
            "luanti",
            nodes,
            Path(__file__).parent / deploy_yml,
            Path(__file__).parent / "luanti_start.yml",
            Path(__file__).parent / "luanti_stop.yml",
            Path(__file__).parent / "luanti_cleanup.yml",
            extravars={
                "hostnames": [n.host for n in nodes],
                "luanti_template": str(Path(__file__).parent / "luanti.conf.j2"),
                "collector_mod": str(Path(__file__).parent.parent / "collector" / "init.lua"),
                "game_mode": game_mode
            },
        ) 