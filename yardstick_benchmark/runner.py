"""Turning a :class:`~yardstick_benchmark.config.BenchmarkConfig` into a run.

This is the straightforward path: bring up a database, a game server and a
metrics agent per node, run one workload, write the metrics out as CSV, tear
everything down. Experiments that need more than that should compose
components directly with :class:`~yardstick_benchmark.deployment.Deployment`;
this module is a worked example of doing exactly that.
"""

import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from yardstick_benchmark.config import BenchmarkConfig, build_kwargs
from yardstick_benchmark.deployment import Deployment
from yardstick_benchmark.model import Node
from yardstick_benchmark.monitoring import InfluxDB, Telegraf
from yardstick_benchmark.util import fan_out


logger = logging.getLogger(__name__)


def run(config: BenchmarkConfig, results_dir: Optional[Path] = None) -> Path:
    """Run the benchmark `config` describes and return its results directory.

    The directory holds one CSV per measurement plus a ``run.json`` manifest
    recording the configuration, timings and what was collected.
    """
    config.validate()

    wd = Path(config.deployment.wd)
    server_host = config.deployment.resolved_server_host()
    nodes = {host: Node(host, wd) for host in config.deployment.hosts}
    server_node = nodes[server_host]
    workload_nodes = [nodes[h] for h in config.deployment.workload_hosts()]

    if results_dir is None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        results_dir = Path(config.output.dir) / f"{config.workload}-{stamp}"
    results_dir = Path(results_dir)

    influxdb = InfluxDB(server_node)
    server = config.game_class(
        server_node,
        **build_kwargs(config.game_class, config.game_options, where="[game]"),
    )

    components: List[Any] = [influxdb, server]
    if config.monitoring.enabled:
        for node in nodes.values():
            telegraf = Telegraf(
                node,
                # Only the server's node has a JVM to scrape.
                jolokia=config.monitoring.jolokia and node.host == server_host,
                jolokia_port=getattr(server, "jolokia_port", 8778),
                execd_minecraft_ticks=(
                    config.monitoring.minecraft_ticks and node.host == server_host
                ),
            )
            telegraf.set_output_influxdb2(influxdb.get_info())
            components.append(telegraf)

    total_bots = _total_bots(config, len(workload_nodes))
    started_at = datetime.now(timezone.utc)

    with Deployment(*components, cleanup=not config.output.keep_node_data):
        # Put spawn at the origin so a workload's coordinates mean the same
        # thing from one run to the next.
        server.set_world_spawn(0, 0)
        server.start_health_monitor()

        workloads = [
            config.workload_class(
                node,
                **build_kwargs(
                    config.workload_class,
                    config.workload_options,
                    context=_context(server, server_host, influxdb, index, total_bots),
                    where="[workload]",
                ),
            )
            for index, node in enumerate(workload_nodes)
        ]

        try:
            logger.info(
                "running %s with %d player(s) across %d node(s)",
                config.workload,
                total_bots,
                len(workload_nodes),
            )
            fan_out(workloads, lambda w: w.deploy())
            fan_out(workloads, lambda w: w.run(health_check=server.assert_healthy))
        finally:
            fan_out(workloads, lambda w: w.cleanup())

        finished_at = datetime.now(timezone.utc)
        # Export before leaving the block: teardown stops the database, and
        # with keep_node_data = false it deletes its storage too.
        logger.info("exporting metrics to %s", results_dir)
        written = influxdb.export_csv(
            results_dir,
            start=started_at.isoformat(),
            stop=finished_at.isoformat(),
        )

    manifest = {
        "workload": config.workload,
        "game": config.game,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_s": (finished_at - started_at).total_seconds(),
        "total_bots": total_bots,
        "hosts": config.deployment.hosts,
        "server_host": server_host,
        "workload_hosts": [n.host for n in workload_nodes],
        "config": _manifest_config(config),
        "files": sorted(p.name for p in written),
    }
    (results_dir / "run.json").write_text(json.dumps(manifest, indent=2) + "\n")
    logger.info("wrote %d measurement file(s) to %s", len(written), results_dir)
    return results_dir


def _context(server, server_host, influxdb, bot_index, total_bots) -> Dict[str, Any]:
    """Values a workload can't know from its own config section.

    build_kwargs() keeps only the keys the workload's constructor actually
    accepts, so a workload that doesn't use RCON simply never sees the
    password. None values are dropped rather than passed through -- a game
    class without, say, a game_port must not end up overriding the workload's
    own default with None.
    """
    context = {
        "server_host": server_host,
        "server_port": getattr(server, "game_port", None),
        "rcon_port": getattr(server, "rcon_port", None),
        "rcon_password": getattr(server, "rcon_password", None),
        "minecraft_version": getattr(server, "version", None),
        "influxdb_info": influxdb.get_info(),
        "bot_index": bot_index,
        "total_bots": total_bots,
    }
    return {k: v for k, v in context.items() if v is not None}


def _total_bots(config: BenchmarkConfig, node_count: int) -> int:
    """Players across the whole run, for workloads that spread them out."""
    explicit = config.workload_options.get("total_bots")
    if explicit is not None:
        return int(explicit)
    per_node = int(config.workload_options.get("bots_per_node", 1))
    return per_node * node_count


def _manifest_config(config: BenchmarkConfig) -> Dict[str, Any]:
    return {
        "game": {"type": config.game, **config.game_options},
        "workload": {"type": config.workload, **config.workload_options},
        "deployment": asdict(config.deployment),
        "monitoring": asdict(config.monitoring),
        "output": asdict(config.output),
    }
