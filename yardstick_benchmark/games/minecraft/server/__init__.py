from pathlib import Path
import threading
import uuid
from typing import Optional

from yardstick_benchmark.model import Node
from yardstick_benchmark.util import random_string, remote, upload, wait_for_tcp


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

    The server runs on the ``node`` it's constructed with: start/stop, RCON,
    and crash-log reads all go through ``remote()``, so on a provisioned
    compute node the container runs there over SSH (the headnode runs no
    container). ``node`` defaults to a localhost node, so single-machine
    callers (and the bundled example/tests) work unchanged.
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
        node: Optional[Node] = None,
        image_url: str = DEFAULT_IMAGE_URL,
        rcon_password: str = "",
        version: str = DEFAULT_VERSION,
        max_tick_time: int = DEFAULT_MAX_TICK_TIME,
        memory: Optional[str] = None,
        view_distance: Optional[int] = None,
    ) -> None:
        # JVM heap (itzg MEMORY env -> -Xms/-Xmx). itzg defaults to 1G, which a
        # world-gen workload (many players streaming fresh chunks) exhausts ->
        # java.lang.OutOfMemoryError. When `memory` is None we default to half
        # the *server node's* total RAM (resolved at start() over remote(),
        # since the node may differ from the headnode) -- a roomier heap so
        # memory isn't the bottleneck while leaving the other half for the OS,
        # page cache, and the JVM's off-heap use. Pass an explicit value (e.g.
        # "8G") to override.
        # Default to a localhost node so single-machine callers keep working
        # without passing a Node; pass a provisioned Node to run the server on
        # a remote compute node.
        self.node = node if node is not None else Node("localhost", Path("/tmp"))
        self.image_url = image_url
        # World data, logs, and crash-reports live under the node's working
        # dir (node-local disk on a compute node) and are bind-mounted into the
        # container at /data. Staged on the node by start(); read back for
        # crash detection over remote().
        self.data_dir = f"{self.node.wd}/mc-data-{random_string(8)}"
        # Where start() stages the bundled Jolokia agent jar on the node, so it
        # can be bind-mounted into the container (apptainer requires every
        # --bind source to exist on the machine running the container).
        self.jar_on_node = f"{self.node.wd}/jolokia-agent-{random_string(8)}.jar"
        self.instance_name = name if name else f"mc-{uuid.uuid4()}"
        self.rcon_password = rcon_password or random_string(16)
        self.version = version
        self.max_tick_time = max_tick_time
        self.memory = memory
        # Server render distance (itzg VIEW_DISTANCE env). Chunks generated per
        # player scale ~quadratically with this, so it's the dominant knob on
        # world-gen load. None leaves itzg's default (10); lower it (e.g. 6) to
        # cut generation cost per teleport.
        self.view_distance = view_distance
        self.running = False
        # Background health monitor state (see start_health_monitor()).
        self._crash: Optional[MinecraftServerCrashed] = None
        self._monitor_stop: Optional[threading.Event] = None
        self._monitor_thread: Optional[threading.Thread] = None

    def _resolve_memory(self, machine) -> str:
        """The itzg MEMORY value to use: the explicit `memory` if set, else
        half of the node's total RAM (read from /proc/meminfo on `machine`)."""
        if self.memory:
            return self.memory
        meminfo = machine["cat"]["/proc/meminfo"]()
        total_kb = None
        for line in meminfo.splitlines():
            if line.startswith("MemTotal:"):
                # "MemTotal:       65799324 kB" -- value is in kB.
                total_kb = int(line.split()[1])
                break
        if total_kb is None:
            raise RuntimeError(
                f"could not read MemTotal from /proc/meminfo on {self.node.host}"
            )
        # Half the RAM, in MiB (itzg accepts e.g. "32768M").
        return f"{total_kb // 2 // 1024}M"

    def start(self):
        jvm_opts = (
            f"-javaagent:/opt/jolokia.jar=port={JOLOKIA_PORT},host=0.0.0.0"
        )
        with remote(self.node.host) as machine:
            memory = self._resolve_memory(machine)
            # Stage the data dir and the Jolokia agent jar on the node:
            # apptainer requires every --bind source to already exist on the
            # machine that runs the container (the compute node for a remote
            # run). For localhost this is a plain mkdir + local file copy.
            machine["mkdir"]["-p", self.data_dir]()
            # upload() scp's the jar to a remote node; the parent dir
            # (node.wd) exists thanks to the mkdir above (data_dir is under it).
            upload(machine, JOLOKIA_JAR, self.jar_on_node)
            args = [
                "instance",
                "run",
                "--no-https",
                "--compat",
                "--bind",
                f"{self.data_dir}:/data",
                "--bind",
                f"{self.jar_on_node}:/opt/jolokia.jar",
                "--env",
                "EULA=TRUE",
                "--env",
                f"MEMORY={memory}",
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
            ]
            if self.view_distance is not None:
                args += ["--env", f"VIEW_DISTANCE={self.view_distance}"]
            args += [self.image_url, self.instance_name]
            res = machine["apptainer"].run(tuple(args))
        if res[0] == 0:
            self.running = True
        else:
            raise RuntimeError(
                f"Failed to start Minecraft server instance {self.instance_name}"
            )

    def stop(self):
        with remote(self.node.host) as machine:
            res = machine["apptainer"].run(
                ("instance", "stop", self.instance_name)
            )
        if res[0] == 0:
            self.running = False
        else:
            raise RuntimeError(
                f"Failed to stop Minecraft server instance {self.instance_name}"
            )

    def wait_until_ready(self, timeout_s: float = 180) -> None:
        """Block until the server has finished booting and is ready to accept
        both gameplay connections and RCON commands.

        Polls the RCON listener port (25575) on the server's node. Minecraft
        binds RCON *after* the game port (25565) and after its "Done!" startup
        log line, so a successful return here means rcon() / set_world_spawn()
        will work and the server is fully ticking.

        On timeout, surfaces the server's own output instead of an opaque TCP
        error: a boot failure (a JVM agent that won't load, a bad flag, OOM)
        leaves the reason in the instance log.
        """
        try:
            wait_for_tcp(self.node.host, RCON_PORT, timeout_s=timeout_s)
        except TimeoutError as e:
            # A detected crash gives the clearest message; otherwise the JVM's
            # own stderr (e.g. UnsupportedClassVersionError from the javaagent)
            # is in the instance .out/.err, which raise_if_crashed's log scan
            # may miss if MC never got far enough to write latest.log.
            self.raise_if_crashed()
            raise TimeoutError(
                f"{e} -- server never opened RCON. Recent instance output:\n"
                f"{self._log_tail()}"
            ) from e

    def logs(self) -> str:
        """Best-effort: the server instance's captured stdout+stderr, read from
        the node (``apptainer instance run`` writes these under
        ~/.apptainer/instances/logs/<host>/<user>/<instance>.{out,err}).
        Returns "" if they can't be located."""
        with remote(self.node.host) as machine:
            try:
                home = machine.env["HOME"]
                host = machine["hostname"]().strip()
                user = machine["whoami"]().strip()
            except Exception:
                return ""
            base = (
                f"{home}/.apptainer/instances/logs/{host}/{user}/"
                f"{self.instance_name}"
            )
            out = ""
            for ext in ("out", "err"):
                p = machine.path(f"{base}.{ext}")
                if p.exists():
                    out += f"--- {self.instance_name}.{ext} ---\n{p.read()}\n"
            return out

    def _log_tail(self, n: int = 40) -> str:
        text = self.logs()
        if not text:
            return "(no instance logs found)"
        return "\n".join(text.splitlines()[-n:])

    def rcon(self, *commands: str) -> None:
        """Send one or more commands to the running server via RCON.

        Uses the rcon-cli binary that itzg/minecraft-server bundles by
        execing straight into the running instance, so no extra container
        is launched. The exec runs on the server's node (over remote()), so
        RCON_HOST stays `localhost` -- it's relative to where rcon-cli runs,
        which is the same node as the server. The server must already be
        started and accepting connections (use wait_until_ready() first).
        """
        if not commands:
            return
        with remote(self.node.host) as machine:
            machine["apptainer"].run(
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

    def raise_if_crashed(self, machine=None) -> None:
        """Raise MinecraftServerCrashed if the server's log/crash-reports show
        a crash (a Watchdog forced shutdown, an OOM, or any unhandled error).

        Cheap and idempotent -- meant to be polled by the orchestrator (e.g.
        each iteration of the loop that waits for a workload to finish) so a
        server crash aborts the run promptly instead of letting clients spin
        against a dead server. Reads the server's own log under its data dir
        on the node over remote(); pass an already-open `machine` (as the
        background monitor does) to reuse one SSH connection across polls
        instead of opening one per call.
        """
        if machine is not None:
            self._raise_if_crashed(machine)
        else:
            with remote(self.node.host) as machine:
                self._raise_if_crashed(machine)

    def _raise_if_crashed(self, machine) -> None:
        # A crash-report file is the unambiguous signal: vanilla writes here
        # only when the server actually crashes. Prefer it for the message.
        crash_dir = machine.path(self.data_dir) / "crash-reports"
        reports = sorted(crash_dir // "*.txt") if crash_dir.exists() else []
        if reports:
            detail = reports[-1].read()[:2000]
            raise MinecraftServerCrashed(
                f"Minecraft server '{self.instance_name}' crashed "
                f"(see {reports[-1]}):\n{detail}"
            )
        # Fall back to scanning the console log for crash markers.
        log = machine.path(self.data_dir) / "logs" / "latest.log"
        if log.exists():
            text = log.read()
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
            # Hold a single remote() connection for the monitor's lifetime so
            # we don't open/close an SSH session on every poll.
            with remote(self.node.host) as machine:
                while not stop.wait(interval_s):
                    try:
                        self.raise_if_crashed(machine=machine)
                    except MinecraftServerCrashed as exc:
                        self._crash = exc
                        return
                    except Exception:
                        # Transient remote read error (e.g. an SSH hiccup);
                        # try again on the next tick rather than killing the
                        # monitor thread.
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
