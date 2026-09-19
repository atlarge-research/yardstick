"""Workload-node saturation detection.

The scenario being guarded against: the bot nodes run out of CPU, the
emulated players slow down, the server therefore does less work, and the run
reports a healthy-looking server. Everything stays up and the workload exits
zero, so nothing else in the system notices.
"""

from typing import Dict

import pytest

from yardstick_benchmark.saturation import (
    SaturationFinding,
    SaturationReport,
    check_workload_saturation,
)


class FakeInfluxDB:
    """Answers the module's three queries from a canned table."""

    def __init__(self, cpu_idle=None, mem_used=None, swap_used=None):
        self.data = {
            ("cpu", "usage_idle"): cpu_idle or {},
            ("mem", "used_percent"): mem_used or {},
            ("swap", "used_percent"): swap_used or {},
        }
        self.queries = []

    def get_info(self):
        class Info:
            bucket = "yardstick"
            organization = "yardstick"

        return Info()

    def _client(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def query_api(self):
        return self

    def query(self, query, org=None):
        self.queries.append(query)
        for (measurement, field), values in self.data.items():
            if f'r._measurement == "{measurement}"' in query and (
                f'r._field == "{field}"' in query
            ):
                return [_FakeTable(values)]
        return []


class _FakeTable:
    def __init__(self, values: Dict[str, float]):
        self.records = [_FakeRecord(node, value) for node, value in values.items()]


class _FakeRecord:
    def __init__(self, node, value):
        self.values = {"yardstick_node": node}
        self._value = value

    def get_value(self):
        return self._value


def test_healthy_nodes_produce_no_findings():
    influx = FakeInfluxDB(cpu_idle={"10.0.0.2": 70.0}, mem_used={"10.0.0.2": 40.0})
    report = check_workload_saturation(influx, start="-1h")
    assert report.ok
    assert report.findings == []
    assert "headroom" in report.summary()


def test_sustained_cpu_saturation_is_flagged():
    # 6% idle -> 94% busy, over the 85% default.
    influx = FakeInfluxDB(cpu_idle={"10.0.0.2": 6.0})
    report = check_workload_saturation(influx, start="-1h")
    assert not report.ok
    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.node == "10.0.0.2"
    assert finding.observed == pytest.approx(94.0)
    assert "CPU" in finding.resource


def test_the_warning_says_what_it_means_for_the_results():
    """A threshold breach is only useful if the reader learns the numbers are
    not trustworthy and what to do about it."""
    influx = FakeInfluxDB(cpu_idle={"10.0.0.2": 2.0})
    summary = check_workload_saturation(influx, start="-1h").summary()
    assert "understate the load" in summary
    assert "fewer players per node" in summary


def test_memory_and_swap_are_checked_too():
    influx = FakeInfluxDB(
        cpu_idle={"n1": 90.0},
        mem_used={"n1": 95.0},
        swap_used={"n1": 40.0},
    )
    report = check_workload_saturation(influx, start="-1h")
    resources = {f.resource for f in report.findings}
    assert "peak memory usage" in resources
    assert "peak swap usage" in resources


def test_only_the_requested_role_is_queried():
    """The game server is *expected* to run hot -- that's the thing being
    measured. Flagging it would be noise."""
    influx = FakeInfluxDB(cpu_idle={"n1": 50.0})
    check_workload_saturation(influx, start="-1h", role="workload")
    assert all('r.yardstick_role == "workload"' in q for q in influx.queries)


def test_cpu_query_uses_the_whole_machine_not_one_core():
    influx = FakeInfluxDB(cpu_idle={"n1": 50.0})
    check_workload_saturation(influx, start="-1h")
    cpu_query = next(q for q in influx.queries if '"cpu"' in q)
    assert 'r.cpu == "cpu-total"' in cpu_query


def test_no_metrics_at_all_is_reported_as_not_checked():
    """Absence of data must not be mistaken for a clean bill of health."""
    report = check_workload_saturation(FakeInfluxDB(), start="-1h")
    assert not report.ok
    assert not report.checked
    assert report.findings == []
    assert "could not check" in report.summary()


def test_thresholds_are_configurable():
    influx = FakeInfluxDB(cpu_idle={"n1": 30.0})  # 70% busy
    assert check_workload_saturation(influx, start="-1h").ok
    strict = check_workload_saturation(influx, start="-1h", cpu_busy_pct=60.0)
    assert not strict.ok


def test_report_serialises_for_the_run_manifest():
    report = SaturationReport(
        [SaturationFinding("n1", "workload", "mean CPU usage", 93.5, 85.0)]
    )
    payload = report.as_dict()
    assert payload["ok"] is False
    assert payload["findings"][0]["observed_pct"] == 93.5
    assert payload["findings"][0]["node"] == "n1"
