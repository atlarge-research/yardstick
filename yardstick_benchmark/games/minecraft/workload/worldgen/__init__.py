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
"""

from datetime import timedelta
from typing import Dict, Optional

from yardstick_benchmark.games.minecraft.server import (
    GAME_PORT,
    RCON_PORT,
    MinecraftServer,
)
from yardstick_benchmark.games.minecraft.workload.base import MineflayerWorkload
from yardstick_benchmark.model import Node
from yardstick_benchmark.monitoring import InfluxDBInfo


class WorldGeneration(MineflayerWorkload):
    """Run the WorldGeneration Mineflayer workload on a single node."""

    NAME = "worldgen"
    ENTRY = "worldgen/main.js"
    FILES = (
        "lib.js",
        "worldgen/main.js",
        "worldgen/worker.js",
    )

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
        server_port: int = GAME_PORT,
        rcon_port: int = RCON_PORT,
        timeout: timedelta = timedelta(minutes=60),
        name: str = "",
        image_url: str = MineflayerWorkload.DEFAULT_IMAGE_URL,
    ):
        """
        Args:
            node: Node to run the workload container on.
            server_host: Hostname/IP of the Minecraft server. Used for both
                the game connection and the RCON connection.
            influxdb_info: Connection info for the InfluxDB v2 instance the
                per-player timing metric is written to (use
                ``InfluxDB.get_info()``).
            rcon_password: RCON password of the target server (use
                ``MinecraftServer.rcon_password``). Teleports and the
                spectator gamemode change are issued over RCON.
            minecraft_version: Minecraft version the bots connect as. Must
                match the server's version and be supported by the image's
                Mineflayer. Defaults to MinecraftServer.DEFAULT_VERSION, so
                the workload and a default-constructed server agree out of
                the box.
            teleports: Number of teleport/load cycles each player completes
                before the workload ends.
            bots_per_node: Number of emulated players to run on this node.
            total_bots: Total number of players across all nodes, used to
                spread players over distinct angular sectors. Defaults to
                ``bots_per_node`` (single-node runs).
            start_distance: Distance (blocks) from spawn of each player's
                first teleport target.
            step_distance: Additional distance (blocks) from spawn added on
                each subsequent teleport, so every target is fresh terrain.
            teleport_y: Y coordinate to teleport players to (high enough to
                sit above generated terrain; spectator mode means no fall
                damage).
            chunk_load_timeout: Per-teleport safety cap on how long to wait
                for the target chunk to load before giving up on that one and
                moving on.
            bots_join_delay: Delay between successive players joining on this
                node.
            bot_index: Index of this node's workload among all nodes; also
                used to namespace bot usernames and compute global player
                indices.
            server_port: Port the Minecraft server listens on.
            rcon_port: RCON port of the Minecraft server.
            timeout: Overall safety timeout. The workload normally exits as
                soon as all players finish their teleports; this just bounds
                a stuck run.
            name: Apptainer instance name for detached runs.
            image_url: Container image to run.
        """
        super().__init__(node, name=name, image_url=image_url, timeout=timeout)
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
        self.server_port = server_port
        self.rcon_port = rcon_port

    def _env(self) -> Dict[str, str]:
        return {
            # Quiet Node's punycode deprecation warning so it doesn't flood
            # the container's stderr and bury the workload's own output.
            "NODE_OPTIONS": "--no-deprecation",
            "MC_HOST": self.server_host,
            "MC_PORT": str(self.server_port),
            "MC_VERSION": self.minecraft_version,
            "RCON_HOST": self.server_host,
            "RCON_PORT": str(self.rcon_port),
            "RCON_PASSWORD": self.rcon_password,
            "TELEPORTS": str(self.teleports),
            "BOTS_PER_NODE": str(self.bots_per_node),
            "TOTAL_BOTS": str(self.total_bots),
            "START_DISTANCE": str(self.start_distance),
            "STEP_DISTANCE": str(self.step_distance),
            "TELEPORT_Y": str(self.teleport_y),
            "CHUNK_LOAD_TIMEOUT": str(int(self.chunk_load_timeout.total_seconds())),
            "BOTS_JOIN_DELAY": str(int(self.bots_join_delay.total_seconds())),
            "BOT_INDEX": str(self.bot_index),
            "TIMEOUT": str(int(self.timeout.total_seconds())),
            "INFLUXDB_URL": self.influxdb_info.urls[0],
            "INFLUXDB_TOKEN": self.influxdb_info.token,
            "INFLUXDB_ORG": self.influxdb_info.organization,
            "INFLUXDB_BUCKET": self.influxdb_info.bucket,
        }
