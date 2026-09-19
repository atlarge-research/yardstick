"""WalkAround workload for Minecraft.

A steady-state player workload: a number of emulated players join the server
and walk around a fixed box near spawn for `duration`, then disconnect and the
entry script exits. Useful as background load while something else (Telegraf,
Jolokia) measures the server.

Setting the world spawn happens via MinecraftServer.set_world_spawn() over
RCON, not via a workload script.
"""

from datetime import timedelta
from typing import Dict, Optional

from yardstick_benchmark.games.minecraft.server import GAME_PORT, MinecraftServer
from yardstick_benchmark.games.minecraft.workload.base import MineflayerWorkload
from yardstick_benchmark.model import Node


class WalkAround(MineflayerWorkload):
    """Run the WalkAround Mineflayer workload on a single node."""

    NAME = "walkaround"
    ENTRY = "walkaround/main.js"
    FILES = (
        "lib.js",
        "walkaround/main.js",
        "walkaround/worker.js",
    )

    def __init__(
        self,
        node: Node,
        server_host: str,
        duration: timedelta = timedelta(seconds=60),
        box_width: int = 32,
        box_x: int = -16,
        box_z: int = -16,
        bots_join_delay: timedelta = timedelta(seconds=5),
        bots_per_node: int = 1,
        bot_index: int = 0,
        server_port: int = GAME_PORT,
        minecraft_version: str = MinecraftServer.DEFAULT_VERSION,
        name: str = "",
        image_url: str = MineflayerWorkload.DEFAULT_IMAGE_URL,
        timeout: Optional[timedelta] = None,
    ):
        """
        Args:
            node: Node to run the workload container on.
            server_host: Hostname/IP of the Minecraft server.
            duration: How long the players walk around before disconnecting.
            box_width: Side length, in blocks, of the box players walk in.
            box_x: X coordinate of the box's corner.
            box_z: Z coordinate of the box's corner.
            bots_join_delay: Delay between successive players joining.
            bots_per_node: Number of emulated players to run on this node.
            bot_index: Index of this node's workload among all nodes; used to
                namespace bot usernames so they don't collide across nodes.
            server_port: Port the Minecraft server listens on.
            minecraft_version: Minecraft version the bots connect as. Must
                match the server's version and be supported by the image's
                Mineflayer.
            name: Apptainer instance name for detached runs.
            image_url: Container image to run.
            timeout: Safety cap on run(). Defaults to `duration` plus the time
                it takes every player to join, plus a margin -- so a wedged
                run is caught rather than hanging for the base class's
                hour-long default.
        """
        if timeout is None:
            join_s = bots_join_delay.total_seconds() * max(0, bots_per_node - 1)
            timeout = timedelta(
                seconds=duration.total_seconds() + join_s + 120,
            )
        super().__init__(node, name=name, image_url=image_url, timeout=timeout)
        self.server_host = server_host
        self.server_port = server_port
        self.minecraft_version = minecraft_version
        self.duration = duration
        self.box_width = box_width
        self.box_x = box_x
        self.box_z = box_z
        self.bots_join_delay = bots_join_delay
        self.bots_per_node = bots_per_node
        self.bot_index = bot_index

    def _env(self) -> Dict[str, str]:
        return {
            "DURATION": str(int(self.duration.total_seconds())),
            "MC_HOST": self.server_host,
            "MC_PORT": str(self.server_port),
            "MC_VERSION": self.minecraft_version,
            "BOX_WIDTH": str(self.box_width),
            "BOX_X": str(self.box_x),
            "BOX_Z": str(self.box_z),
            "BOTS_JOIN_DELAY": str(int(self.bots_join_delay.total_seconds())),
            "BOTS_PER_NODE": str(self.bots_per_node),
            "BOT_INDEX": str(self.bot_index),
        }
