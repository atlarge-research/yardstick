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
            "[deployment]\nhosts = ['127.0.0.1', '127.0.0.2']\n"
            "server_host = '127.0.0.9'",
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


def test_local_is_the_default_mode(tmp_path):
    config = BenchmarkConfig.from_toml(_write(tmp_path, ""))
    assert config.deployment.mode == "local"
    config.validate()


@pytest.mark.parametrize("mode,provider", [("cloud", "ubicloud"), ("cluster", "das")])
def test_remote_modes_validate_now_that_staging_works(tmp_path, mode, provider):
    config = BenchmarkConfig.from_toml(
        _write(
            tmp_path,
            f"[deployment]\nmode = '{mode}'\n\n"
            f"[provisioning]\nprovider = '{provider}'\nworkload_nodes = 2\n",
        )
    )
    config.validate()
    assert config.provisioning.workload_nodes == 2


def test_remote_modes_do_not_require_hosts_to_be_local(tmp_path):
    """In cloud/cluster mode the machines are provisioned, so the local-only
    host check must not apply."""
    config = BenchmarkConfig.from_toml(
        _write(
            tmp_path,
            "[deployment]\nmode = 'cloud'\nhosts = ['some-remote-host']\n"
            "server_host = 'some-remote-host'\n",
        )
    )
    config.validate()


def test_provider_options_are_checked_against_the_provider(tmp_path):
    config = BenchmarkConfig.from_toml(
        _write(
            tmp_path,
            "[deployment]\nmode = 'cloud'\n\n"
            "[provisioning]\nprovider = 'ubicloud'\nlocationn = 'eu-central-h1'\n",
        )
    )
    with pytest.raises(ConfigError, match="locationn"):
        config.validate()


def test_per_group_options_override_the_shared_ones(tmp_path):
    config = BenchmarkConfig.from_toml(
        _write(
            tmp_path,
            "[deployment]\nmode = 'cloud'\n\n"
            "[provisioning]\nprovider = 'ubicloud'\nsize = 'standard-2'\n"
            "location = 'eu-central-h1'\n\n"
            "[provisioning.server]\nsize = 'standard-4'\n",
        )
    )
    config.validate()
    assert config.provisioning.options_for("server")["size"] == "standard-4"
    assert config.provisioning.options_for("workload")["size"] == "standard-2"
    # Shared options reach both groups.
    assert config.provisioning.options_for("server")["location"] == "eu-central-h1"


def test_an_unknown_provider_lists_the_known_ones(tmp_path):
    with pytest.raises(ConfigError, match="das, ubicloud"):
        BenchmarkConfig.from_toml(
            _write(tmp_path, "[provisioning]\nprovider = 'aws'\n")
        )


def test_an_oversized_machine_is_refused_at_validate_time(tmp_path):
    """The size guard lives in the provisioner; validate() must surface it
    before anything is created."""
    config = BenchmarkConfig.from_toml(
        _write(
            tmp_path,
            "[deployment]\nmode = 'cloud'\n\n"
            "[provisioning]\nprovider = 'ubicloud'\n\n"
            "[provisioning.server]\nsize = 'standard-60'\n",
        )
    )
    with pytest.raises(ConfigError, match="standard-60"):
        config.validate()


def test_an_unknown_mode_lists_the_valid_ones(tmp_path):
    config = BenchmarkConfig.from_toml(_write(tmp_path, "[deployment]\nmode = 'k8s'"))
    with pytest.raises(ConfigError, match="local, cloud, cluster"):
        config.validate()


def test_local_mode_rejects_hosts_it_cannot_reach(tmp_path):
    config = BenchmarkConfig.from_toml(
        _write(tmp_path, "[deployment]\nhosts = ['localhost', 'node042']")
    )
    with pytest.raises(ConfigError, match="node042"):
        config.validate()


def test_local_mode_accepts_loopback_aliases(tmp_path):
    """Distinct loopback addresses are a legitimate way to exercise a
    multi-node layout on one machine."""
    config = BenchmarkConfig.from_toml(
        _write(tmp_path, "[deployment]\nhosts = ['127.0.0.1', '127.0.0.2']")
    )
    config.validate()
