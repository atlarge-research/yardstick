from yardstick_benchmark.model import RemoteApplication, Node
from pathlib import Path
from datetime import timedelta

class RedisWorkload(RemoteApplication):
    def __init__(
        self,
        nodes: list[Node],
        redis_host: str,
        duration: timedelta = timedelta(seconds=60),
        bots_per_node: int = 1,
        bot_start_delay: timedelta = timedelta(seconds=1),
        hz: int = 10,  # Default Hz for bot updates
        grid_radius: int = 1
    ):
        super().__init__(
            "redis_workload",
            nodes,
            Path(__file__).parent / "redis_workload_deploy.yml",
            Path(__file__).parent / "redis_workload_start.yml",
            Path(__file__).parent / "redis_workload_stop.yml",
            Path(__file__).parent / "redis_workload_cleanup.yml",
            extravars={
                "hostnames": [n.host for n in nodes],
                "scripts": [str(Path(__file__).parent / "redis_worker.py")],
                "duration": duration.total_seconds(),
                "redis_host": redis_host,
                "bots_per_node": bots_per_node,
                "bot_start_delay": bot_start_delay.total_seconds(),
                "node_indices": {n.host: i for i, n in enumerate(nodes)},
                "hz": hz ,
                "grid_radius": grid_radius
            },
        )
    
    @property
    def work_dir(self):
        """Return the working directory for the workload."""
        return next(iter(self.deploy_action.hosts.values()))["wd"]

    @property
    def worker_metrics_dir(self):
        """Get the directory where worker metrics are stored (same as work_dir)"""
        return self.work_dir