import logging
import threading
from pathlib import Path
from typing import List, Sequence

from plumbum import local

from yardstick_benchmark.model import Node
from yardstick_benchmark.util import fan_out, is_localhost, remote


logger = logging.getLogger(__name__)


#: rsync filter patterns for the files worth keeping from a node: the
#: Minecraft console log and its rotations, crash reports (``*.txt``), the
#: ``server.properties`` the server actually ran with, the rendered Telegraf
#: config, and the apptainer instance logs staged in by
#: :func:`_stage_instance_logs` (``*.out`` / ``*.err``).
#:
#: ``*/`` lets rsync descend into every directory; combined with ``-m`` the
#: ones that end up empty are dropped again, so the world and the metrics
#: database's storage cost a directory scan and nothing else.
ARTIFACT_INCLUDES: tuple = (
    "*/",
    "*.log",
    "*.log.gz",
    "*.txt",
    "*.properties",
    "*.conf",
    "*.out",
    "*.err",
)

#: Directory inside a node's working directory that the node's apptainer
#: instance logs are copied into, so one rsync collects them along with
#: everything else.
INSTANCE_LOG_DIR = "apptainer-instance-logs"


def clean(nodes: list[Node]) -> None:
    """Remove each node's working directory. Idempotent: succeeds whether or
    not the directory exists. Runs in parallel across nodes.
    """

    def _rm(node: Node) -> None:
        with remote(node.host, node.user) as machine:
            machine["rm"]["-rf", str(node.wd)](retcode=None)

    fan_out(nodes, _rm)


def fetch(
    dest: Path,
    nodes: list[Node],
    include: Sequence[str] = (),
    exclude: Sequence[str] = (),
) -> None:
    """Pull each node's working directory into ``dest/<host>/`` via rsync.
    Runs in parallel across nodes. Fails fast if any single node's rsync
    fails.

    One directory per host, because every node in a deployment has the same
    working directory *path*: without the host in the destination, a
    multi-node run's files would land on top of each other.

    `include` and `exclude` are rsync filter patterns, passed in that order,
    so an include wins over a later exclude -- ``include=("*.log",),
    exclude=("*",)`` copies the logs and nothing else. Filtering also turns
    on ``-m``, which prunes the directories that end up empty rather than
    recreating the whole tree to hold a handful of files.
    """
    dest.mkdir(parents=True, exist_ok=True)

    def _pull(node: Node) -> None:
        if is_localhost(node.host):
            src = f"{node.wd}/"
        else:
            # rsync needs the login user for the same reason ssh does: the
            # account on a provisioned VM is not the local one.
            target = f"{node.user}@{node.host}" if node.user else node.host
            src = f"{target}:{node.wd}/"
        into = dest / node.host
        into.mkdir(parents=True, exist_ok=True)
        args = ["-a"]
        if include or exclude:
            args.append("-m")
        for pattern in include:
            args += ["--include", pattern]
        for pattern in exclude:
            args += ["--exclude", pattern]
        local["rsync"][args + [src, str(into)]]()

    fan_out(nodes, _pull)


def collect_node_artifacts(
    dest: Path,
    nodes: list[Node],
    keep_world: bool = False,
    level_name: str = "world",
) -> List[str]:
    """Copy each node's logs, crash reports and rendered configs into
    ``dest/<host>/``, and return the hosts it managed to collect from.

    This is what stands between a failed run and having nothing to look at:
    teardown removes the nodes' working directories, and in cloud mode the
    machines are destroyed minutes later. Call it *before* teardown.

    Never raises. Collection is evidence gathering, not part of the
    measurement: a node that has gone unreachable must not turn a run that
    otherwise succeeded into a failure, nor bury the exception from a run
    that failed. Problems are logged and the host is left out of the
    returned list.

    Args:
        dest: Directory to collect into, one subdirectory per host.
        nodes: Nodes to collect from.
        keep_world: Also copy the generated world. Off by default: a
            world-generation run produces gigabytes of region files, and
            copying them off every node would cost far more than the
            evidence is usually worth.
        level_name: The server's ``level-name``, i.e. the name of the world
            directory to copy when `keep_world` is set. Its sibling
            dimensions (``<level_name>_nether``, ``<level_name>_the_end``)
            come along too.
    """
    dest = Path(dest)
    includes = list(ARTIFACT_INCLUDES)
    if keep_world:
        # The world lives at `<server wd>/data/<level_name>`; `**/` is how an
        # rsync pattern reaches a name at an unknown depth, and `***` takes
        # the directory and everything under it.
        includes.insert(0, f"**/{level_name}*/***")

    collected: List[str] = []
    lock = threading.Lock()

    def _collect(node: Node) -> None:
        try:
            _stage_instance_logs(node)
            fetch(dest, [node], include=includes, exclude=("*",))
        except BaseException as exc:
            logger.warning(
                "could not collect artifacts from %s: %s (the run itself is "
                "unaffected)",
                node.host,
                exc,
            )
            return
        with lock:
            collected.append(node.host)

    fan_out(nodes, _collect)
    return sorted(collected)


def _stage_instance_logs(node: Node) -> None:
    """Copy a node's apptainer instance logs into its working directory.

    ``apptainer instance run`` -- how the game server, the database and the
    metrics agent are all started -- writes each container's stdout and
    stderr to ``~/.apptainer/instances/logs/<host>/<user>/<instance>.{out,err}``,
    outside the working directory that :func:`fetch` pulls. Copying them in
    first means one rsync collects everything, on a remote node as well as a
    local one.

    Best effort: a node with no instance logs (nothing was started, or
    apptainer keeps them elsewhere) is left alone.
    """
    script = (
        'src="$HOME/.apptainer/instances/logs"; '
        '[ -d "$src" ] || exit 0; '
        f'dst="{node.wd}/{INSTANCE_LOG_DIR}"; '
        'mkdir -p "$dst" && cp -RL "$src/." "$dst/"'
    )
    with remote(node.host, node.user) as machine:
        machine["sh"]["-c", script](retcode=None)
