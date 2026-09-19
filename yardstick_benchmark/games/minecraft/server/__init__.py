"""Minecraft game server, deployed as an apptainer instance.

Wraps the upstream ``itzg/minecraft-server`` image. The Jolokia Java agent
(shipped with this package) is bind-mounted in, so no custom container image
needs to be built or pulled. RCON is enabled with an auto-generated password
and is used for in-band server commands like :meth:`set_world_spawn`.
"""

from pathlib import Path
from typing import Dict, List, Optional
import threading
import uuid

from yardstick_benchmark.model import Node
from yardstick_benchmark.util import random_string, remote, wait_for_tcp


JOLOKIA_JAR = Path(__file__).parent / "jolokia-agent-jvm-2.5.1-javaagent.jar"
JOLOKIA_PORT = 8778
GAME_PORT = 25565
RCON_PORT = 25575

# Substrings in the server console log that indicate a crash / forced
# shutdown. The crash-report header covers crashes that produce a report; the
# Watchdog only logs at ERROR level when it's force-crashing the server, so any
# "Watchdog/ERROR" line is a crash (caught even if the message wording changes,
# and only relevant if the Watchdog is re-enabled -- it's off by default); and
# the JVM OutOfMemoryError is matched directly because an OOM can kill the
# server (or leave it wedged) without always emitting a Minecraft crash report.
_CRASH_LOG_MARKERS = (
    "---- Minecraft Crash Report ----",
    "Watchdog/ERROR",
    "java.lang.OutOfMemoryError",
)


def _flag(value: bool) -> str:
    """Render a Python bool the way server.properties expects it."""
    return "true" if value else "false"


class MinecraftServerCrashed(RuntimeError):
    """Raised when the Minecraft server's log/crash-reports show it crashed."""


# https://gist.github.com/tensoralex/a278b39a965d7c509dbd06b57797c6c1
class MinecraftServer:
    """Run a Minecraft server on one node.

    Follows the standard component lifecycle: ``deploy()``, ``start()``,
    ``stop()``, ``cleanup()``. All server state (world, logs, crash reports)
    lives under ``node.wd`` so it is picked up by
    :func:`yardstick_benchmark.fetch` and removed by
    :func:`yardstick_benchmark.clean`.

    Most constructor arguments map onto a ``server.properties`` entry via the
    corresponding itzg image environment variable. Anything not exposed here
    can be set through ``extra_env``.
    """

    DEFAULT_IMAGE_URL = "docker://itzg/minecraft-server:java25"

    # Newest Minecraft version the bundled Mineflayer (and its
    # minecraft-data) in the workload image understands. itzg's default
    # VERSION=LATEST tracks the newest release, which routinely outpaces
    # minecraft-data -- and a server the bots can't speak the protocol of is
    # useless for a benchmark -- so we pin to a known-supported version by
    # default. Bump this when the workload image's Mineflayer is upgraded.
    DEFAULT_VERSION = "1.21.11"

    # Disable Minecraft's Watchdog by default (max-tick-time = -1). The
    # Watchdog force-crashes the server if a single tick exceeds ~60s, which a
    # heavy world-generation workload (many players loading fresh chunks at
    # once) trivially trips -- self-crashing the very server we're measuring.
    # For a benchmark we want load to make the server *slow*, not kill it.
    DEFAULT_MAX_TICK_TIME = -1

    # JVM heap (itzg MEMORY env -> -Xms/-Xmx). itzg defaults to 1G, which a
    # world-gen workload (many players streaming fresh chunks) exhausts ->
    # java.lang.OutOfMemoryError. Default to a roomier heap so memory isn't
    # the bottleneck; bump it via the `memory` kwarg for heavier runs.
    DEFAULT_MEMORY = "4G"

    # itzg (like vanilla) caps the server at 20 players, which silently
    # rejects bots in any benchmark run larger than that. A scalability
    # benchmark wants no artificial cap, so default it out of the way.
    DEFAULT_MAX_PLAYERS = 999

    # Chunk radius the server sends to / simulates for each player. These are
    # the two knobs that dominate server load per player, so they're the ones
    # experiments sweep most often.
    DEFAULT_VIEW_DISTANCE = 10
    DEFAULT_SIMULATION_DISTANCE = 10

    def __init__(
        self,
        node: Node,
        name: str = "",
        image_url: str = DEFAULT_IMAGE_URL,
        rcon_password: str = "",
        version: str = DEFAULT_VERSION,
        max_tick_time: int = DEFAULT_MAX_TICK_TIME,
        memory: str = DEFAULT_MEMORY,
        max_players: int = DEFAULT_MAX_PLAYERS,
        seed: Optional[str] = None,
        view_distance: int = DEFAULT_VIEW_DISTANCE,
        simulation_distance: int = DEFAULT_SIMULATION_DISTANCE,
        difficulty: str = "easy",
        gamemode: str = "survival",
        level_name: str = "world",
        pvp: bool = True,
        online_mode: bool = False,
        spawn_protection: int = 0,
        motd: Optional[str] = None,
        game_port: int = GAME_PORT,
        rcon_port: int = RCON_PORT,
        jolokia_port: int = JOLOKIA_PORT,
        extra_env: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Args:
            node: Node to run the server on.
            name: Apptainer instance name. Defaults to a unique generated
                name, so several servers can coexist on one node.
            image_url: Container image to run.
            rcon_password: RCON password. Generated if empty.
            version: Minecraft version. Must be one the workload image's
                Mineflayer can speak; see DEFAULT_VERSION.
            max_tick_time: server.properties max-tick-time. -1 disables the
                Watchdog; see DEFAULT_MAX_TICK_TIME.
            memory: JVM heap size (itzg MEMORY), e.g. "4G".
            max_players: server.properties max-players.
            seed: server.properties level-seed. Pin this to make world
                generation reproducible across runs; None lets the server
                pick a random world.
            view_distance: server.properties view-distance, in chunks.
            simulation_distance: server.properties simulation-distance, in
                chunks.
            difficulty: server.properties difficulty.
            gamemode: server.properties gamemode.
            level_name: server.properties level-name (the world directory).
            pvp: server.properties pvp.
            online_mode: server.properties online-mode. Must stay False for
                emulated players, which have no Mojang accounts.
            spawn_protection: server.properties spawn-protection, in blocks.
                Defaults to 0 so bots aren't restricted near spawn.
            motd: server.properties motd. None keeps the image default.
            game_port: Port the server listens on for gameplay.
            rcon_port: Port the server listens on for RCON.
            jolokia_port: Port the Jolokia agent exposes its REST API on.
            extra_env: Additional environment variables passed to the image,
                for any itzg setting not exposed above. Applied last, so it
                overrides the values derived from the arguments here.
        """
        self.node = node
        self.image_url = image_url
        self.instance_name = name if name else f"mc-{uuid.uuid4()}"
        self.rcon_password = rcon_password or random_string(16)
        self.version = version
        self.max_tick_time = max_tick_time
        self.memory = memory
        self.max_players = max_players
        self.seed = seed
        self.view_distance = view_distance
        self.simulation_distance = simulation_distance
        self.difficulty = difficulty
        self.gamemode = gamemode
        self.level_name = level_name
        self.pvp = pvp
        self.online_mode = online_mode
        self.spawn_protection = spawn_protection
        self.motd = motd
        self.game_port = game_port
        self.rcon_port = rcon_port
        self.jolokia_port = jolokia_port
        self.extra_env = dict(extra_env) if extra_env else {}
        self.running = False
        # Server state lives under the node's working directory (rather than
        # a private /tmp dir) so fetch() collects it and clean() removes it.
        self.wd = f"{node.wd}/{self.instance_name}"
        self.data_dir = f"{self.wd}/data"
        # Background health monitor state (see start_health_monitor()).
        self._crash: Optional[MinecraftServerCrashed] = None
        self._monitor_stop: Optional[threading.Event] = None
        self._monitor_thread: Optional[threading.Thread] = None

    def _env(self) -> Dict[str, str]:
        """The image environment derived from this server's configuration."""
        jvm_opts = f"-javaagent:/opt/jolokia.jar=port={self.jolokia_port},host=0.0.0.0"
        env = {
            "EULA": "TRUE",
            "MEMORY": self.memory,
            "VERSION": self.version,
            "ENABLE_JMX": "true",
            "ENABLE_RCON": "true",
            "RCON_PASSWORD": self.rcon_password,
            "SERVER_PORT": str(self.game_port),
            "RCON_PORT": str(self.rcon_port),
            # The data dir persists across restarts now that it lives under
            # node.wd, so tell itzg to re-apply these settings to an existing
            # server.properties instead of leaving the first run's values.
            "OVERRIDE_SERVER_PROPERTIES": "true",
            "MAX_TICK_TIME": str(self.max_tick_time),
            "MAX_PLAYERS": str(self.max_players),
            "VIEW_DISTANCE": str(self.view_distance),
            "SIMULATION_DISTANCE": str(self.simulation_distance),
            "DIFFICULTY": self.difficulty,
            "MODE": self.gamemode,
            "LEVEL": self.level_name,
            "PVP": _flag(self.pvp),
            "ONLINE_MODE": _flag(self.online_mode),
            "SPAWN_PROTECTION": str(self.spawn_protection),
            "JVM_OPTS": jvm_opts,
        }
        if self.seed is not None:
            env["SEED"] = str(self.seed)
        if self.motd is not None:
            env["MOTD"] = self.motd
        env.update(self.extra_env)
        return env

    def _env_args(self) -> List[str]:
        args: List[str] = []
        for key, value in self._env().items():
            args += ["--env", f"{key}={value}"]
        return args

    def deploy(self) -> None:
        """Create the server's working directory on the node."""
        with remote(self.node.host) as machine:
            machine["mkdir"]["-p", self.data_dir]()

    def start(self) -> None:
        """Launch the server as a background apptainer instance.

        Creates the data directory first if deploy() wasn't called: apptainer
        fails with an opaque bind error when the source path is missing, and
        the mkdir is idempotent and cheap.
        """
        with remote(self.node.host) as machine:
            machine["mkdir"]["-p", self.data_dir]()
            args = (
                [
                    "instance",
                    "run",
                    "--no-https",
                    "--compat",
                    "--bind",
                    f"{self.data_dir}:/data",
                    "--bind",
                    f"{JOLOKIA_JAR}:/opt/jolokia.jar",
                ]
                + self._env_args()
                + [self.image_url, self.instance_name]
            )
            machine["apptainer"][args]()
        self.running = True

    def stop(self) -> None:
        """Stop the server instance. Safe to call if it never started."""
        self.stop_health_monitor()
        with remote(self.node.host) as machine:
            machine["apptainer"]["instance", "stop", self.instance_name].run(
                retcode=None
            )
        self.running = False

    def cleanup(self) -> None:
        """Remove the server's working directory (world, logs, crash reports)."""
        with remote(self.node.host) as machine:
            machine["rm"]["-rf", self.wd](retcode=None)

    def wait_until_ready(self, timeout_s: float = 180) -> None:
        """Block until the server has finished booting and is ready to accept
        both gameplay connections and RCON commands.

        Polls the RCON listener port. Minecraft binds RCON *after* the game
        port and after its "Done!" startup log line, so a successful return
        here means rcon() / set_world_spawn() will work and the server is
        fully ticking.
        """
        wait_for_tcp(self.node.host, self.rcon_port, timeout_s=timeout_s)

    def ready(self, timeout_s: float = 180) -> None:
        """Alias for wait_until_ready(), the hook Deployment looks for."""
        self.wait_until_ready(timeout_s=timeout_s)

    def rcon(self, *commands: str) -> None:
        """Send one or more commands to the running server via RCON.

        Uses the rcon-cli binary that itzg/minecraft-server bundles by
        execing straight into the running instance, so no extra container
        is launched. The server must already be started and accepting
        connections (see wait_until_ready()).
        """
        if not commands:
            return
        args = [
            "exec",
            "--env",
            "RCON_HOST=localhost",
            "--env",
            f"RCON_PORT={self.rcon_port}",
            "--env",
            f"RCON_PASSWORD={self.rcon_password}",
            f"instance://{self.instance_name}",
            "rcon-cli",
        ] + list(commands)
        with remote(self.node.host) as machine:
            machine["apptainer"][args]()

    def set_world_spawn(self, x: int, z: int, y: int = 4) -> None:
        """Move the world spawn to (x, y, z) via RCON."""
        self.rcon(f"setworldspawn {x} {y} {z}")

    def raise_if_crashed(self) -> None:
        """Raise MinecraftServerCrashed if the server's log/crash-reports show
        a crash (a Watchdog forced shutdown, an OOM, or any unhandled error).

        Cheap and idempotent -- meant to be polled by the orchestrator (e.g.
        each iteration of the loop that waits for a workload to finish) so a
        server crash aborts the run promptly instead of letting clients spin
        against a dead server. The log scan runs as a `grep` on the node, so
        a long run's console log is never pulled across in full.
        """
        with remote(self.node.host) as machine:
            # A crash-report file is the unambiguous signal: vanilla writes
            # here only when the server actually crashes. Prefer it for the
            # message.
            crash_dir = machine.path(f"{self.data_dir}/crash-reports")
            reports = sorted(crash_dir // "*.txt") if crash_dir.is_dir() else []
            if reports:
                try:
                    detail = machine["head"]["-c", "2000", str(reports[-1])]()
                except Exception:
                    detail = "(could not read crash report)"
                raise MinecraftServerCrashed(
                    f"Minecraft server '{self.instance_name}' crashed "
                    f"(see {reports[-1]}):\n{detail}"
                )
            # Fall back to scanning the console log for crash markers. -a
            # keeps grep in text mode even if the log picked up a stray
            # non-UTF-8 byte; -o -m1 makes it print just the first marker it
            # matched, which is what we report.
            log = machine.path(f"{self.data_dir}/logs/latest.log")
            if not log.is_file():
                return
            args = ["-a", "-o", "-m", "1", "-F"]
            for marker in _CRASH_LOG_MARKERS:
                args += ["-e", marker]
            args.append(str(log))
            retcode, out, _ = machine["grep"][args].run(retcode=None)
        if retcode != 0:
            return
        matched = out.strip().splitlines()
        marker = matched[0] if matched else "unknown"
        raise MinecraftServerCrashed(
            f"Minecraft server '{self.instance_name}' crash "
            f"detected in log (marker: {marker!r})"
        )

    def start_health_monitor(self, interval_s: float = 5.0) -> None:
        """Begin polling the server's health in the background.

        Spawns a daemon thread that calls raise_if_crashed() every
        `interval_s` while the server runs as a background service; the first
        detected crash is recorded and the thread stops. The orchestrator
        surfaces it cheaply on its own thread via assert_healthy() (e.g. as the
        `health_check` passed to a workload's run()). Idempotent-ish: call
        stop_health_monitor() before re-starting.
        """
        self.stop_health_monitor()
        self._crash = None
        stop = threading.Event()
        self._monitor_stop = stop

        def _loop() -> None:
            while not stop.wait(interval_s):
                try:
                    self.raise_if_crashed()
                except MinecraftServerCrashed as exc:
                    self._crash = exc
                    return
                except Exception:
                    # A transient read error (log rotating, node briefly
                    # unreachable) must not kill the monitor.
                    continue

        self._monitor_thread = threading.Thread(
            target=_loop, name=f"mc-health-{self.instance_name}", daemon=True
        )
        self._monitor_thread.start()

    def stop_health_monitor(self) -> None:
        """Stop the background health monitor (if running)."""
        if self._monitor_stop is not None:
            self._monitor_stop.set()
        if self._monitor_thread is not None:
            self._monitor_thread.join(timeout=5)
        self._monitor_stop = None
        self._monitor_thread = None

    def assert_healthy(self) -> None:
        """Raise the crash the background monitor caught, if any. Cheap to call
        repeatedly -- it only checks a flag, doing no log I/O itself."""
        if self._crash is not None:
            raise self._crash
