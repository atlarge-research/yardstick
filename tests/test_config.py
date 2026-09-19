"""Configuration parsing, validation and error messages.

A configuration file is the interface most people will use, so a bad one
should fail immediately with a message that says what to write instead --
not minutes later, after the container images have been pulled.
"""

from datetime import timedelta

import pytest

from yardstick_benchmark.config import (
    EXAMPLE_CONFIG,
    BenchmarkConfig,
    ConfigError,
    build_kwargs,
    parse_duration,
    resolve,
)
from yardstick_benchmark.games.minecraft.workload import WalkAround, WorldGeneration


def _write(tmp_path, text, name="experiment.toml"):
    path = tmp_path / name
    path.write_text(text)
    return path


def test_the_shipped_example_config_is_valid(tmp_path):
    """`yardstick init` writes this; it must actually work."""
    config = BenchmarkConfig.from_toml(_write(tmp_path, EXAMPLE_CONFIG))
    config.validate()
    assert config.game == "minecraft"
    assert config.workload == "worldgen"


def test_defaults_apply_to_an_empty_config(tmp_path):
    config = BenchmarkConfig.from_toml(_write(tmp_path, ""))
    config.validate()
    assert config.deployment.hosts == ["localhost"]
    assert config.output.dir == "results"


def test_game_and_workload_options_reach_the_constructor(tmp_path):
    config = BenchmarkConfig.from_toml(
        _write(
            tmp_path,
            """
[game]
type = "minecraft"
max_players = 250
seed = "abc"

[workload]
type = "walkaround"
bots_per_node = 7
""",
        )
    )
    config.validate()
    game_kwargs = build_kwargs(config.game_class, config.game_options)
    assert game_kwargs["max_players"] == 250
    assert game_kwargs["seed"] == "abc"
    assert (
        build_kwargs(config.workload_class, config.workload_options)["bots_per_node"]
        == 7
    )


@pytest.mark.parametrize(
    "text,expected",
    [
        ('[workload]\nduration = "5m"', timedelta(minutes=5)),
        ("[workload]\nduration = 90", timedelta(seconds=90)),
        ('[workload]\nduration = "250ms"', timedelta(milliseconds=250)),
        ('[workload]\nduration = "2h"', timedelta(hours=2)),
    ],
)
def test_durations_are_parsed_from_the_config(tmp_path, text, expected):
    config = BenchmarkConfig.from_toml(_write(tmp_path, text + '\ntype = "walkaround"'))
    kwargs = build_kwargs(config.workload_class, config.workload_options)
    assert kwargs["duration"] == expected


def test_a_bad_duration_says_what_to_write(tmp_path):
    config = BenchmarkConfig.from_toml(
        _write(tmp_path, '[workload]\ntype = "walkaround"\nduration = "soon"')
    )
    with pytest.raises(ConfigError, match="cannot read 'soon' as a duration"):
        config.validate()


def test_an_unknown_option_lists_the_valid_ones(tmp_path):
    config = BenchmarkConfig.from_toml(
        _write(tmp_path, '[game]\ntype = "minecraft"\nmax_playerz = 10')
    )
    with pytest.raises(ConfigError) as exc:
        config.validate()
    message = str(exc.value)
    assert "max_playerz" in message
    assert "max_players" in message, "the error should suggest the real option"


def test_an_unknown_workload_lists_the_known_ones(tmp_path):
    with pytest.raises(ConfigError, match="walkaround, worldgen"):
        BenchmarkConfig.from_toml(_write(tmp_path, '[workload]\ntype = "wanderabout"'))


def test_an_unknown_section_is_rejected(tmp_path):
    with pytest.raises(ConfigError, match="unknown section"):
        BenchmarkConfig.from_toml(_write(tmp_path, "[gaem]\ntype = 'minecraft'"))


def test_an_unknown_deployment_option_is_rejected(tmp_path):
    with pytest.raises(ConfigError, match="hosts"):
        BenchmarkConfig.from_toml(_write(tmp_path, "[deployment]\nhost = 'localhost'"))


def test_invalid_toml_is_reported_with_the_file_name(tmp_path):
    with pytest.raises(ConfigError, match="invalid TOML"):
        BenchmarkConfig.from_toml(_write(tmp_path, "[game\n"))


def test_a_missing_file_is_reported(tmp_path):
    with pytest.raises(ConfigError, match="no such configuration file"):
        BenchmarkConfig.from_toml(tmp_path / "nope.toml")


def test_server_host_must_be_one_of_the_hosts(tmp_path):
    config = BenchmarkConfig.from_toml(
        _write(
            tmp_path,
            "[deployment]\nhosts = ['a', 'b']\nserver_host = 'c'",
        )
    )
    with pytest.raises(ConfigError, match="not in hosts"):
        config.validate()


def test_workload_hosts_exclude_the_server_when_there_is_a_choice(tmp_path):
    config = BenchmarkConfig.from_toml(
        _write(tmp_path, "[deployment]\nhosts = ['srv', 'c1', 'c2']")
    )
    assert config.deployment.resolved_server_host() == "srv"
    assert config.deployment.workload_hosts() == ["c1", "c2"]


def test_a_single_host_runs_both_the_server_and_the_players(tmp_path):
    config = BenchmarkConfig.from_toml(
        _write(tmp_path, "[deployment]\nhosts = ['localhost']")
    )
    assert config.deployment.workload_hosts() == ["localhost"]


def test_a_custom_class_can_be_named_by_import_path(tmp_path):
    config = BenchmarkConfig.from_toml(
        _write(
            tmp_path,
            "[workload]\n"
            "type = 'yardstick_benchmark.games.minecraft.workload.WalkAround'\n"
            "bots_per_node = 2\n",
        )
    )
    config.validate()
    assert config.workload_class is WalkAround


def test_a_bad_import_path_is_reported_clearly():
    with pytest.raises(ConfigError, match="cannot import module"):
        resolve("nosuchpkg.Thing", {}, "workload")
    with pytest.raises(ConfigError, match="has no"):
        resolve("yardstick_benchmark.config.NoSuchThing", {}, "workload")


def test_context_only_fills_parameters_the_class_accepts(tmp_path):
    """WalkAround takes no RCON password; supplying one must not be an error,
    and must not be passed on."""
    context = {
        "server_host": "srv",
        "rcon_password": "secret",
        "influxdb_info": object(),
        "bot_index": 3,
    }
    walk = build_kwargs(WalkAround, {}, context=context)
    assert walk["server_host"] == "srv"
    assert "rcon_password" not in walk
    assert "influxdb_info" not in walk

    gen = build_kwargs(WorldGeneration, {}, context=context)
    assert gen["rcon_password"] == "secret"


def test_explicit_config_wins_over_context():
    kwargs = build_kwargs(
        WalkAround, {"bot_index": 9}, context={"bot_index": 0, "server_host": "srv"}
    )
    assert kwargs["bot_index"] == 9


def test_parse_duration_rejects_nonsense():
    with pytest.raises(ConfigError):
        parse_duration("later")
    with pytest.raises(ConfigError):
        parse_duration(None)
