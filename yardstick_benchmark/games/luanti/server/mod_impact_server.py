from yardstick_benchmark.model import RemoteApplication, Node
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ModConfiguration:
    """Configuration for different mod combinations to test"""
    name: str
    description: str
    game_mode: str = "minetest_game"
    extra_ordinance_enabled: bool = False
    weather_enabled: bool = False
    performance_test_enabled: bool = False
    yardstick_collector_enabled: bool = True  # Always enabled for monitoring


class LuantiModImpactServer(RemoteApplication):
    """Luanti server with configurable mod setup for impact testing"""
    
    def __init__(self, nodes: list[Node], mod_config: ModConfiguration):
        self.mod_config = mod_config
        
        # Convert mod config to ansible variables
        extravars = {
            "hostnames": [n.host for n in nodes],
            "luanti_template": str(Path(__file__).parent / "luanti.conf.j2"),
            "collector_mod": str(Path(__file__).parent.parent / "collector" / "init.lua"),
            "mod_config": {
                "name": mod_config.name,
                "description": mod_config.description,
                "game_mode": mod_config.game_mode,
                "extra_ordinance_enabled": mod_config.extra_ordinance_enabled,
                "weather_enabled": mod_config.weather_enabled,
                "performance_test_enabled": mod_config.performance_test_enabled,
                "yardstick_collector_enabled": mod_config.yardstick_collector_enabled,
            }
        }
        
        super().__init__(
            f"luanti-{mod_config.name}",
            nodes,
            Path(__file__).parent / "luanti_mod_impact_deploy.yml",
            Path(__file__).parent / "luanti_start.yml",
            Path(__file__).parent / "luanti_stop.yml",
            Path(__file__).parent / "luanti_cleanup.yml",
            extravars=extravars,
        )


# Predefined mod configurations for testing
MOD_CONFIGURATIONS = {
    "vanilla": ModConfiguration(
        name="vanilla",
        description="Vanilla Luanti with only yardstick_collector",
        game_mode="minetest_game",
        extra_ordinance_enabled=False,
        weather_enabled=False,
        performance_test_enabled=False,
    ),
    
    "extra_ordinance_only": ModConfiguration(
        name="extra_ordinance_only",
        description="Extra Ordinance mod only",
        game_mode="extra_ordinance",  # Extra Ordinance is a complete game
        extra_ordinance_enabled=True,
        weather_enabled=False,
        performance_test_enabled=False,
    ),
    
    "weather_only": ModConfiguration(
        name="weather_only",
        description="Simple weather mod only",
        game_mode="minetest_game",
        extra_ordinance_enabled=False,
        weather_enabled=True,
        performance_test_enabled=False,
    ),
    
    "performance_test_only": ModConfiguration(
        name="performance_test_only",
        description="CPU/memory heavy test mod only",
        game_mode="minetest_game",
        extra_ordinance_enabled=False,
        weather_enabled=False,
        performance_test_enabled=True,
    ),
    
    "weather_and_performance": ModConfiguration(
        name="weather_and_performance",
        description="Weather + performance test mods",
        game_mode="minetest_game",
        extra_ordinance_enabled=False,
        weather_enabled=True,
        performance_test_enabled=True,
    ),
    
    "all_mods": ModConfiguration(
        name="all_mods",
        description="All test mods enabled (except Extra Ordinance which conflicts)",
        game_mode="minetest_game",
        extra_ordinance_enabled=False,  # Cannot combine with other mods easily
        weather_enabled=True,
        performance_test_enabled=True,
    ),
}


def get_mod_configuration(config_name: str) -> ModConfiguration:
    """Get a predefined mod configuration by name"""
    if config_name not in MOD_CONFIGURATIONS:
        available = list(MOD_CONFIGURATIONS.keys())
        raise ValueError(f"Unknown mod configuration '{config_name}'. Available: {available}")
    
    return MOD_CONFIGURATIONS[config_name]


def list_mod_configurations() -> Dict[str, str]:
    """List all available mod configurations with descriptions"""
    return {name: config.description for name, config in MOD_CONFIGURATIONS.items()} 