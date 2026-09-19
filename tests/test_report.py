"""The post-run report, built from a synthetic results directory.

A report is only useful if it is honest about the run it describes, so the
tests that matter here are about what it says rather than how it looks: that
the configuration and percentiles come through, that a saturated run is
labelled as one instead of being presented as a measurement, that the page is
self-contained, and that a directory missing half its data still produces a
report rather than an exception -- the report must never be the thing that
fails a run.

Everything runs against CSVs written in Flux's annotated format, the same
shape `InfluxDB.export_csv` produces; no run, no database, no containers.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("pandas")
pytest.importorskip("matplotlib")
pytest.importorskip("seaborn")

from yardstick_benchmark.__main__ import main  # noqa: E402
from yardstick_benchmark.report import (  # noqa: E402
    ReportError,
    collect,
    generate_report,
    try_generate_report,
)

START = datetime(2026, 9, 19, 10, 15, 0, tzinfo=timezone.utc)
DURATION_S = 300


def _annotated(header, rows, extra_types=""):
    """One Flux result table: annotations, a header row, then the data."""
    types = "string,long,dateTime:RFC3339,double,string,string,string" + extra_types
    groups = ",".join(["false"] * 4 + ["true"] * (len(header.split(",")) - 4))
    return (
        f"#datatype,{types}\n"
        f"#group,false,{groups}\n"
        f"#default,_result,,,,,,{',' * (len(extra_types.split(',')) - 1)}\n"
        f",result,table,{header}\n" + "".join(rows)
    )


def _rows(values, field, measurement, tags, start=START, step_s=1):
    out = []
    for i, value in enumerate(values):
        stamp = (start + timedelta(seconds=i * step_s)).strftime("%Y-%m-%dT%H:%M:%SZ")
        out.append(f",,0,{stamp},{value},{field},{measurement},{','.join(tags)}\n")
    return out


def _tick_csv():
    # A run that mostly keeps up and stalls hard a few times: without a tail
    # in the report, those stalls are exactly what a mean would hide.
    values = [45.0 + (i % 7) for i in range(200)]
    values[50] = 900.0
    values[120] = 1450.0
    return _annotated(
        "_time,_value,_field,_measurement,yardstick_node,yardstick_role",
        _rows(values, "tick_duration_ms", "minecraft_tick", ["10.0.0.1", "server"]),
        extra_types=",string",
    )


def _cpu_csv():
    idle = [30.0, 25.0, 20.0, 18.0, 22.0]
    server = _annotated(
        "_time,_value,_field,_measurement,yardstick_node,yardstick_role,cpu",
        _rows(
            idle,
            "usage_idle",
            "cpu",
            ["10.0.0.1", "server", "cpu-total"],
            step_s=10,
        ),
        extra_types=",string,string",
    )
    workload = _annotated(
        "_time,_value,_field,_measurement,yardstick_node,yardstick_role,cpu",
        _rows(
            [8.0, 6.0, 5.0, 4.0, 7.0],
            "usage_idle",
            "cpu",
            ["10.0.0.2", "workload", "cpu-total"],
            step_s=10,
        ),
        extra_types=",string,string",
    )
    return server + workload


def _mem_csv():
    return _annotated(
        "_time,_value,_field,_measurement,yardstick_node,yardstick_role",
        _rows(
            [40.0, 55.0, 61.0, 64.0, 66.0],
            "used_percent",
            "mem",
            ["10.0.0.1", "server"],
            step_s=10,
        ),
        extra_types=",string",
    )


def _jvm_csv():
    return _annotated(
        "_time,_value,_field,_measurement,yardstick_node,yardstick_role",
        _rows(
            [1.2e9, 1.6e9, 2.1e9, 1.1e9, 1.9e9],
            "HeapMemoryUsage_used",
            "jvm_memory",
            ["10.0.0.1", "server"],
            step_s=10,
        ),
        extra_types=",string",
    )


def _gc_csv():
    return _annotated(
        "_time,_value,_field,_measurement,yardstick_node,yardstick_role,name",
        _rows(
            [100.0, 180.0, 290.0, 410.0, 560.0],
            "CollectionTime",
            "jvm_garbage_collector",
            ["10.0.0.1", "server", "G1 Young Generation"],
            step_s=10,
        ),
        extra_types=",string,string",
    )


def manifest(saturation_ok=True, **overrides):
    finished = START + timedelta(seconds=DURATION_S)
    findings = (
        []
        if saturation_ok
        else [
            {
                "node": "10.0.0.2",
                "role": "workload",
                "resource": "mean CPU usage",
                "observed_pct": 94.2,
                "threshold_pct": 85.0,
            }
        ]
    )
    data = {
        "workload": "worldgen",
        "game": "minecraft",
        "started_at": START.isoformat(),
        "finished_at": finished.isoformat(),
        "duration_s": float(DURATION_S),
        "total_bots": 32,
        "hosts": ["10.0.0.1", "10.0.0.2"],
        "server_host": "10.0.0.1",
        "workload_hosts": ["10.0.0.2"],
        "influxdb_host": "10.0.0.2",
        "config": {
            "game": {
                "type": "minecraft",
                "seed": "yardstick",
                "version": "1.21.11",
                "view_distance": 10,
                "simulation_distance": 10,
            },
            "workload": {"type": "worldgen", "bots_per_node": 16, "teleports": 32},
            "deployment": {"mode": "cloud", "hosts": ["10.0.0.1", "10.0.0.2"]},
            "provisioning": {
                "provider": "ubicloud",
                "workload_nodes": 1,
                "options": {"location": "eu-central-h1"},
                "server": {"size": "standard-8"},
                "workload": {"size": "standard-4"},
            },
            "monitoring": {"enabled": True, "jolokia": True},
            "output": {"dir": "results"},
        },
        "files": ["cpu.csv", "mem.csv", "minecraft_tick.csv"],
        "workload_saturation": {
            "checked": True,
            "ok": saturation_ok,
            "findings": findings,
        },
    }
    data.update(overrides)
    return data


@pytest.fixture
def results_dir(tmp_path):
    def build(saturation_ok=True, csvs=True, **overrides):
        directory = tmp_path / ("ok" if saturation_ok else "saturated")
        directory.mkdir(exist_ok=True)
        if csvs:
            (directory / "minecraft_tick.csv").write_text(_tick_csv())
            (directory / "cpu.csv").write_text(_cpu_csv())
            (directory / "mem.csv").write_text(_mem_csv())
            (directory / "jvm_memory.csv").write_text(_jvm_csv())
            (directory / "jvm_garbage_collector.csv").write_text(_gc_csv())
        (directory / "run.json").write_text(
            json.dumps(manifest(saturation_ok, **overrides), indent=2)
        )
        return directory

    return build


def test_writes_report_next_to_the_data(results_dir):
    directory = results_dir()
    path = generate_report(directory)
    assert path == directory / "report.html"
    assert path.read_text().startswith("<!doctype html>")


def test_reports_the_configuration(results_dir):
    html = generate_report(results_dir()).read_text()
    for expected in ("worldgen", "minecraft", "1.21.11", "yardstick", "32"):
        assert expected in html
    # Machine sizes come from the provisioning section of the manifest.
    assert "standard-8" in html and "standard-4" in html


def test_reports_tick_percentiles_and_the_tail(results_dir):
    html = generate_report(results_dir()).read_text()
    assert "Tick duration" in html
    for label in ("p50", "p95", "p99"):
        assert label in html
    # The two 900+ ms stalls must be visible as the maximum, not averaged away.
    assert "1450.0 ms" in html
    assert "Ticks over 50 ms" in html


def test_charts_are_embedded_and_the_page_is_self_contained(results_dir):
    html = generate_report(results_dir()).read_text()
    assert html.count("data:image/png;base64,") >= 3
    assert "<script" not in html
    assert 'link rel="stylesheet"' not in html
    assert "http://" not in html and "https://" not in html


def test_a_sound_run_is_not_hedged(results_dir):
    html = generate_report(results_dir(saturation_ok=True)).read_text()
    assert "had resource headroom" in html
    assert "UNDERSTATES" not in html


def test_a_saturated_run_says_so_before_anything_else(results_dir):
    directory = results_dir(saturation_ok=False)
    html = generate_report(directory).read_text()
    assert "UNDERSTATES the intended load" in html
    assert "Result not trustworthy" in html
    # The finding itself, so the reader knows which machine and how far over.
    assert "94.2" in html and "mean CPU usage" in html
    # And it is at the top, above the charts it qualifies.
    assert html.index("UNDERSTATES") < html.index("data:image/png;base64,")


def test_an_unchecked_run_is_flagged_as_unverified(results_dir):
    directory = results_dir(
        workload_saturation={"checked": False, "ok": False, "findings": []}
    )
    html = generate_report(directory).read_text()
    assert "Result unverified" in html


def test_run_metadata(results_dir):
    html = generate_report(results_dir()).read_text()
    assert "Run metadata" in html
    assert "5 min 0 s" in html
    assert "10.0.0.1" in html


def test_a_recorded_crash_is_reported(results_dir):
    html = generate_report(
        results_dir(server_crashed=True, players_failed_to_join=True)
    ).read_text()
    assert "The server crashed." in html
    assert "Some emulated players never joined." in html


def test_a_directory_without_csvs_still_produces_a_report(results_dir):
    """A missing measurement is a note in the report, not a failure."""
    html = generate_report(results_dir(csvs=False)).read_text()
    assert "No minecraft_tick samples" in html
    assert "No CSV exports" in html


def test_a_directory_without_a_manifest_is_an_error(tmp_path):
    with pytest.raises(ReportError, match="run.json"):
        generate_report(tmp_path)


def test_try_generate_report_never_raises(tmp_path):
    assert try_generate_report(tmp_path / "does-not-exist") is None
    assert try_generate_report(tmp_path) is None


def test_collect_keeps_the_sections_separable(results_dir):
    """Collection is separate from rendering, so two runs can share a page."""
    report = collect(results_dir())
    assert [s.anchor for s in report.sections] == [
        "configuration",
        "run",
        "ticks",
        "server",
        "workload",
        "data",
    ]


def test_cli_report_subcommand(results_dir, tmp_path, capsys):
    directory = results_dir()
    out = tmp_path / "elsewhere.html"
    assert main(["report", str(directory), "-o", str(out)]) == 0
    assert out.exists()
    assert str(out) in capsys.readouterr().out


def test_cli_report_subcommand_reports_a_bad_directory(tmp_path, capsys):
    assert main(["report", str(tmp_path / "nope")]) == 2
    assert "error:" in capsys.readouterr().err
