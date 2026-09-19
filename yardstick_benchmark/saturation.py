"""Detecting when the measurement apparatus, not the game server, was the
bottleneck.

A benchmark result is only meaningful if the emulated players kept up. When
the machines running the bots run out of CPU or memory, the players send
fewer actions and load fewer chunks, so the server does *less* work -- and
the run reports the server looking healthy precisely when the experiment has
stopped measuring anything. That failure is silent: every component stays up,
the workload exits zero, and the numbers look plausible.

This module turns that into an explicit finding. Telegraf already collects
CPU, memory and swap on every node and tags each metric with
``yardstick_role``, so after a run we can ask whether the workload nodes were
themselves under strain and say so next to the results.

Thresholds are deliberately conservative: the aim is to flag a run whose
numbers should not be trusted, not to police every transient spike.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List

from yardstick_benchmark.monitoring import InfluxDB


logger = logging.getLogger(__name__)


#: Sustained CPU utilisation above this on a workload node means the bots were
#: competing for CPU with each other. Mineflayer runs one worker thread per
#: player, so a saturated node throttles every player on it at once.
DEFAULT_CPU_BUSY_PCT = 85.0

#: Memory above this leaves no headroom for the JVM-side spikes that chunk
#: loading causes on the client, and risks the OOM killer taking players out
#: mid-run.
DEFAULT_MEM_USED_PCT = 90.0

#: Any sustained swapping on a workload node invalidates its timing data.
DEFAULT_SWAP_USED_PCT = 10.0


@dataclass(frozen=True)
class SaturationFinding:
    """One resource on one node that exceeded its threshold."""

    node: str
    role: str
    resource: str
    observed: float
    threshold: float

    def __str__(self) -> str:
        return (
            f"{self.role} node {self.node}: {self.resource} reached "
            f"{self.observed:.1f}% (threshold {self.threshold:.0f}%)"
        )


@dataclass(frozen=True)
class SaturationReport:
    """The outcome of checking a run's nodes."""

    findings: List[SaturationFinding]
    #: False when no data was found at all -- which is itself worth knowing,
    #: because it means the check could not be performed rather than that the
    #: nodes were healthy.
    checked: bool = True

    @property
    def ok(self) -> bool:
        return self.checked and not self.findings

    def summary(self) -> str:
        if not self.checked:
            return (
                "could not check workload node saturation: no CPU metrics "
                "found for the run (was monitoring enabled?)"
            )
        if not self.findings:
            return "workload nodes had resource headroom throughout the run"
        lines = [
            "WARNING: workload nodes were resource constrained, so the "
            "server-side numbers from this run understate the load the "
            "players were meant to generate:"
        ]
        lines += [f"  - {finding}" for finding in self.findings]
        lines.append(
            "  Re-run with fewer players per node, or on larger workload nodes."
        )
        return "\n".join(lines)

    def as_dict(self) -> Dict[str, object]:
        return {
            "checked": self.checked,
            "ok": self.ok,
            "findings": [
                {
                    "node": f.node,
                    "role": f.role,
                    "resource": f.resource,
                    "observed_pct": round(f.observed, 2),
                    "threshold_pct": f.threshold,
                }
                for f in self.findings
            ],
        }


def _query_by_node(
    influxdb: InfluxDB,
    measurement: str,
    field: str,
    aggregate: str,
    start: str,
    stop: str,
    role: str,
    extra_filter: str = "",
) -> Dict[str, float]:
    """Aggregate one field per node, for nodes tagged with `role`."""
    info = influxdb.get_info()
    query = f'''
from(bucket: "{info.bucket}")
  |> range(start: {start}, stop: {stop})
  |> filter(fn: (r) => r._measurement == "{measurement}" and r._field == "{field}")
  |> filter(fn: (r) => r.yardstick_role == "{role}")
  {extra_filter}
  |> group(columns: ["yardstick_node"])
  |> {aggregate}()
'''
    values: Dict[str, float] = {}
    with influxdb._client() as client:
        tables = client.query_api().query(query=query, org=info.organization)
        for table in tables:
            for record in table.records:
                node = record.values.get("yardstick_node")
                value = record.get_value()
                if node is None or value is None:
                    continue
                values[str(node)] = float(value)
    return values


def check_workload_saturation(
    influxdb: InfluxDB,
    start: str,
    stop: str = "now()",
    role: str = "workload",
    cpu_busy_pct: float = DEFAULT_CPU_BUSY_PCT,
    mem_used_pct: float = DEFAULT_MEM_USED_PCT,
    swap_used_pct: float = DEFAULT_SWAP_USED_PCT,
) -> SaturationReport:
    """Check whether the nodes running emulated players had headroom.

    Args:
        influxdb: The database the run's metrics were written to. Query it
            before teardown -- the storage is removed with the deployment.
        start: Flux range start (an RFC3339 timestamp, or e.g. "-1h").
        stop: Flux range stop.
        role: The `yardstick_role` tag to check. Defaults to the emulated
            players' nodes, which are the ones whose saturation silently
            corrupts a result.
        cpu_busy_pct: Mean CPU utilisation, per node, above which the node is
            considered constrained. Mean rather than peak: a brief spike is
            normal, sustained saturation is what distorts a run.
        mem_used_pct: Peak memory utilisation per node.
        swap_used_pct: Peak swap utilisation per node.

    Returns:
        A report listing every threshold exceeded. An empty report means the
        players were not the bottleneck; it says nothing about whether the
        *server* was, which is what the benchmark is there to measure.
    """
    findings: List[SaturationFinding] = []

    # CPU is reported as idle time, so invert it. cpu-total is the whole
    # machine rather than a single core.
    idle = _query_by_node(
        influxdb,
        "cpu",
        "usage_idle",
        "mean",
        start,
        stop,
        role,
        extra_filter='|> filter(fn: (r) => r.cpu == "cpu-total")',
    )
    for node, mean_idle in idle.items():
        busy = 100.0 - mean_idle
        if busy > cpu_busy_pct:
            findings.append(
                SaturationFinding(node, role, "mean CPU usage", busy, cpu_busy_pct)
            )

    for measurement, field, threshold, label in (
        ("mem", "used_percent", mem_used_pct, "peak memory usage"),
        ("swap", "used_percent", swap_used_pct, "peak swap usage"),
    ):
        peaks = _query_by_node(influxdb, measurement, field, "max", start, stop, role)
        for node, value in peaks.items():
            if value > threshold:
                findings.append(SaturationFinding(node, role, label, value, threshold))

    report = SaturationReport(findings=findings, checked=bool(idle))
    if not report.ok:
        logger.warning("%s", report.summary())
    return report
