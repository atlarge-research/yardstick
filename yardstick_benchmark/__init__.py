from pathlib import Path

from plumbum import local

from yardstick_benchmark.model import Node
from yardstick_benchmark.util import fan_out, is_localhost, remote


def clean(nodes: list[Node]) -> None:
    """Remove each node's working directory. Idempotent: succeeds whether or
    not the directory exists. Runs in parallel across nodes.
    """

    def _rm(node: Node) -> None:
        with remote(node.host) as machine:
            machine["rm"]["-rf", str(node.wd)](retcode=None)

    fan_out(nodes, _rm)


def fetch(dest: Path, nodes: list[Node]) -> None:
    """Pull each node's working directory into `dest` via rsync. Runs in
    parallel across nodes. Fails fast if any single node's rsync fails.
    """
    dest.mkdir(parents=True, exist_ok=True)

    def _pull(node: Node) -> None:
        src = str(node.wd) if is_localhost(node.host) else f"{node.host}:{node.wd}"
        local["rsync"]["-a", src, str(dest)]()

    fan_out(nodes, _pull)
