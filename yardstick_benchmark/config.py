"""Running a benchmark from a configuration file.

The Python API (see :mod:`yardstick_benchmark.deployment`) is there for
building whatever deployment an experiment needs. This module is the other
end of the scale: the common case -- one game, one workload, metrics
collected and written out -- expressed as a TOML file and run with

    yardstick run experiment.toml

A minimal configuration::

    [deployment]
    hosts = ["localhost"]
    wd = "/tmp/yardstick"

    [game]
    type = "minecraft"
    seed = "yardstick"
    max_players = 100

    [workload]
    type = "worldgen"
    bots_per_node = 8
    teleports = 32

    [output]
    dir = "results"

Keys under ``[game]`` and ``[workload]`` other than ``type`` are passed
straight to the corresponding class's constructor, so the configuration file
exposes the whole API without this module having to mirror it. An unknown key
is an error that names the ones that would have worked.

``type`` accepts a short name from the registries below, or a dotted import
path (``mypackage.workloads.MyWorkload``) for a class of your own.
"""

import importlib
import inspect
import re
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Union, get_args, get_origin

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on 3.9/3.10
    import tomli as tomllib  # type: ignore[no-redef]

from yardstick_benchmark.games.minecraft.server import MinecraftServer
from yardstick_benchmark.games.minecraft.workload import WalkAround, WorldGeneration
from yardstick_benchmark.util import is_localhost


#: Short names usable as ``[game] type``.
GAMES: Dict[str, type] = {
    "minecraft": MinecraftServer,
}

#: Short names usable as ``[workload] type``.
WORKLOADS: Dict[str, type] = {
    "walkaround": WalkAround,
    "worldgen": WorldGeneration,
}


class ConfigError(ValueError):
    """Raised when a configuration file can't be turned into a benchmark."""


_DURATION_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(ms|s|m|h)?\s*$")
_DURATION_UNITS = {
    "ms": 0.001,
    "s": 1.0,
    "m": 60.0,
    "h": 3600.0,
}


def parse_duration(value: Union[str, int, float], key: str = "duration") -> timedelta:
    """Parse a duration written as "90s", "5m", "1h", "250ms", or a number.

    A bare number is seconds, which is what TOML gives for ``duration = 90``.
    """
    if isinstance(value, timedelta):
        return value
    if isinstance(value, (int, float)):
        return timedelta(seconds=float(value))
    if isinstance(value, str):
        match = _DURATION_RE.match(value)
        if match:
            amount, unit = match.groups()
            return timedelta(seconds=float(amount) * _DURATION_UNITS[unit or "s"])
    raise ConfigError(
        f"{key}: cannot read {value!r} as a duration; write a number of "
        f"seconds, or a string like '90s', '5m', '1h'"
    )


def _is_duration(annotation: Any) -> bool:
    """True for `timedelta` and `Optional[timedelta]` annotations."""
    if annotation is timedelta:
        return True
    if get_origin(annotation) is Union:
        return any(arg is timedelta for arg in get_args(annotation))
    return False


def resolve(name: str, registry: Mapping[str, type], kind: str) -> type:
    """Look `name` up in `registry`, or import it as a dotted path."""
    if name in registry:
        return registry[name]
    if "." in name:
        module_name, _, attr = name.rpartition(".")
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            raise ConfigError(
                f"{kind} {name!r}: cannot import module {module_name!r} ({exc})"
            ) from exc
        try:
            return getattr(module, attr)
        except AttributeError as exc:
            raise ConfigError(
                f"{kind} {name!r}: module {module_name!r} has no {attr!r}"
            ) from exc
    known = ", ".join(sorted(registry))
    raise ConfigError(
        f"unknown {kind} {name!r}. Known {kind}s: {known}. To use your own "
        f"class, give its full import path, e.g. 'mypackage.MyClass'."
    )


def build_kwargs(
    cls: type,
    options: Mapping[str, Any],
    context: Optional[Mapping[str, Any]] = None,
    where: str = "",
) -> Dict[str, Any]:
    """Turn configuration options into constructor keyword arguments.

    Values are coerced to match the constructor's annotations (currently that
    means durations), unknown keys are rejected with a list of the accepted
    ones, and anything in `context` that the constructor accepts -- and the
    configuration didn't already set -- is filled in. The context is how a
    workload gets things it can't know from its own section, like the server's
    host and RCON password, without this module special-casing each class.
    """
    try:
        params = inspect.signature(cls).parameters
    except (TypeError, ValueError) as exc:  # pragma: no cover - exotic classes
        raise ConfigError(f"{where}: cannot inspect {cls.__name__} ({exc})") from exc

    accepts_kwargs = any(
        p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()
    )
    unknown = [k for k in options if k not in params]
    if unknown and not accepts_kwargs:
        # Only parameters with defaults are settable from a config file:
        # the required ones (node, server_host, rcon_password, ...) are
        # supplied by the runner, so suggesting them would mislead.
        settable = sorted(
            name
            for name, p in params.items()
            if name != "self"
            and p.default is not inspect.Parameter.empty
            and p.kind
            not in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL)
        )
        raise ConfigError(
            f"{where}: {cls.__name__} has no option "
            f"{', '.join(repr(k) for k in sorted(unknown))}. "
            f"Available options: {', '.join(settable)}"
        )

    kwargs: Dict[str, Any] = {}
    for key, value in options.items():
        param = params.get(key)
        if param is not None and _is_duration(param.annotation):
            value = parse_duration(value, key=f"{where}.{key}" if where else key)
        kwargs[key] = value

    for key, value in (context or {}).items():
        if key in kwargs:
            continue
        # A class that declares **kwargs has opted into receiving keywords it
        # didn't name, so give it the whole context; otherwise only pass what
        # it actually declared.
        if key in params or accepts_kwargs:
            kwargs[key] = value
    return kwargs


#: How the control plane (the process running Yardstick) relates to the data
#: plane (the machines running the game, the players and the metrics stack).
DEPLOYMENT_MODES = ("local", "cloud", "cluster")


@dataclass
class DeploymentConfig:
    """Which machines to run on, and where to put things on them.

    ``mode`` names the topology:

    ``local``
        Control plane and data plane are the same machine. Everything runs
        where you started Yardstick. This is the mode that works today.

    ``cloud``
        Control plane is your local machine; the data plane is a set of
        remote hosts you name in ``hosts``.

    ``cluster``
        Control plane is the cluster's head node; the data plane is the
        worker nodes you reserved. On DAS-6 you run Yardstick on the head
        node and it drives the nodes from ``preserve``.

    ``cloud`` and ``cluster`` both need Yardstick to stage files onto a
    machine other than the one it runs on, which is not implemented yet (see
    :func:`yardstick_benchmark.util.stage`). Configurations using them are
    rejected up front rather than failing partway through a deployment.
    """

    mode: str = "local"
    hosts: List[str] = field(default_factory=lambda: ["localhost"])
    wd: str = "/tmp/yardstick"
    #: Host running the game server. Defaults to the first entry in `hosts`.
    server_host: Optional[str] = None

    def resolved_server_host(self) -> str:
        return self.server_host or self.hosts[0]

    def workload_hosts(self) -> List[str]:
        """Hosts that run emulated players.

        Every host except the server's -- or the server's own host when
        that's the only one available, which is the single-machine case.
        """
        others = [h for h in self.hosts if h != self.resolved_server_host()]
        return others or [self.resolved_server_host()]


@dataclass
class MonitoringConfig:
    """What to collect while the workload runs."""

    enabled: bool = True
    #: Scrape the game server's JVM through its Jolokia agent.
    jolokia: bool = True
    #: Run the Go collector that samples Minecraft's per-tick durations.
    minecraft_ticks: bool = True


@dataclass
class OutputConfig:
    """Where results go."""

    dir: str = "results"
    #: Keep each node's working directory (worlds, logs, raw database) after
    #: the run instead of deleting it.
    keep_node_data: bool = False


@dataclass
class BenchmarkConfig:
    """A whole benchmark, as described by a configuration file."""

    game: str = "minecraft"
    game_options: Dict[str, Any] = field(default_factory=dict)
    workload: str = "worldgen"
    workload_options: Dict[str, Any] = field(default_factory=dict)
    deployment: DeploymentConfig = field(default_factory=DeploymentConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def from_toml(cls, path: Union[str, Path]) -> "BenchmarkConfig":
        path = Path(path)
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except FileNotFoundError as exc:
            raise ConfigError(f"no such configuration file: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(f"{path}: invalid TOML ({exc})") from exc
        return cls.from_dict(data, where=str(path))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], where: str = "") -> "BenchmarkConfig":
        known_sections = {"deployment", "game", "workload", "monitoring", "output"}
        unknown = set(data) - known_sections
        if unknown:
            raise ConfigError(
                f"{where}: unknown section(s) {', '.join(sorted(unknown))}. "
                f"Known sections: {', '.join(sorted(known_sections))}"
            )

        def section(name: str) -> Dict[str, Any]:
            value = data.get(name, {})
            if not isinstance(value, dict):
                raise ConfigError(f"{where}: [{name}] must be a table")
            return dict(value)

        def typed(name: str, registry: Mapping[str, type], default: str):
            raw = section(name)
            type_name = raw.pop("type", default)
            if not isinstance(type_name, str):
                raise ConfigError(f"{where}: [{name}] type must be a string")
            # Fail fast on an unknown name, rather than after a deployment.
            resolve(type_name, registry, name)
            return type_name, raw

        game, game_options = typed("game", GAMES, "minecraft")
        workload, workload_options = typed("workload", WORKLOADS, "worldgen")

        return cls(
            game=game,
            game_options=game_options,
            workload=workload,
            workload_options=workload_options,
            deployment=_build_section(DeploymentConfig, section("deployment"), where),
            monitoring=_build_section(MonitoringConfig, section("monitoring"), where),
            output=_build_section(OutputConfig, section("output"), where),
        )

    @property
    def game_class(self) -> type:
        return resolve(self.game, GAMES, "game")

    @property
    def workload_class(self) -> type:
        return resolve(self.workload, WORKLOADS, "workload")

    def validate(self) -> None:
        """Check the configuration builds, without deploying anything.

        Resolves both classes and assembles their constructor arguments, so
        an unknown option or an unparsable duration is reported now rather
        than after the images have been pulled.
        """
        if self.deployment.mode not in DEPLOYMENT_MODES:
            raise ConfigError(
                f"[deployment] unknown mode {self.deployment.mode!r}. "
                f"Valid modes: {', '.join(DEPLOYMENT_MODES)}"
            )
        # Structural problems first: they're true regardless of which mode is
        # supported, so report them before the capability limit below.
        if not self.deployment.hosts:
            raise ConfigError("[deployment] hosts must list at least one host")
        server_host = self.deployment.resolved_server_host()
        if server_host not in self.deployment.hosts:
            raise ConfigError(
                f"[deployment] server_host {server_host!r} is not in hosts "
                f"{self.deployment.hosts}"
            )
        if self.deployment.mode != "local":
            raise ConfigError(
                f"[deployment] mode = {self.deployment.mode!r} is not "
                f"supported yet: Yardstick cannot yet stage files onto a "
                f"machine other than the one it runs on (see "
                f"yardstick_benchmark.util.stage). Use mode = 'local' and run "
                f"Yardstick on the machine that should host the deployment."
            )
        remote_hosts = [h for h in self.deployment.hosts if not is_localhost(h)]
        if remote_hosts:
            raise ConfigError(
                f"[deployment] mode = 'local' runs everything on this machine, "
                f"but hosts names {', '.join(remote_hosts)}. Either use "
                f"hosts = ['localhost'], or run Yardstick on the machine you "
                f"want the deployment on."
            )
        build_kwargs(self.game_class, self.game_options, where="[game]")
        build_kwargs(
            self.workload_class,
            self.workload_options,
            context={
                # Values the runner supplies; included here so validation
                # doesn't reject a workload for lacking them.
                "server_host": server_host,
                "rcon_password": "",
                "influxdb_info": None,
                "bot_index": 0,
                "total_bots": 1,
                "minecraft_version": "",
            },
            where="[workload]",
        )


def _build_section(cls: type, values: Mapping[str, Any], where: str):
    fields = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    unknown = set(values) - fields
    if unknown:
        raise ConfigError(
            f"{where}: [{cls.__name__}] has no option "
            f"{', '.join(repr(k) for k in sorted(unknown))}. "
            f"Available options: {', '.join(sorted(fields))}"
        )
    return cls(**values)


EXAMPLE_CONFIG = """\
# Yardstick benchmark configuration.
#
# Run it with:  yardstick run experiment.toml
# Check it with: yardstick validate experiment.toml

[deployment]
# How the control plane (this process) relates to the data plane (the
# machines running the game, the players and the metrics stack):
#
#   local    both are this machine -- everything runs where you start
#            Yardstick. The only mode supported today.
#   cloud    control plane here, data plane on remote hosts.
#   cluster  control plane on a cluster head node, data plane on the worker
#            nodes you reserved (e.g. with `preserve` on DAS-6).
#
# cloud and cluster need Yardstick to copy files onto another machine, which
# is not implemented yet (see yardstick_benchmark.util.stage). Until then,
# run Yardstick on the machine that should host the deployment.
mode = "local"
hosts = ["localhost"]
# Working directory on each node. Worlds, logs and the metrics database live
# here during a run.
wd = "/tmp/yardstick"

[game]
type = "minecraft"
# Pin the world seed to make world generation reproducible across runs.
seed = "yardstick"
memory = "4G"
max_players = 100
view_distance = 10
simulation_distance = 10

[monitoring]
enabled = true
jolokia = true
minecraft_ticks = true

[workload]
# "worldgen" or "walkaround", or the import path of your own class.
type = "worldgen"
bots_per_node = 4
teleports = 16

[output]
dir = "results"
keep_node_data = false
"""
