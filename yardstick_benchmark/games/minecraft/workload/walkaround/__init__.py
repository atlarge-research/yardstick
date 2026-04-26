"""WalkAround workload for Minecraft.

One apptainer instance per node, from the Yardstick Mineflayer image.
The image bundles Node + mineflayer + mineflayer-pathfinder; per-workload
.js files are bind-mounted from this Python package's data into the
container, so the image only needs to be republished when npm
dependencies change.

To run across multiple nodes, construct one WalkAround per node (with a
distinct `bot_index` for each so bot usernames don't collide) and fan
out the deploy/start/stop/cleanup methods via util.fan_out.

The published image lives at docker://jdonkervliet/yardstick-mineflayer:1.0;
override via the image_url constructor kwarg if you publish your own.
"""

from datetime import timedelta
from pathlib import Path
from typing import List

from plumbum import local

from yardstick_benchmark.model import Node
from yardstick_benchmark.util import random_string, remote


# Root of the workload tree as it lives on the headnode (this Python
# package). It mirrors the layout that gets bind-mounted into the
# container at /opt/workload/scripts.
WORKLOAD_ROOT = Path(__file__).parent.parent

# Files (relative to WORKLOAD_ROOT) that this workload needs staged onto
# the node before start. Includes the shared lib.js plus the per-workload
# entry/worker scripts. Setting the world spawn happens via
# MinecraftServer.set_world_spawn() (RCON), not via a workload script.
WORKLOAD_FILES = (
    "lib.js",
    "walkaround/main.js",
    "walkaround/worker.js",
)


class WalkAround:
    """Run the WalkAround Mineflayer workload on a single node."""

    DEFAULT_IMAGE_URL = "docker://jdonkervliet/yardstick-mineflayer:1.0"
    INSTANCE_NAME = "yardstick-walkaround"
    CONTAINER_SCRIPTS_ROOT = "/opt/workload/scripts"
    CONTAINER_PWD = f"{CONTAINER_SCRIPTS_ROOT}/walkaround"
    ENTRY_SCRIPT = f"{CONTAINER_SCRIPTS_ROOT}/walkaround/main.js"

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
        image_url: str = DEFAULT_IMAGE_URL,
    ):
        self.node = node
        self.server_host = server_host
        self.duration = duration
        self.box_width = box_width
        self.box_x = box_x
        self.box_z = box_z
        self.bots_join_delay = bots_join_delay
        self.bots_per_node = bots_per_node
        self.bot_index = bot_index
        self.image_url = image_url
        self.wd = f"{node.wd}/walkaround-{random_string(8)}"

    def _env_args(self) -> List[str]:
        return [
            "--env", f"DURATION={int(self.duration.total_seconds())}",
            "--env", f"MC_HOST={self.server_host}",
            "--env", f"BOX_WIDTH={self.box_width}",
            "--env", f"BOX_X={self.box_x}",
            "--env", f"BOX_Z={self.box_z}",
            "--env",
            f"BOTS_JOIN_DELAY={int(self.bots_join_delay.total_seconds())}",
            "--env", f"BOTS_PER_NODE={self.bots_per_node}",
            "--env", f"BOT_INDEX={self.bot_index}",
        ]

    def deploy(self) -> None:
        with remote(self.node.host) as machine:
            for relpath in WORKLOAD_FILES:
                src = WORKLOAD_ROOT / relpath
                dst = f"{self.wd}/{relpath}"
                local.path(src).copy(machine.path(dst))

    def start(self) -> None:
        with remote(self.node.host) as machine:
            args = (
                [
                    "instance", "run",
                    "--no-https",
                    "--compat",
                    "--pwd", self.CONTAINER_PWD,
                    "--bind",
                    f"{self.wd}:{self.CONTAINER_SCRIPTS_ROOT}",
                ]
                + self._env_args()
                + [self.image_url, self.INSTANCE_NAME, self.ENTRY_SCRIPT]
            )
            machine["apptainer"][args]()

    def stop(self) -> None:
        with remote(self.node.host) as machine:
            machine["apptainer"][
                "instance", "stop", self.INSTANCE_NAME
            ].run(retcode=None)

    def cleanup(self) -> None:
        with remote(self.node.host) as machine:
            machine["rm"]["-rf", self.wd](retcode=None)
