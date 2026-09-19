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

import threading
from contextlib import contextmanager

from yardstick_benchmark.config import BenchmarkConfig, build_kwargs
from yardstick_benchmark.deployment import Deployment
from yardstick_benchmark.model import Node
from yardstick_benchmark.monitoring import InfluxDB, Telegraf
from yardstick_benchmark.report import try_generate_report
from yardstick_benchmark.saturation import check_workload_saturation
from yardstick_benchmark.util import fan_out


logger = logging.getLogger(__name__)


def run(config: BenchmarkConfig, results_dir: Optional[Path] = None) -> Path:
    """Run the benchmark `config` describes and return its results directory.

    The directory holds one CSV per measurement plus a ``run.json`` manifest
    recording the configuration, timings and what was collected.
    """
    config.validate()

    if results_dir is None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        results_dir = Path(config.output.dir) / f"{config.workload}-{stamp}"
    results_dir = Path(results_dir)

    with machines(config) as placed:
        return _run_on(config, placed, results_dir)


@contextmanager
def machines(config: BenchmarkConfig):
    """Yield the machines a run needs, as ``{role: node-or-nodes}``.

    In `local` mode they already exist and nothing is acquired. In
    `cloud`/`cluster` mode they are provisioned and then released again --
    always, including when the benchmark raises, because a leaked VM bills
    until someone notices and a leaked cluster reservation blocks other
    users.

    The game server always gets a machine to itself. Where the metrics
    database goes is set by ``[monitoring] influxdb_placement``; it defaults
    to a workload machine rather than the server's, because InfluxDB's WAL
    flushes and compaction would otherwise spike CPU and disk I/O on exactly
    the machine whose tick durations are being measured.
    """
    placement = config.monitoring.influxdb_placement
    if config.deployment.mode == "local":
        wd = Path(config.deployment.wd)
        nodes = {host: Node(host, wd) for host in config.deployment.hosts}
        server_host = config.deployment.resolved_server_host()
        server = nodes[server_host]
        workload = [nodes[h] for h in config.deployment.workload_hosts()]
        influx = server if placement == "server" else workload[0]
        yield {"server": server, "workload": workload, "influxdb": influx}
        return

    provider = config.provider_class

    def pool(group: str):
        return provider(
            **build_kwargs(
                provider,
                config.provisioning.options_for(group),
                where=f"[provisioning.{group}]",
            )
        )

    plan = [
        ("server", pool("server"), 1),
        ("workload", pool("workload"), config.provisioning.workload_nodes),
    ]
    if placement == "dedicated":
        plan.append(("influxdb", pool("influxdb"), 1))

    acquired: List[Any] = []
    lock = threading.Lock()
    results: Dict[str, List[Node]] = {}

    def acquire(entry):
        group, group_pool, count = entry
        logger.info("provisioning %d machine(s) for %s", count, group)
        nodes = group_pool.provision(count, wd=config.deployment.wd or None)
        with lock:
            acquired.append((group_pool, nodes))
            results[group] = nodes

    try:
        # Provision the groups concurrently. Each machine spends minutes in
        # its init script, so doing this one group after another roughly
        # doubles the time before a run can start.
        fan_out(plan, acquire)
        server = results["server"][0]
        workload = results["workload"]
        if placement == "dedicated":
            influx = results["influxdb"][0]
        elif placement == "server":
            influx = server
        else:
            influx = workload[0]
        yield {"server": server, "workload": workload, "influxdb": influx}
    finally:
        for group_pool, pool_nodes in reversed(acquired):
            try:
                logger.info("releasing %d machine(s)", len(pool_nodes))
                group_pool.release(pool_nodes)
            except Exception as exc:
                logger.error(
                    "could not release machines (%s). They are recorded in %s; "
                    "run `yardstick machines release` to give them back.",
                    exc,
                    group_pool.ledger.path,
                )


def _run_on(
    config: BenchmarkConfig,
    placed: Dict[str, Any],
    results_dir: Path,
) -> Path:
    server_node = placed["server"]
    workload_nodes = placed["workload"]
    influx_node = placed["influxdb"]
    server_host = server_node.host
    nodes = {server_node.host: server_node}
    for node in workload_nodes:
        nodes.setdefault(node.host, node)
    nodes.setdefault(influx_node.host, influx_node)

    influxdb = InfluxDB(influx_node)
    server = config.game_class(
        server_node,
        **build_kwargs(config.game_class, config.game_options, where="[game]"),
    )

    components: List[Any] = [influxdb, server]
    if config.monitoring.enabled:
        for node in nodes.values():
            is_server = node.host == server_host
            telegraf = Telegraf(
                node,
                # Only the server's node has a JVM to scrape.
                jolokia=config.monitoring.jolokia and is_server,
                jolokia_port=getattr(server, "jolokia_port", 8778),
                execd_minecraft_ticks=(config.monitoring.minecraft_ticks and is_server),
                # Tag every metric with where it came from and what that
                # machine was doing, so server and player metrics can be told
                # apart after the fact.
                tags={
                    "yardstick_node": node.host,
                    "yardstick_role": "server" if is_server else "workload",
                },
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

        # Did the players actually keep up? If the workload nodes ran out of
        # CPU or memory, the server did less work than the experiment asked
        # for and the numbers understate the load. Check before teardown,
        # while the database is still up.
        saturation = check_workload_saturation(
            influxdb,
            start=started_at.isoformat(),
            stop=finished_at.isoformat(),
        )
        if not saturation.ok:
            logger.warning("%s", saturation.summary())

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
        "hosts": sorted(nodes),
        "server_host": server_host,
        "workload_hosts": [n.host for n in workload_nodes],
        "influxdb_host": influx_node.host,
        "config": _manifest_config(config),
        "files": sorted(p.name for p in written),
        # Recorded next to the data, so a result can't be read later without
        # the caveat that came with it.
        "workload_saturation": saturation.as_dict(),
    }
    (results_dir / "run.json").write_text(json.dumps(manifest, indent=2) + "\n")
    logger.info("wrote %d measurement file(s) to %s", len(written), results_dir)

    # Deliberately last, and deliberately unable to fail the run: a benchmark
    # that ran and exported its metrics is a success even if no chart could
    # be drawn. The same report can be regenerated from this directory at any
    # time with `yardstick report`.
    report = try_generate_report(results_dir)
    if report is not None:
        print(f"report: {report}")

    if not saturation.ok:
        print(saturation.summary())
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
        # Recorded so a report can say what the machines were: for a
        # provisioned run the sizes are part of the result, not an
        # implementation detail of how it was started.
        "provisioning": asdict(config.provisioning),
        "monitoring": asdict(config.monitoring),
        "output": asdict(config.output),
    }
