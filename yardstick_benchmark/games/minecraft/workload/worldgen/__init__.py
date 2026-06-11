"""WorldGeneration workload for Minecraft.

A world-generation stress workload: each emulated player joins, is put into
spectator mode, and then repeatedly teleports to a fresh location far from
spawn and far from the other players, waits for that area's chunks to load
in (which forces the server to generate them), and immediately teleports
again. The run ends once *every* player has completed `teleports` (default
32) teleport/load cycles, and the time each player took is committed as a
metric to InfluxDB (the `minecraft_worldgen` measurement).

Teleporting and gamemode changes are issued over RCON (the bundled
`rcon-client` npm dep) so they run as the server console -- no op needed and
no client-side flying. Spectator mode keeps a player loading chunks around
itself while immune to fall damage/suffocation, so the teleport sequence is
never interrupted by death/respawn.

Players are spread over distinct angular sectors and march outward by
`step_distance` blocks per teleport, so every target is fresh, ungenerated
terrain, away from spawn, and away from the other players.

Like WalkAround, this is one apptainer instance per node from the Yardstick
Mineflayer image; the per-workload .js files are bind-mounted from this
package. To run across multiple nodes, construct one WorldGeneration per node
with a distinct `bot_index` (and the same `total_bots`) so usernames don't
collide and the angular spread covers every player.

The published image lives at docker://jdonkervliet/yardstick-mineflayer:1.0;
override via the image_url constructor kwarg if you publish your own.
"""

import json
import time
from datetime import timedelta
from pathlib import Path
from typing import Callable, List, Optional

from plumbum import local

from yardstick_benchmark.games.minecraft.server import (
    GAME_PORT,
    RCON_PORT,
    MinecraftServer,
)
from yardstick_benchmark.model import Node
from yardstick_benchmark.monitoring import InfluxDBInfo
from yardstick_benchmark.util import random_string, remote


# Root of the workload tree as it lives on the headnode (this Python
# package). It mirrors the layout that gets bind-mounted into the
# container at /opt/workload/scripts.
WORKLOAD_ROOT = Path(__file__).parent.parent

# Files (relative to WORKLOAD_ROOT) that this workload needs staged onto
# the node before start: the shared lib.js plus this workload's entry and
# worker scripts.
WORKLOAD_FILES = (
    "lib.js",
    "worldgen/main.js",
    "worldgen/worker.js",
)


class WorldGeneration:
    """Run the WorldGeneration Mineflayer workload on a single node.

    Args:
        node: Node to run the workload (apptainer instance) on.
        server_host: Hostname/IP of the Minecraft server. Used for both the
            game connection and the RCON connection.
        influxdb_info: Connection info for the InfluxDB v2 instance the
            per-player timing metric is written to (use
            ``InfluxDB.get_info()``).
        rcon_password: RCON password of the target server (use
            ``MinecraftServer.rcon_password``). Teleports and the spectator
            gamemode change are issued over RCON.
        minecraft_version: Minecraft version the bots connect as. Must match
            the server's version and be supported by the image's Mineflayer.
            Defaults to MinecraftServer.DEFAULT_VERSION, so the workload and
            a default-constructed server agree out of the box.
        teleports: Number of teleport/load cycles each player completes
            before the workload ends. Defaults to 32.
        bots_per_node: Number of emulated players to run on this node.
        total_bots: Total number of players across all nodes, used to spread
            players over distinct angular sectors. Defaults to
            ``bots_per_node`` (single-node runs).
        start_distance: Distance (blocks) from spawn of each player's first
            teleport target.
        step_distance: Additional distance (blocks) from spawn added on each
            subsequent teleport, so every target is fresh terrain.
        teleport_y: Y coordinate to teleport players to (high enough to sit
            above generated terrain; spectator mode means no fall damage).
        chunk_load_timeout: Per-teleport safety cap on how long to wait for
            the target chunk to load before giving up on that one and moving
            on.
        bots_join_delay: Delay between successive players joining on this
            node.
        bot_index: Index of this node's workload among all nodes; also used
            to namespace bot usernames and compute global player indices.
        timeout: Overall safety timeout. The workload normally exits as soon
            as all players finish their teleports; this just bounds a stuck
            run.
        image_url: Container image to run.
    """

    DEFAULT_IMAGE_URL = "docker://jdonkervliet/yardstick-mineflayer:1.0"
    INSTANCE_NAME = "yardstick-worldgen"
    CONTAINER_SCRIPTS_ROOT = "/opt/workload/scripts"
    ENTRY_SCRIPT = f"{CONTAINER_SCRIPTS_ROOT}/worldgen/main.js"
    # Completion sentinel the entry script drops in its working dir (== the
    # bind-mounted scripts root) when the run finishes; poll_status()/wait()
    # read it. Kept in sync with main.js's STATUS_FILE.
    STATUS_FILE = "worldgen.status"

    def __init__(
        self,
        node: Node,
        server_host: str,
        influxdb_info: InfluxDBInfo,
        rcon_password: str,
        minecraft_version: str = MinecraftServer.DEFAULT_VERSION,
        teleports: int = 32,
        bots_per_node: int = 1,
        total_bots: Optional[int] = None,
        start_distance: int = 2000,
        step_distance: int = 1500,
        teleport_y: int = 200,
        chunk_load_timeout: timedelta = timedelta(seconds=60),
        bots_join_delay: timedelta = timedelta(seconds=5),
        bot_index: int = 0,
        timeout: timedelta = timedelta(minutes=60),
        image_url: str = DEFAULT_IMAGE_URL,
    ):
        self.node = node
        self.server_host = server_host
        self.influxdb_info = influxdb_info
        self.rcon_password = rcon_password
        self.minecraft_version = minecraft_version
        self.teleports = teleports
        self.bots_per_node = bots_per_node
        self.total_bots = total_bots if total_bots is not None else bots_per_node
        self.start_distance = start_distance
        self.step_distance = step_distance
        self.teleport_y = teleport_y
        self.chunk_load_timeout = chunk_load_timeout
        self.bots_join_delay = bots_join_delay
        self.bot_index = bot_index
        self.timeout = timeout
        self.image_url = image_url
        self.wd = f"{node.wd}/worldgen-{random_string(8)}"

    def _env_args(self) -> List[str]:
        return [
            # Quiet Node's punycode deprecation warning so it doesn't flood
            # the instance's stderr and bury the workload's own logs().
            "--env", "NODE_OPTIONS=--no-deprecation",
            "--env", f"MC_HOST={self.server_host}",
            "--env", f"MC_PORT={GAME_PORT}",
            "--env", f"MC_VERSION={self.minecraft_version}",
            "--env", f"RCON_HOST={self.server_host}",
            "--env", f"RCON_PORT={RCON_PORT}",
            "--env", f"RCON_PASSWORD={self.rcon_password}",
            "--env", f"TELEPORTS={self.teleports}",
            "--env", f"BOTS_PER_NODE={self.bots_per_node}",
            "--env", f"TOTAL_BOTS={self.total_bots}",
            "--env", f"START_DISTANCE={self.start_distance}",
            "--env", f"STEP_DISTANCE={self.step_distance}",
            "--env", f"TELEPORT_Y={self.teleport_y}",
            "--env",
            f"CHUNK_LOAD_TIMEOUT={int(self.chunk_load_timeout.total_seconds())}",
            "--env",
            f"BOTS_JOIN_DELAY={int(self.bots_join_delay.total_seconds())}",
            "--env", f"BOT_INDEX={self.bot_index}",
            "--env", f"TIMEOUT={int(self.timeout.total_seconds())}",
            "--env", f"INFLUXDB_URL={self.influxdb_info.urls[0]}",
            "--env", f"INFLUXDB_TOKEN={self.influxdb_info.token}",
            "--env", f"INFLUXDB_ORG={self.influxdb_info.organization}",
            "--env", f"INFLUXDB_BUCKET={self.influxdb_info.bucket}",
        ]

    def deploy(self) -> None:
        with remote(self.node.host) as machine:
            for relpath in WORKLOAD_FILES:
                src = WORKLOAD_ROOT / relpath
                dst = f"{self.wd}/{relpath}"
                local.path(src).copy(machine.path(dst))

    def start(self) -> None:
        with remote(self.node.host) as machine:
            # See WalkAround.start: `apptainer instance run` doesn't accept
            # --pwd/--cwd, and the .js files use __dirname-relative paths,
            # so CWD inside the container doesn't matter.
            args = (
                [
                    "instance", "run",
                    "--no-https",
                    "--compat",
                    "--bind",
                    f"{self.wd}:{self.CONTAINER_SCRIPTS_ROOT}",
                ]
                + self._env_args()
                + [self.image_url, self.INSTANCE_NAME, self.ENTRY_SCRIPT]
            )
            machine["apptainer"][args]()

    def poll_status(self) -> Optional[dict]:
        """Return the workload's completion status as a dict, or None if it
        hasn't finished yet.

        The entry script (start()ed as a detached instance) drops a status
        sentinel in its working dir when the run finishes/aborts; this reads it
        over remote(), so it works whether the workload runs on this host or
        another. The dict carries at least ``status`` ('complete'/'timeout'/
        'error') plus ``players``/``players_done``.
        """
        with remote(self.node.host) as machine:
            status_path = machine.path(f"{self.wd}/{self.STATUS_FILE}")
            if not status_path.exists():
                return None
            try:
                return json.loads(status_path.read())
            except (ValueError, OSError):
                return {"status": "unknown"}

    def wait(
        self,
        health_check: Optional[Callable[[], None]] = None,
        poll_s: float = 5.0,
        timeout: Optional[timedelta] = None,
    ) -> dict:
        """Block (on the headnode) until the started workload finishes, then
        return its status dict.

        This is the detached-instance completion mechanism: deploy() and
        start() the workload, then wait() for it. Nothing runs in the
        foreground -- the workload is an `apptainer instance run` on its node
        and this only polls a sentinel over remote()/SSH, so it works when the
        headnode itself can't run containers.

        Args:
            health_check: optional zero-arg callable invoked each poll; if it
                raises (e.g. MinecraftServer.raise_if_crashed), that exception
                propagates out of wait() so a dependency failure aborts the
                run promptly. The caller still stop()s/cleanup()s the workload
                in a finally.
            poll_s: seconds between polls.
            timeout: max wall-clock to wait; defaults to the workload's own
                safety ``timeout`` plus a margin. Raises TimeoutError if
                exceeded.
        """
        grace_s = (timeout or self.timeout).total_seconds() + 60
        deadline = time.monotonic() + grace_s
        with remote(self.node.host) as machine:
            status_path = machine.path(f"{self.wd}/{self.STATUS_FILE}")
            while True:
                if health_check is not None:
                    health_check()
                if status_path.exists():
                    try:
                        return json.loads(status_path.read())
                    except (ValueError, OSError):
                        return {"status": "unknown"}
                if time.monotonic() > deadline:
                    raise TimeoutError(
                        f"worldgen workload did not finish within {grace_s:.0f}s"
                    )
                time.sleep(poll_s)

    def logs(self) -> str:
        """Return the workload instance's captured stdout+stderr (best effort).

        `apptainer instance run` writes instance logs under
        ~/.apptainer/instances/logs/<host>/<user>/<instance>.{out,err} on the
        node that runs it; fetch them over remote() for debugging (the
        detached-model replacement for the old foreground stdout streaming).
        Returns "" if they can't be located.
        """
        with remote(self.node.host) as machine:
            try:
                home = machine.env["HOME"]
                host = machine["hostname"]().strip()
                user = machine["whoami"]().strip()
            except Exception:
                return ""
            base = (
                f"{home}/.apptainer/instances/logs/{host}/{user}/"
                f"{self.INSTANCE_NAME}"
            )
            out = ""
            for ext in ("out", "err"):
                p = machine.path(f"{base}.{ext}")
                if p.exists():
                    out += f"--- {self.INSTANCE_NAME}.{ext} ---\n{p.read()}\n"
            return out

    def stop(self) -> None:
        with remote(self.node.host) as machine:
            machine["apptainer"][
                "instance", "stop", self.INSTANCE_NAME
            ].run(retcode=None)

    def cleanup(self) -> None:
        with remote(self.node.host) as machine:
            machine["rm"]["-rf", self.wd](retcode=None)


class WorldGeneration1User(WorldGeneration):
    """WorldGeneration with a single emulated player."""

    INSTANCE_NAME = "yardstick-worldgen-1user"

    def __init__(self, node: Node, server_host: str, influxdb_info: InfluxDBInfo,
                 rcon_password: str, **kwargs):
        kwargs["bots_per_node"] = 1
        super().__init__(node, server_host, influxdb_info, rcon_password, **kwargs)


class WorldGeneration8Users(WorldGeneration):
    """WorldGeneration with eight emulated players."""

    INSTANCE_NAME = "yardstick-worldgen-8users"

    def __init__(self, node: Node, server_host: str, influxdb_info: InfluxDBInfo,
                 rcon_password: str, **kwargs):
        kwargs["bots_per_node"] = 8
        super().__init__(node, server_host, influxdb_info, rcon_password, **kwargs)
