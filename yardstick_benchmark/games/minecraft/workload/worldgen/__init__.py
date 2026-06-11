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

import sys
import threading
import time
from datetime import timedelta
from pathlib import Path
from typing import IO, Callable, List, Optional

from yardstick_benchmark.games.minecraft.server import (
    GAME_PORT,
    RCON_PORT,
    MinecraftServer,
)
from yardstick_benchmark.model import Node
from yardstick_benchmark.monitoring import InfluxDBInfo
from yardstick_benchmark.util import random_string, remote, upload


def _pump(src: Optional[IO], dst: IO) -> None:
    """Stream lines from a subprocess pipe `src` to `dst` (e.g. sys.stdout),
    decoding bytes if needed. Used to forward a foreground workload's output
    so it's visible for debugging instead of being buffered and discarded."""
    if src is None:
        return
    try:
        for line in iter(src.readline, b""):
            if not line:
                break
            if isinstance(line, (bytes, bytearray)):
                line = line.decode(errors="replace")
            dst.write(line)
            dst.flush()
    except Exception:
        pass


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
        chunk_load_timeout: timedelta = timedelta(seconds=30),
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
                # upload() scp's the file to a remote node; scp won't create
                # missing parent dirs (e.g. the worldgen/ subdir), so make the
                # destination's directory first.
                machine["mkdir"]["-p", machine.path(dst).dirname]()
                upload(machine, src, dst)

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

    def run(self, health_check: Optional[Callable[[], None]] = None) -> None:
        """Run the workload in the foreground, blocking until every player has
        finished its teleports (the entry script then exits) or the safety
        ``timeout`` elapses.

        Uses ``apptainer run`` (not ``instance run``) -- the right primitive
        for a job you wait to exit: the container is gone the moment the entry
        script exits, leaving no instance to stop. When the node is remote the
        container runs there over SSH (the headnode runs no container), and
        remote() holds the SSH session open with keepalives. The container's
        stdout/stderr are streamed to this process's stdout/stderr. deploy()
        first; cleanup() after.

        Args:
            health_check: optional zero-arg callable polled while the workload
                runs; if it raises (e.g. MinecraftServer.assert_healthy), the
                container is killed and the exception propagates, so a server
                crash aborts the run promptly.

        Raises:
            RuntimeError: if the workload exits non-zero.
            TimeoutError: if it doesn't exit within ``timeout`` plus a margin.
        """
        with remote(self.node.host) as machine:
            args = (
                [
                    "run",
                    "--no-https",
                    "--compat",
                    "--bind",
                    f"{self.wd}:{self.CONTAINER_SCRIPTS_ROOT}",
                ]
                + self._env_args()
                + [self.image_url, self.ENTRY_SCRIPT]
            )
            grace_s = self.timeout.total_seconds() + 60
            deadline = time.monotonic() + grace_s
            proc = machine["apptainer"][args].popen()
            # Drain stdout/stderr in background threads: surfaces the workload's
            # output and avoids a full pipe buffer blocking a chatty run.
            pumps = [
                threading.Thread(
                    target=_pump, args=(proc.stdout, sys.stdout), daemon=True
                ),
                threading.Thread(
                    target=_pump, args=(proc.stderr, sys.stderr), daemon=True
                ),
            ]
            for t in pumps:
                t.start()
            try:
                while proc.poll() is None:
                    if health_check is not None:
                        health_check()
                    if time.monotonic() > deadline:
                        raise TimeoutError(
                            f"worldgen workload did not finish within "
                            f"{grace_s:.0f}s"
                        )
                    time.sleep(2)
                if proc.returncode != 0:
                    raise RuntimeError(
                        f"worldgen workload exited with code {proc.returncode}"
                    )
            finally:
                # Kill the foreground container on timeout / crash / interrupt
                # so nothing is left running.
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=15)
                    except Exception:
                        proc.kill()
                for t in pumps:
                    t.join(timeout=5)

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
