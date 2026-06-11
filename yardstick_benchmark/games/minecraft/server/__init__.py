from pathlib import Path
from plumbum import local
import tempfile
import threading
import uuid
from typing import Optional

from yardstick_benchmark.util import random_string, wait_for_tcp


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


class MinecraftServerCrashed(RuntimeError):
    """Raised when the Minecraft server's log/crash-reports show it crashed."""


# https://gist.github.com/tensoralex/a278b39a965d7c509dbd06b57797c6c1
class MinecraftServer:
    """Runs a Minecraft server in apptainer with Jolokia + RCON attached.

    The Jolokia Java agent (shipped with this package) is bind-mounted into
    the upstream itzg/minecraft-server image, so no custom container image
    needs to be built or pulled. RCON is enabled with an auto-generated
    password (override via the rcon_password constructor kwarg) and is used
    for in-band server commands like set_world_spawn().
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

    def __init__(
        self,
        name: str = "",
        image_url: str = DEFAULT_IMAGE_URL,
        rcon_password: str = "",
        version: str = DEFAULT_VERSION,
        max_tick_time: int = DEFAULT_MAX_TICK_TIME,
    ) -> None:
        self.image_url = image_url
        self.data_dir = tempfile.mkdtemp(dir="/tmp", prefix="mc-data-")
        self.instance_name = name if name else f"mc-{uuid.uuid4()}"
        self.rcon_password = rcon_password or random_string(16)
        self.version = version
        self.max_tick_time = max_tick_time
        self.running = False
        # Background health monitor state (see start_health_monitor()).
        self._crash: Optional[MinecraftServerCrashed] = None
        self._monitor_stop: Optional[threading.Event] = None
        self._monitor_thread: Optional[threading.Thread] = None

    def start(self):
        jvm_opts = (
            f"-javaagent:/opt/jolokia.jar=port={JOLOKIA_PORT},host=0.0.0.0"
        )
        res = local["apptainer"].run(
            (
                "instance",
                "run",
                "--no-https",
                "--compat",
                "--bind",
                f"{self.data_dir}:/data",
                "--bind",
                f"{JOLOKIA_JAR}:/opt/jolokia.jar",
                "--env",
                "EULA=TRUE",
                "--env",
                f"VERSION={self.version}",
                "--env",
                "ONLINE_MODE=false",
                "--env",
                "ENABLE_JMX=true",
                "--env",
                "ENABLE_RCON=true",
                "--env",
                f"RCON_PASSWORD={self.rcon_password}",
                "--env",
                f"MAX_TICK_TIME={self.max_tick_time}",
                "--env",
                f"JVM_OPTS={jvm_opts}",
                self.image_url,
                self.instance_name,
            )
        )
        if res[0] == 0:
            self.running = True
        else:
            raise RuntimeError(
                f"Failed to start Minecraft server instance {self.instance_name}"
            )

    def stop(self):
        res = local["apptainer"].run(("instance", "stop", self.instance_name))
        if res[0] == 0:
            self.running = False
        else:
            raise RuntimeError(
                f"Failed to stop Minecraft server instance {self.instance_name}"
            )

    def wait_until_ready(self, timeout_s: float = 180) -> None:
        """Block until the server has finished booting and is ready to accept
        both gameplay connections and RCON commands.

        Polls the RCON listener port (25575). Minecraft binds RCON *after*
        the game port (25565) and after its "Done!" startup log line, so a
        successful return here means rcon() / set_world_spawn() will work
        and the server is fully ticking.
        """
        wait_for_tcp("localhost", RCON_PORT, timeout_s=timeout_s)

    def rcon(self, *commands: str) -> None:
        """Send one or more commands to the running server via RCON.

        Uses the rcon-cli binary that itzg/minecraft-server bundles by
        execing straight into the running instance, so no extra container
        is launched. The server must already be started and accepting
        connections (use a TCP-readiness check on the game port before
        calling this).
        """
        if not commands:
            return
        local["apptainer"].run(
            (
                "exec",
                "--env", "RCON_HOST=localhost",
                "--env", f"RCON_PORT={RCON_PORT}",
                "--env", f"RCON_PASSWORD={self.rcon_password}",
                f"instance://{self.instance_name}",
                "rcon-cli",
                *commands,
            )
        )

    def set_world_spawn(self, x: int, z: int, y: int = 4) -> None:
        """Move the world spawn to (x, y, z) via RCON."""
        self.rcon(f"setworldspawn {x} {y} {z}")

    def raise_if_crashed(self) -> None:
        """Raise MinecraftServerCrashed if the server's log/crash-reports show
        a crash (a Watchdog forced shutdown, an OOM, or any unhandled error).

        Cheap and idempotent -- meant to be polled by the orchestrator (e.g.
        each iteration of the loop that waits for a workload to finish) so a
        server crash aborts the run promptly instead of letting clients spin
        against a dead server. Reads the server's own log under its data dir;
        for an off-headnode server this read will move behind `remote()`.
        """
        # A crash-report file is the unambiguous signal: vanilla writes here
        # only when the server actually crashes. Prefer it for the message.
        crash_dir = Path(self.data_dir) / "crash-reports"
        reports = sorted(crash_dir.glob("*.txt")) if crash_dir.is_dir() else []
        if reports:
            detail = reports[-1].read_text(errors="replace")[:2000]
            raise MinecraftServerCrashed(
                f"Minecraft server '{self.instance_name}' crashed "
                f"(see {reports[-1]}):\n{detail}"
            )
        # Fall back to scanning the console log for crash markers.
        log = Path(self.data_dir) / "logs" / "latest.log"
        if log.is_file():
            text = log.read_text(errors="replace")
            for marker in _CRASH_LOG_MARKERS:
                if marker in text:
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
        `health_check` passed to a workload's wait()). Idempotent-ish: call
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
