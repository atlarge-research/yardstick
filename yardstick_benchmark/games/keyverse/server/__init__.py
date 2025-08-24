from yardstick_benchmark.model import RemoteApplication, Node
from pathlib import Path


class RedisServer(RemoteApplication):
    def __init__(self, nodes: list[Node]):
        super().__init__(
            "redis",
            nodes,
            Path(__file__).parent / "redis_deploy.yml",
            Path(__file__).parent / "redis_start.yml",
            Path(__file__).parent / "redis_stop.yml",
            Path(__file__).parent / "redis_cleanup.yml",
            extravars={
                "hostnames": [n.host for n in nodes],
                "redis_template": str(Path(__file__).parent / "redis.conf.j2")
            },
        )
