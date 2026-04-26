"""WalkAround workload for Minecraft.

Spins up one apptainer instance per node from the Yardstick Mineflayer
image (Node + mineflayer + mineflayer-pathfinder + rcon-client). Workload
.js files are bind-mounted from this Python package's data into the
container, so the image only needs to be republished when npm
dependencies change.

The published image lives at docker://jdonkervliet/yardstick-mineflayer:1.0;
override via the image_url constructor kwarg if you publish your own.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
from pathlib import Path
from typing import List

from plumbum import SshMachine, local

from yardstick_benchmark.model import Node
from yardstick_benchmark.util import is_localhost, random_string


# Root of the workload tree as it lives on the headnode (this Python
# package). It mirrors the layout that gets bind-mounted into the
# container at /opt/workload/scripts.
WORKLOAD_ROOT = Path(__file__).parent.parent

# Files (relative to WORKLOAD_ROOT) that this workload needs staged onto
# each remote node before start. Includes the shared lib.js plus the
# per-workload entry/worker/setup scripts.
WORKLOAD_FILES = (
    "lib.js",
    "walkaround/main.js",
    "walkaround/worker.js",
    "walkaround/set_spawn.js",
)


def _remote(host: str):
    return local if is_localhost(host) else SshMachine(host)


class WalkAround:
    """Run the WalkAround Mineflayer workload across one or more nodes."""

    DEFAULT_IMAGE_URL = "docker://jdonkervliet/yardstick-mineflayer:1.0"
    INSTANCE_NAME = "yardstick-walkaround"
    CONTAINER_SCRIPTS_ROOT = "/opt/workload/scripts"
    CONTAINER_PWD = f"{CONTAINER_SCRIPTS_ROOT}/walkaround"
    ENTRY_SCRIPT = f"{CONTAINER_SCRIPTS_ROOT}/walkaround/main.js"
    SET_SPAWN_SCRIPT = f"{CONTAINER_SCRIPTS_ROOT}/walkaround/set_spawn.js"

    def __init__(
        self,
        nodes: List[Node],
        server_host: str,
        duration: timedelta = timedelta(seconds=60),
        spawn_x: int = 0,
        spawn_y: int = 0,
        box_width: int = 32,
        box_x: int = -16,
        box_z: int = -16,
        bots_join_delay: timedelta = timedelta(seconds=5),
        bots_per_node: int = 1,
        set_world_spawn: bool = True,
        image_url: str = DEFAULT_IMAGE_URL,
    ):
        self.nodes = list(nodes)
        self.server_host = server_host
        self.duration = duration
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y
        self.box_width = box_width
        self.box_x = box_x
        self.box_z = box_z
        self.bots_join_delay = bots_join_delay
        self.bots_per_node = bots_per_node
        self.set_world_spawn = set_world_spawn
        self.image_url = image_url
        self.wds = {
            node: f"{node.wd}/walkaround-{random_string(8)}" for node in self.nodes
        }

    def _env_args(self, bot_index: int) -> List[str]:
        return [
            "--env", f"DURATION={int(self.duration.total_seconds())}",
            "--env", f"MC_HOST={self.server_host}",
            "--env", f"SPAWN_X={self.spawn_x}",
            "--env", f"SPAWN_Y={self.spawn_y}",
            "--env", f"BOX_WIDTH={self.box_width}",
            "--env", f"BOX_X={self.box_x}",
            "--env", f"BOX_Z={self.box_z}",
            "--env",
            f"BOTS_JOIN_DELAY={int(self.bots_join_delay.total_seconds())}",
            "--env", f"BOTS_PER_NODE={self.bots_per_node}",
            "--env", f"BOT_INDEX={bot_index}",
        ]

    def _per_node(self, fn) -> None:
        with ThreadPoolExecutor(max_workers=max(1, len(self.nodes))) as pool:
            futs = [pool.submit(fn, n, i) for i, n in enumerate(self.nodes)]
            for fut in as_completed(futs):
                fut.result()

    def deploy(self) -> None:
        def _stage(node: Node, _i: int) -> None:
            machine = _remote(node.host)
            try:
                wd = self.wds[node]
                for relpath in WORKLOAD_FILES:
                    src = WORKLOAD_ROOT / relpath
                    dst = f"{wd}/{relpath}"
                    local.path(src).copy(machine.path(dst))
            finally:
                if isinstance(machine, SshMachine):
                    machine.close()

        self._per_node(_stage)

    def start(self) -> None:
        if self.set_world_spawn:
            self._set_world_spawn()

        def _run(node: Node, bot_index: int) -> None:
            machine = _remote(node.host)
            try:
                args = (
                    [
                        "instance", "run",
                        "--no-https",
                        "--compat",
                        "--pwd", self.CONTAINER_PWD,
                        "--bind",
                        f"{self.wds[node]}:{self.CONTAINER_SCRIPTS_ROOT}",
                    ]
                    + self._env_args(bot_index)
                    + [self.image_url, self.INSTANCE_NAME, self.ENTRY_SCRIPT]
                )
                machine["apptainer"][args]()
            finally:
                if isinstance(machine, SshMachine):
                    machine.close()

        self._per_node(_run)

    def _set_world_spawn(self) -> None:
        # Run set_spawn.js once, on the first node, against the MC server's
        # RCON port. Requires the MC server to have RCON enabled with the
        # password 'password' (or override RCON_PASSWORD via env).
        node = self.nodes[0]
        machine = _remote(node.host)
        try:
            args = (
                [
                    "exec",
                    "--no-https",
                    "--compat",
                    "--pwd", self.CONTAINER_PWD,
                    "--bind",
                    f"{self.wds[node]}:{self.CONTAINER_SCRIPTS_ROOT}",
                ]
                + self._env_args(0)
                + [self.image_url, "node", self.SET_SPAWN_SCRIPT]
            )
            machine["apptainer"][args]()
        finally:
            if isinstance(machine, SshMachine):
                machine.close()

    def stop(self) -> None:
        def _stop(node: Node, _i: int) -> None:
            machine = _remote(node.host)
            try:
                machine["apptainer"][
                    "instance", "stop", self.INSTANCE_NAME
                ].run(retcode=None)
            finally:
                if isinstance(machine, SshMachine):
                    machine.close()

        self._per_node(_stop)

    def cleanup(self) -> None:
        def _rm(node: Node, _i: int) -> None:
            machine = _remote(node.host)
            try:
                machine["rm"]["-rf", self.wds[node]](retcode=None)
            finally:
                if isinstance(machine, SshMachine):
                    machine.close()

        self._per_node(_rm)
