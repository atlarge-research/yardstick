"""Shared base for Mineflayer-based Minecraft workloads.

Every workload here is one apptainer container per node, run from the
Yardstick Mineflayer image. The image bundles Node plus mineflayer and its
supporting libraries; the per-workload ``.js`` files are bind-mounted in from
this Python package, so the image only needs republishing when the npm
dependencies change, not when a workload does.

A subclass supplies three things -- the files it needs staged, its entry
script, and its container environment -- and inherits the whole lifecycle:

    class MyWorkload(MineflayerWorkload):
        NAME = "myworkload"
        ENTRY = "myworkload/main.js"
        FILES = ("lib.js", "myworkload/main.js", "myworkload/worker.js")

        def _env(self):
            return {"MC_HOST": self.server_host, ...}

To run a workload across several nodes, construct one per node with a
distinct ``bot_index`` (and the same ``total_bots``) so usernames don't
collide, then fan the lifecycle methods out with
:func:`yardstick_benchmark.util.fan_out`.
"""

import sys
import threading
import time
from datetime import timedelta
from pathlib import Path
from typing import IO, Callable, Dict, List, Optional

from yardstick_benchmark.model import Node
from yardstick_benchmark.util import random_string, remote, stage


# Root of the workload tree as it lives on the headnode (this Python
# package). It mirrors the layout that gets bind-mounted into the container
# at CONTAINER_SCRIPTS_ROOT.
WORKLOAD_ROOT = Path(__file__).parent


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


class MineflayerWorkload:
    """Run a Mineflayer workload container on a single node.

    The normal way to use a workload is ``deploy()``, ``run()``, ``cleanup()``:
    :meth:`run` blocks until the workload finishes and streams its output, so
    the caller learns when it actually ended rather than sleeping for a
    guessed duration. :meth:`start` / :meth:`stop` are the detached
    alternative, for when you want the bots running in the background while
    the calling code does something else.
    """

    DEFAULT_IMAGE_URL = "docker://jdonkervliet/yardstick-mineflayer:1.0"
    CONTAINER_SCRIPTS_ROOT = "/opt/workload/scripts"

    #: Short workload name, used for the default instance name and wd.
    NAME = "workload"
    #: Entry script, relative to the workload package root.
    ENTRY = ""
    #: Files to stage onto the node, relative to the workload package root.
    FILES: tuple = ()

    def __init__(
        self,
        node: Node,
        name: str = "",
        image_url: str = DEFAULT_IMAGE_URL,
        timeout: timedelta = timedelta(minutes=60),
    ):
        """
        Args:
            node: Node to run the workload container on.
            name: Apptainer instance name for detached runs. Defaults to
                ``yardstick-<NAME>``; override it to run more than one
                workload of the same kind on a node.
            image_url: Container image to run.
            timeout: Safety cap on :meth:`run`. A workload normally exits on
                its own well before this; it only bounds a stuck run.
        """
        self.node = node
        self.instance_name = name or f"yardstick-{self.NAME}"
        self.image_url = image_url
        self.timeout = timeout
        self.wd = f"{node.wd}/{self.NAME}-{random_string(8)}"

    @property
    def entry_script(self) -> str:
        """Absolute path of the entry script inside the container."""
        return f"{self.CONTAINER_SCRIPTS_ROOT}/{self.ENTRY}"

    def _env(self) -> Dict[str, str]:
        """The container environment for this workload. Subclasses override."""
        raise NotImplementedError

    def _env_args(self) -> List[str]:
        args: List[str] = []
        for key, value in self._env().items():
            args += ["--env", f"{key}={value}"]
        return args

    def _container_args(self) -> List[str]:
        return [
            "--no-https",
            "--compat",
            "--bind",
            f"{self.wd}:{self.CONTAINER_SCRIPTS_ROOT}",
        ] + self._env_args()

    def deploy(self) -> None:
        """Stage this workload's scripts onto the node."""
        with remote(self.node.host, self.node.user) as machine:
            for relpath in self.FILES:
                stage(machine, WORKLOAD_ROOT / relpath, f"{self.wd}/{relpath}")

    def run(self, health_check: Optional[Callable[[], None]] = None) -> None:
        """Run the workload in the foreground, blocking until it exits.

        Uses ``apptainer run`` rather than ``instance run`` -- the right
        primitive for a job you wait on: the container is gone the moment the
        entry script exits, leaving no instance to stop. The container's
        stdout/stderr are streamed to this process's own. Call :meth:`deploy`
        first and :meth:`cleanup` after.

        Args:
            health_check: optional zero-arg callable polled while the workload
                runs; if it raises (e.g. MinecraftServer.assert_healthy), the
                container is killed and the exception propagates, so a server
                crash aborts the run promptly instead of leaving the bots
                spinning against a dead server.

        Raises:
            RuntimeError: if the workload exits non-zero.
            TimeoutError: if it doesn't exit within ``timeout`` plus a margin.
        """
        # Note: `apptainer instance run` doesn't accept --pwd / --cwd (only
        # the non-instance `run` and `exec` do). The workload .js files use
        # __dirname-relative paths for require() and Worker spawning, so the
        # CWD inside the container doesn't matter either way.
        args = ["run"] + self._container_args() + [self.image_url, self.entry_script]
        grace_s = self.timeout.total_seconds() + 60
        deadline = time.monotonic() + grace_s
        with remote(self.node.host, self.node.user) as machine:
            proc = machine["apptainer"][args].popen()
            # Drain stdout/stderr in background threads: surfaces the
            # workload's output and avoids a full pipe buffer blocking a
            # chatty run.
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
                            f"{self.NAME} workload did not finish within {grace_s:.0f}s"
                        )
                    time.sleep(2)
                if proc.returncode != 0:
                    raise RuntimeError(
                        f"{self.NAME} workload exited with code {proc.returncode}"
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

    def start(self) -> None:
        """Start the workload detached, as a background apptainer instance.

        Use this only when the calling code needs to do something while the
        bots run; :meth:`run` is the better default because it reports when
        the workload actually finished. Pair with :meth:`stop` and read the
        container's output with :meth:`logs`.
        """
        args = (
            ["instance", "run"]
            + self._container_args()
            + [self.image_url, self.instance_name, self.entry_script]
        )
        with remote(self.node.host, self.node.user) as machine:
            machine["apptainer"][args]()

    def logs(self) -> str:
        """Return a detached run's captured stdout+stderr (best effort).

        ``apptainer instance run`` writes instance logs under
        ``~/.apptainer/instances/logs/<host>/<user>/<instance>.{out,err}`` on
        the node that runs it. Returns "" if they can't be located. Only
        meaningful after :meth:`start`; :meth:`run` streams its output live.
        """
        with remote(self.node.host, self.node.user) as machine:
            try:
                home = machine.env["HOME"]
                host = machine["hostname"]().strip()
                user = machine["whoami"]().strip()
            except Exception:
                return ""
            base = (
                f"{home}/.apptainer/instances/logs/{host}/{user}/{self.instance_name}"
            )
            out = ""
            for ext in ("out", "err"):
                p = machine.path(f"{base}.{ext}")
                if p.exists():
                    out += f"--- {self.instance_name}.{ext} ---\n{p.read()}\n"
            return out

    def stop(self) -> None:
        """Stop a detached run. Safe to call if it never started."""
        with remote(self.node.host, self.node.user) as machine:
            machine["apptainer"]["instance", "stop", self.instance_name].run(
                retcode=None
            )

    def cleanup(self) -> None:
        """Remove the workload's staged files from the node."""
        with remote(self.node.host, self.node.user) as machine:
            machine["rm"]["-rf", self.wd](retcode=None)
