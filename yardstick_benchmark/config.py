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
from yardstick_benchmark.provisioning import Das, ProvisioningError, Ubicloud
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

#: Short names usable as ``[provisioning] provider``.
PROVIDERS: Dict[str, type] = {
    "ubicloud": Ubicloud,
    "das": Das,
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
class ProvisioningConfig:
    """How to acquire machines, for the modes that need to.

    Options other than those named here are passed to the provider's
    constructor, so provider-specific settings (an Ubicloud location, the SSH
    key to install, machine sizes) live here without this module having to
    mirror them. ``[provisioning.server]`` and ``[provisioning.workload]``
    override them for one group of machines:

        [provisioning]
        provider = "ubicloud"
        workload_nodes = 2
        location = "eu-central-h1"

        [provisioning.server]
        size = "standard-4"

        [provisioning.workload]
        size = "standard-2"
    """

    provider: str = "ubicloud"
    #: Machines to run emulated players on. The game server always gets one
    #: of its own, so that the players never compete with it for CPU.
    workload_nodes: int = 1
    #: Options shared by both groups, passed to the provider's constructor.
    options: Dict[str, Any] = field(default_factory=dict)
    #: Per-group overrides.
    server: Dict[str, Any] = field(default_factory=dict)
    workload: Dict[str, Any] = field(default_factory=dict)

    def options_for(self, group: str) -> Dict[str, Any]:
        """Constructor options for one group of machines."""
        merged = dict(self.options)
        merged.update(self.server if group == "server" else self.workload)
        return merged


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
    provisioning: ProvisioningConfig = field(default_factory=ProvisioningConfig)
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
        known_sections = {
            "deployment",
            "game",
            "workload",
            "monitoring",
            "output",
            "provisioning",
        }
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
            provisioning=_build_provisioning(section("provisioning"), where),
            monitoring=_build_section(MonitoringConfig, section("monitoring"), where),
            output=_build_section(OutputConfig, section("output"), where),
        )

    @property
    def provider_class(self) -> type:
        return resolve(self.provisioning.provider, PROVIDERS, "provider")

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
        if self.deployment.mode == "local":
            remote_hosts = [h for h in self.deployment.hosts if not is_localhost(h)]
            if remote_hosts:
                raise ConfigError(
                    f"[deployment] mode = 'local' runs everything on this "
                    f"machine, but hosts names {', '.join(remote_hosts)}. "
                    f"Either use hosts = ['localhost'], or run Yardstick on "
                    f"the machine you want the deployment on."
                )
        else:
            if self.provisioning.workload_nodes < 1:
                raise ConfigError("[provisioning] workload_nodes must be at least 1")
            provider = self.provider_class
            for group in ("server", "workload"):
                where = f"[provisioning.{group}]"
                kwargs = build_kwargs(
                    provider, self.provisioning.options_for(group), where=where
                )
                # Actually construct it: the provider's own guards (machine
                # size, storage size, a missing SSH key) live in __init__,
                # and checking option *names* alone would let a run get as
                # far as provisioning before hitting them. Constructing a
                # provisioner touches nothing remote.
                try:
                    provider(**kwargs)
                except ProvisioningError as exc:
                    raise ConfigError(f"{where}: {exc}") from exc
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


def _build_provisioning(values: Mapping[str, Any], where: str) -> ProvisioningConfig:
    """Split the [provisioning] table into named fields and provider options."""
    raw = dict(values)
    server = raw.pop("server", {})
    workload = raw.pop("workload", {})
    for name, value in (("server", server), ("workload", workload)):
        if not isinstance(value, dict):
            raise ConfigError(f"{where}: [provisioning.{name}] must be a table")
    provider = raw.pop("provider", "ubicloud")
    workload_nodes = raw.pop("workload_nodes", 1)
    if not isinstance(workload_nodes, int) or isinstance(workload_nodes, bool):
        raise ConfigError(f"{where}: [provisioning] workload_nodes must be an integer")
    # Fail fast on an unknown provider, rather than after a deployment.
    resolve(str(provider), PROVIDERS, "provider")
    return ProvisioningConfig(
        provider=str(provider),
        workload_nodes=workload_nodes,
        options=raw,
        server=dict(server),
        workload=dict(workload),
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
# Run it with:   yardstick run experiment.toml
# Check it with: yardstick validate experiment.toml

[deployment]
# How the control plane (this process) relates to the data plane (the
# machines running the game, the players and the metrics stack):
#
#   local    both are this machine -- everything runs where you start
#            Yardstick.
#   cloud    control plane here, data plane on VMs provisioned on demand.
#   cluster  control plane on a cluster head node, data plane on worker
#            nodes reserved with `preserve` (e.g. DAS-6).
#
# For cloud and cluster, see [provisioning] below.
mode = "local"
hosts = ["localhost"]
# Working directory on each node. Worlds, logs and the metrics database live
# here during a run.
wd = "/tmp/yardstick"

# Only used when mode is "cloud" or "cluster".
#
# [provisioning]
# provider = "ubicloud"          # or "das", or an import path
# workload_nodes = 1             # machines running emulated players; the
#                                # game server always gets one to itself
# location = "eu-central-h1"     # options here go to the provider, and are
#                                # shared by both groups below
#
# The game server wants headroom over its JVM heap (4 GB by default) and
# several cores for chunk generation; the emulated players are much lighter.
# yardstick_benchmark.saturation checks after every run whether the workload
# machines were actually the bottleneck, so you find out if these are too
# small rather than quietly measuring the wrong thing.
#
# [provisioning.server]
# size = "standard-4"            # 4 vCPU / 16 GB on Ubicloud
#
# [provisioning.workload]
# size = "standard-2"            # 2 vCPU / 8 GB

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
