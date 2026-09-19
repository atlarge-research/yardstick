"""Turning a results directory into a report a human can judge.

A run leaves behind one CSV per measurement and a ``run.json`` manifest.
Answering "how did this run go?" from that meant opening a notebook and
writing queries, every time. This module writes the answer out instead: a
single self-contained HTML file, next to the data, that shows the
configuration, the tick durations and their distribution, the server's
resources, and -- first, in a banner you cannot miss -- whether the workload
machines were saturated, which decides whether any of the rest means
anything.

Three decisions are worth spelling out.

*Self-contained HTML.* Charts are embedded as base64 PNGs and the stylesheet
is inline, so the file needs no server, no kernel and no network. It can be
mailed, committed next to the results, or opened years later.

*Generated from the exported CSVs, never from InfluxDB.* The database is torn
down with the deployment, so a report that queried it could only ever be
built once. Reading the CSVs means ``yardstick report <dir>`` works on any
results directory that survives. The CSVs are Flux's annotated format, so
they are read with :func:`yardstick_benchmark.results.read_csv` -- a plain
``pd.read_csv(comment="#")`` silently corrupts them.

*Off the critical path.* :func:`try_generate_report` never raises, and inside
a report every chart is drawn in isolation: a measurement that is missing,
empty or malformed turns into a note in the section where the chart would
have been. A benchmark that ran is not failed by a plot that didn't.

The structure is deliberately two-stage -- :func:`collect` reads a directory
into a :class:`RunReport`, :func:`render_html` turns one into a page -- so
that comparing two runs later means collecting twice and rendering a page
that takes both, rather than unpicking this module.
"""

import base64
import html
import io
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

logger = logging.getLogger(__name__)


#: Written into the results directory unless told otherwise.
REPORT_FILENAME = "report.html"

#: A tick that takes longer than this is a tick the server missed its 20 Hz
#: budget on; the fraction of ticks above it is the headline "was it keeping
#: up?" number.
TICK_BUDGET_MS = 50.0

#: Percentiles reported for tick duration. The mean hides the stalls that
#: matter, which is the whole reason this report exists.
PERCENTILES = (0.5, 0.95, 0.99)

_EXTRA_HINT = (
    "generating a report needs pandas, matplotlib and seaborn, which are in "
    "the 'notebooks' extra -- install them with 'uv sync --extra notebooks' "
    "(or 'pip install yardstick-benchmark[notebooks]')"
)


class ReportError(RuntimeError):
    """Raised when a report cannot be produced at all."""


# --------------------------------------------------------------------------
# Page model
#
# Sections hold blocks; blocks are rendered by type. Keeping the page as data
# rather than as strings is what makes a two-run report a new renderer over
# the same collectors instead of a rewrite.
# --------------------------------------------------------------------------


@dataclass
class Note:
    """A line of prose, coloured by how bad the news is."""

    text: str
    #: One of "info", "good", "warn", "bad".
    kind: str = "info"


@dataclass
class Table:
    """A key/value table, or a full one when `headers` is given."""

    rows: List[List[str]]
    headers: Optional[List[str]] = None
    caption: str = ""


@dataclass
class Chart:
    """A rendered figure, embedded in the page as a data URI."""

    title: str
    uri: str
    caption: str = ""


@dataclass
class Details:
    """A collapsed block of preformatted text -- the raw manifest, say."""

    summary: str
    text: str


Block = Union[Note, Table, Chart, Details]


@dataclass
class Section:
    anchor: str
    title: str
    lead: str = ""
    blocks: List[Block] = field(default_factory=list)

    def add(self, block: Block) -> None:
        self.blocks.append(block)


@dataclass
class RunReport:
    """Everything one run contributes to a page."""

    directory: Path
    title: str
    subtitle: str
    #: The saturation banner, shown above everything else.
    verdict: Note
    sections: List[Section] = field(default_factory=list)


# --------------------------------------------------------------------------
# Reading a results directory
# --------------------------------------------------------------------------


class RunData:
    """Lazy, forgiving access to one results directory.

    Every accessor returns an empty frame rather than raising when a
    measurement is absent: monitoring can be switched off, Jolokia can be
    switched off, and an old directory can simply predate a metric.
    """

    def __init__(self, directory: Path, manifest: Dict[str, Any]):
        self.directory = directory
        self.manifest = manifest
        self._cache: Dict[Any, Any] = {}

    def measurements(self) -> List[str]:
        return sorted(p.stem for p in self.directory.glob("*.csv"))

    def frame(self, measurement: str, field_name: Optional[str] = None):
        """One measurement (optionally one field) as a DataFrame."""
        key = (measurement, field_name)
        if key not in self._cache:
            from yardstick_benchmark.results import read_csv

            import pandas as pd

            path = self.directory / f"{measurement}.csv"
            if not path.exists():
                self._cache[key] = pd.DataFrame()
            else:
                try:
                    self._cache[key] = read_csv(path, field=field_name)
                except Exception as exc:  # pragma: no cover - corrupt export
                    logger.warning("could not read %s (%s)", path, exc)
                    self._cache[key] = pd.DataFrame()
        return self._cache[key]

    def fields(self, measurement: str) -> List[str]:
        df = self.frame(measurement)
        if df.empty or "_field" not in df.columns:
            return []
        return sorted(str(f) for f in df["_field"].dropna().unique())

    def config(self, *path: str, default: Any = None) -> Any:
        node: Any = self.manifest.get("config", {})
        for key in path:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node


def load_manifest(directory: Path) -> Dict[str, Any]:
    path = directory / "run.json"
    if not path.exists():
        raise ReportError(
            f"{directory} does not look like a results directory: no run.json. "
            f"Point 'yardstick report' at the directory a run wrote."
        )
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ReportError(f"{path} is not valid JSON ({exc})") from exc


def _role(df, role: str):
    """Rows from nodes tagged with `role`.

    An export from a run without the role tag (monitoring off, or a hand-made
    directory) has no such column; use it whole rather than pretending there
    is nothing there.
    """
    if df.empty or "yardstick_role" not in df.columns:
        return df
    return df[df["yardstick_role"] == role]


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------


def _mpl():
    """Import matplotlib/seaborn, with a message that says what to install."""
    try:
        import matplotlib
        import seaborn as sns
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure
    except ImportError as exc:  # pragma: no cover - depends on the extra
        raise ReportError(_EXTRA_HINT) from exc
    return matplotlib, sns, Figure, FigureCanvasAgg


def _figure(width: float, height: float):
    """A figure with an Agg canvas, built without pyplot.

    pyplot keeps global state and picks a backend from the environment, which
    is the wrong thing for a library that may be called from a notebook: this
    draws into its own canvas and leaves the caller's plotting alone.
    """
    _, _, Figure, FigureCanvasAgg = _mpl()
    fig = Figure(figsize=(width, height))
    FigureCanvasAgg(fig)
    return fig


def _to_uri(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _style():
    """seaborn's `ticks` look, applied without mutating global rcParams.

    Matches the chart style the experiment notebooks use (see
    ``experiments/tick_latency.ipynb``): white background, no grid, despined.
    """
    matplotlib, sns, _, _ = _mpl()
    rc = dict(sns.axes_style("ticks"))
    rc.update(sns.plotting_context("notebook"))
    return matplotlib.rc_context(rc)


def _seconds(df):
    """Seconds since this frame's first sample."""
    from yardstick_benchmark.results import elapsed

    return elapsed(df)


def _plot_lines(ax, df, ylabel: str, group: str = "yardstick_node") -> None:
    """One line per node (or per `group` value), against elapsed seconds."""
    _, sns, _, _ = _mpl()
    data = df.sort_values("_time")
    data = data.assign(_t=_seconds(data))
    keys = []
    if group in data.columns:
        keys = sorted(str(k) for k in data[group].dropna().unique())
    if len(keys) > 1:
        for key in keys:
            part = data[data[group].astype(str) == key]
            ax.plot(part["_t"], part["_value"], linewidth=1.0, label=key)
        ax.legend(frameon=False, fontsize="small")
    else:
        ax.plot(data["_t"], data["_value"], linewidth=1.0)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel(ylabel)
    ax.set_ylim(bottom=0)
    sns.despine(ax=ax)


def _chart(section: Section, title: str, draw: Callable[[], str], caption: str = ""):
    """Draw one chart, and turn a failure into a note instead of an error.

    This is the promise the issue asks for: a chart that cannot be drawn must
    not take the report -- let alone the run -- down with it.
    """
    try:
        uri = draw()
    except ReportError:
        raise
    except Exception as exc:
        logger.warning("could not draw %r (%s)", title, exc)
        section.add(Note(f"{title}: chart unavailable ({exc}).", "warn"))
        return
    if uri:
        section.add(Chart(title, uri, caption))


# --------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------


def _fmt(value: Any) -> str:
    if value is None:
        return "--"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:,.2f}".rstrip("0").rstrip(".")
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value) or "--"
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return str(value)


def _fmt_time(value: Any) -> str:
    try:
        return (
            datetime.fromisoformat(str(value)).strftime("%Y-%m-%d %H:%M:%S %Z").strip()
        )
    except (TypeError, ValueError):
        return _fmt(value)


def _fmt_duration(seconds: Any) -> str:
    try:
        total = float(seconds)
    except (TypeError, ValueError):
        return _fmt(seconds)
    minutes, secs = divmod(total, 60)
    if minutes < 1:
        return f"{total:.1f} s"
    return f"{int(minutes)} min {secs:.0f} s ({total:.0f} s)"


def _machine_sizes(data: RunData) -> str:
    """What the machines were, for the modes where Yardstick picked them."""
    mode = data.config("deployment", "mode", default="local")
    if mode == "local":
        return "local machine (not provisioned)"
    provisioning = data.config("provisioning", default=None)
    if not isinstance(provisioning, dict):
        return "not recorded"
    shared = provisioning.get("options") or {}

    def size(group: str) -> str:
        merged = {**shared, **(provisioning.get(group) or {})}
        return str(merged.get("size", "provider default"))

    workers = provisioning.get("workload_nodes", 1)
    return (
        f"server 1 x {size('server')}, workload {workers} x {size('workload')} "
        f"({provisioning.get('provider', 'unknown provider')})"
    )


def _saturation_verdict(manifest: Dict[str, Any]) -> Note:
    """The one sentence the rest of the report has to be read through."""
    saturation = manifest.get("workload_saturation")
    if not isinstance(saturation, dict):
        return Note(
            "No workload-saturation check is recorded for this run, so there "
            "is no evidence the emulated players kept up. Treat the "
            "server-side numbers below as unverified.",
            "warn",
        )
    if not saturation.get("checked", False):
        return Note(
            "The workload-saturation check could not run: no CPU metrics were "
            "found for the run. Whether the emulated players kept up is "
            "unknown, so the numbers below are unverified.",
            "warn",
        )
    if saturation.get("ok"):
        return Note(
            "The machines running the emulated players had resource headroom "
            "throughout the run, so the load the server saw is the load the "
            "experiment asked for.",
            "good",
        )
    return Note(
        "The machines running the emulated players ran out of resources. The "
        "players therefore sent fewer actions and loaded fewer chunks than "
        "the experiment asked for, so every server-side number in this report "
        "UNDERSTATES the intended load. Do not read the charts below as a "
        "measurement of the server at this player count; re-run with fewer "
        "players per node, or on larger workload machines.",
        "bad",
    )


def _configuration_section(data: RunData) -> Section:
    section = Section(
        "configuration",
        "Configuration",
        "What was run, in enough detail to run it again.",
    )
    manifest = data.manifest
    game = data.config("game", default={}) or {}
    workload = data.config("workload", default={}) or {}
    rows = [
        ["Game", _fmt(manifest.get("game") or game.get("type"))],
        ["Version", _fmt(game.get("version", "server default"))],
        ["Workload", _fmt(manifest.get("workload") or workload.get("type"))],
        ["Players", _fmt(manifest.get("total_bots"))],
        [
            "Workload machines",
            _fmt(len(manifest.get("workload_hosts") or []) or None),
        ],
        ["Machine sizes", _machine_sizes(data)],
        ["World seed", _fmt(game.get("seed", "random"))],
        ["View distance", _fmt(game.get("view_distance", "server default"))],
        [
            "Simulation distance",
            _fmt(game.get("simulation_distance", "server default")),
        ],
        ["Deployment mode", _fmt(data.config("deployment", "mode"))],
    ]
    for key in ("duration", "teleports", "bots_per_node"):
        if key in workload:
            rows.append([f"Workload {key.replace('_', ' ')}", _fmt(workload[key])])
    section.add(Table(rows))
    section.add(
        Details(
            "Full configuration as recorded in run.json",
            json.dumps(manifest.get("config", {}), indent=2, sort_keys=True),
        )
    )
    return section


def _metadata_section(data: RunData) -> Section:
    section = Section(
        "run",
        "Run metadata",
        "When it ran, how long for, and whether it ran to completion.",
    )
    manifest = data.manifest
    rows = [
        ["Started", _fmt_time(manifest.get("started_at"))],
        ["Finished", _fmt_time(manifest.get("finished_at"))],
        ["Duration", _fmt_duration(manifest.get("duration_s"))],
        ["Server host", _fmt(manifest.get("server_host"))],
        ["Workload hosts", _fmt(manifest.get("workload_hosts"))],
        ["Metrics database host", _fmt(manifest.get("influxdb_host"))],
        ["Measurements exported", _fmt(len(manifest.get("files") or []))],
    ]
    section.add(Table(rows))

    # A crash or a workload that never got a player online aborts a run
    # before the manifest is written, so the manifest's existence is itself
    # evidence -- but only up to the point it was written, which is why the
    # data-derived checks below are worth having.
    for key, good, bad in (
        ("server_crashed", "The server did not crash.", "The server crashed."),
        (
            "players_failed_to_join",
            "Every emulated player joined.",
            "Some emulated players never joined.",
        ),
    ):
        if key in manifest:
            failed = bool(manifest[key])
            section.add(Note(bad if failed else good, "bad" if failed else "good"))
    if "server_crashed" not in manifest:
        section.add(
            Note(
                "The run reached the end of its workload and exported its "
                "metrics: a server crash, or a workload in which no player "
                "ever joined, aborts a run before this manifest is written.",
                "info",
            )
        )

    _tick_coverage(data, section)
    _player_coverage(data, section)
    return section


def _tick_coverage(data: RunData, section: Section) -> None:
    """Did the tick metrics keep coming until the end of the run?

    A long gap at the end is what a server that stopped responding looks like
    in the data, even when nothing raised.
    """
    import pandas as pd

    ticks = data.frame("minecraft_tick", "tick_duration_ms")
    if ticks.empty or "_time" not in ticks.columns:
        section.add(
            Note(
                "No per-tick samples were exported, so the server's own "
                "health over the run cannot be checked here.",
                "warn",
            )
        )
        return
    finished = data.manifest.get("finished_at")
    if not finished:
        return
    try:
        end = pd.to_datetime(finished, format="mixed", utc=True)
        last = pd.to_datetime(ticks["_time"].max(), utc=True)
    except Exception:  # pragma: no cover - unparseable manifest timestamps
        return
    gap = (end - last).total_seconds()
    duration = float(data.manifest.get("duration_s") or 0.0)
    # Telegraf flushes every 10 s, so a gap of a few tens of seconds is
    # ordinary. Flag it when it eats a tenth of the run.
    if gap > max(30.0, 0.1 * duration):
        section.add(
            Note(
                f"Tick samples stop {gap:.0f} s before the recorded end of the "
                f"run. The server may have stopped responding, or metrics "
                f"collection may have stopped, well before the workload did.",
                "warn",
            )
        )


def _player_coverage(data: RunData, section: Section) -> None:
    """How many distinct players show up in the workload's own telemetry."""
    expected = data.manifest.get("total_bots")
    seen = set()
    for measurement in data.measurements():
        if not measurement.startswith("minecraft_") or measurement == "minecraft_tick":
            continue
        df = data.frame(measurement)
        if df.empty or "player" not in df.columns:
            continue
        seen.update(str(p) for p in df["player"].dropna().unique())
    if not seen:
        return
    if isinstance(expected, int) and len(seen) < expected:
        section.add(
            Note(
                f"Only {len(seen)} of the {expected} configured players appear "
                f"in the workload's telemetry: the rest never got far enough "
                f"to report anything, so the server was loaded by fewer "
                f"players than the configuration asks for.",
                "bad",
            )
        )
    else:
        section.add(Note(f"{len(seen)} player(s) reported workload telemetry.", "good"))


def _tick_section(data: RunData) -> Section:
    section = Section(
        "ticks",
        "Tick duration",
        "The headline metric. A Minecraft server ticks 20 times a second, so "
        f"a tick over {TICK_BUDGET_MS:.0f} ms is one the server did not keep "
        "up with. The mean hides exactly the stalls that matter, so the "
        "distribution and its tail are shown next to the time series.",
    )
    ticks = data.frame("minecraft_tick", "tick_duration_ms")
    if ticks.empty:
        section.add(
            Note(
                "No minecraft_tick samples in this results directory -- the "
                "tick collector was disabled, or the run predates it.",
                "warn",
            )
        )
        return section

    values = ticks["_value"].dropna()
    quantiles = values.quantile(list(PERCENTILES))
    over_budget = float((values > TICK_BUDGET_MS).mean() * 100.0)
    rows = [["Samples", f"{len(values):,}"]]
    rows.append(["Mean", f"{values.mean():.1f} ms"])
    for p in PERCENTILES:
        rows.append([f"p{p * 100:g}", f"{quantiles[p]:.1f} ms"])
    rows.append(["Max", f"{values.max():.1f} ms"])
    rows.append(
        [f"Ticks over {TICK_BUDGET_MS:.0f} ms", f"{over_budget:.2f}% of samples"]
    )
    tps = data.frame("minecraft_tick", "tps")
    if not tps.empty:
        rows.append(["Mean TPS", f"{tps['_value'].mean():.1f}"])
    section.add(Table(rows))

    def draw() -> str:
        _, sns, _, _ = _mpl()
        with _style():
            fig = _figure(11, 3.6)
            axes = fig.subplots(1, 2, width_ratios=[2, 1])
            over_time, dist = axes
            _plot_lines(over_time, ticks, "Tick duration [ms]", group="")
            over_time.set_title("Over time")
            for p, colour in zip(PERCENTILES, ("#4c72b0", "#dd8452", "#c44e52")):
                over_time.axhline(
                    quantiles[p],
                    color=colour,
                    linewidth=0.9,
                    linestyle="--",
                    label=f"p{p * 100:g}",
                )
            over_time.legend(frameon=False, fontsize="small")

            sns.histplot(x=values, bins=60, ax=dist, color="#4c72b0")
            # Log counts: the tail is a handful of samples next to thousands
            # of ordinary ticks, and on a linear axis it simply is not there.
            dist.set_yscale("log")
            dist.set_xlabel("Tick duration [ms]")
            dist.set_ylabel("Samples (log)")
            dist.set_title("Distribution")
            for p, colour in zip(PERCENTILES, ("#4c72b0", "#dd8452", "#c44e52")):
                dist.axvline(quantiles[p], color=colour, linewidth=0.9, linestyle="--")
            sns.despine(ax=dist)
            fig.tight_layout()
            return _to_uri(fig)

    _chart(
        section,
        "Tick duration over time and its distribution",
        draw,
        "Dashed lines mark p50, p95 and p99.",
    )
    return section


def _resources_section(data: RunData) -> Section:
    section = Section(
        "server",
        "Server resources",
        "What the machine under test was doing: CPU and memory of the host, "
        "then the JVM's heap and garbage collector.",
    )
    _chart(section, "Server CPU and memory", lambda: _cpu_mem_chart(data, "server"))

    heap = _heap_frame(data)
    gc = _role(data.frame("jvm_garbage_collector", "CollectionTime"), "server")
    if heap.empty and gc.empty:
        section.add(
            Note(
                "No JVM metrics in this directory: Jolokia was disabled, or "
                "the server was not a JVM.",
                "info",
            )
        )
        return section

    def draw() -> str:
        _, sns, _, _ = _mpl()
        with _style():
            fig = _figure(11, 3.4)
            axes = fig.subplots(1, 2)
            if heap.empty:
                axes[0].set_axis_off()
            else:
                mib = heap.assign(_value=heap["_value"] / (1024 * 1024))
                _plot_lines(axes[0], mib, "Heap used [MiB]", group="")
                axes[0].set_title("JVM heap")
            if gc.empty:
                axes[1].set_axis_off()
            else:
                _plot_lines(axes[1], _gc_rate(gc), "GC time [ms per s]", group="name")
                axes[1].set_title("Garbage collection")
            sns.despine(fig=fig)
            fig.tight_layout()
            return _to_uri(fig)

    _chart(
        section,
        "JVM heap and garbage collection",
        draw,
        "GC time is the per-second derivative of each collector's cumulative "
        "collection time: 1000 ms/s would mean a thread spent the whole "
        "second collecting.",
    )
    return section


def _heap_frame(data: RunData):
    """Heap-used samples, whatever Telegraf called the field.

    The Jolokia input flattens ``HeapMemoryUsage`` into one field per
    attribute, and the separator has changed between Telegraf versions, so
    match on the shape of the name rather than pinning one spelling.
    """
    df = _role(data.frame("jvm_memory"), "server")
    if df.empty or "_field" not in df.columns:
        return df
    wanted = [
        f
        for f in df["_field"].dropna().unique()
        if str(f).lower().startswith("heapmemoryusage")
        and str(f).lower().endswith("used")
    ]
    if not wanted:
        return df.iloc[0:0]
    return df[df["_field"] == wanted[0]]


def _gc_rate(gc):
    """Cumulative collection time -> ms of GC per second, per collector."""
    frames = []
    group = "name" if "name" in gc.columns else None
    parts = gc.groupby(group) if group else [("", gc)]
    for key, part in parts:
        part = part.sort_values("_time")
        seconds = part["_time"].diff().dt.total_seconds()
        rate = part["_value"].diff() / seconds
        out = part.assign(_value=rate.where(rate >= 0))
        frames.append(out.dropna(subset=["_value"]))
    import pandas as pd

    return pd.concat(frames, ignore_index=True) if frames else gc.iloc[0:0]


def _cpu_mem_chart(data: RunData, role: str) -> str:
    """CPU and memory over time for every node with the given role."""
    _, sns, _, _ = _mpl()
    cpu = _cpu_frame(data, role)
    mem = _role(data.frame("mem", "used_percent"), role)
    if cpu.empty and mem.empty:
        return ""
    with _style():
        fig = _figure(11, 3.4)
        axes = fig.subplots(1, 2)
        if cpu.empty:
            axes[0].set_axis_off()
        else:
            _plot_lines(axes[0], cpu, "CPU busy [%]")
            axes[0].set_ylim(0, 100)
            axes[0].set_title("CPU")
        if mem.empty:
            axes[1].set_axis_off()
        else:
            _plot_lines(axes[1], mem, "Memory used [%]")
            axes[1].set_ylim(0, 100)
            axes[1].set_title("Memory")
        sns.despine(fig=fig)
        fig.tight_layout()
        return _to_uri(fig)


def _cpu_frame(data: RunData, role: str):
    """Whole-machine CPU busy percentage.

    Telegraf reports ``usage_active`` when ``report_active`` is on and always
    reports ``usage_idle``; take the first and fall back to inverting the
    second, so an export from either configuration plots.
    """
    fields = data.fields("cpu")
    if "usage_active" in fields:
        df = _role(data.frame("cpu", "usage_active"), role)
        invert = False
    elif "usage_idle" in fields:
        df = _role(data.frame("cpu", "usage_idle"), role)
        invert = True
    else:
        return data.frame("cpu").iloc[0:0]
    if df.empty:
        return df
    if "cpu" in df.columns:
        total = df[df["cpu"] == "cpu-total"]
        # Per-core series would otherwise be drawn on top of the total.
        df = total if not total.empty else df
    return df.assign(_value=100.0 - df["_value"]) if invert else df


def _workload_section(data: RunData) -> Section:
    section = Section(
        "workload",
        "Workload-side health",
        "Whether the emulated players kept up. If they did not, the server "
        "did less work than the experiment asked for and every number above "
        "is an understatement rather than a measurement.",
    )
    section.add(_saturation_verdict(data.manifest))
    saturation = data.manifest.get("workload_saturation")
    if isinstance(saturation, dict) and saturation.get("findings"):
        rows = [
            [
                _fmt(f.get("node")),
                _fmt(f.get("role")),
                _fmt(f.get("resource")),
                f"{_fmt(f.get('observed_pct'))}%",
                f"{_fmt(f.get('threshold_pct'))}%",
            ]
            for f in saturation["findings"]
        ]
        section.add(
            Table(
                rows,
                headers=["Node", "Role", "Resource", "Observed", "Threshold"],
                caption="Thresholds exceeded on the machines running players",
            )
        )
    _chart(
        section,
        "Workload machine CPU and memory",
        lambda: _cpu_mem_chart(data, "workload"),
    )
    return section


def _data_section(data: RunData) -> Section:
    section = Section(
        "data",
        "Exported data",
        "Everything this report was built from. Regenerate it at any time "
        "with 'yardstick report <this directory>'.",
    )
    measurements = data.measurements()
    if not measurements:
        section.add(Note("No CSV exports in this directory.", "warn"))
        return section
    rows = []
    for name in measurements:
        size = (data.directory / f"{name}.csv").stat().st_size
        rows.append([name, f"{size / 1024:,.0f} KiB"])
    section.add(Table(rows, headers=["Measurement", "Size"]))
    return section


#: The sections a single-run report is made of, in order. A comparison
#: report is the same collectors run over two directories.
SECTIONS: Sequence[Callable[[RunData], Section]] = (
    _configuration_section,
    _metadata_section,
    _tick_section,
    _resources_section,
    _workload_section,
    _data_section,
)


def collect(directory: Union[str, Path]) -> RunReport:
    """Read a results directory into the model a report is rendered from."""
    directory = Path(directory)
    manifest = load_manifest(directory)
    data = RunData(directory, manifest)
    workload = manifest.get("workload", "run")
    game = manifest.get("game", "")
    started = _fmt_time(manifest.get("started_at"))
    report = RunReport(
        directory=directory,
        title=f"{workload} on {game}".strip() if game else str(workload),
        subtitle=f"{directory.name} -- started {started}",
        verdict=_saturation_verdict(manifest),
    )
    for build in SECTIONS:
        try:
            report.sections.append(build(data))
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("could not build a report section (%s)", exc)
            report.sections.append(
                Section(
                    "error",
                    "Section unavailable",
                    blocks=[Note(f"This section could not be built ({exc}).", "warn")],
                )
            )
    return report


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


_CSS = """
:root { color-scheme: light; }
body { margin: 0; padding: 2rem 1rem 4rem; background: #f7f7f8; color: #16181d;
  font: 16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
  "Helvetica Neue", Arial, sans-serif; }
main { max-width: 60rem; margin: 0 auto; }
h1 { font-size: 1.7rem; margin: 0 0 .25rem; }
h2 { font-size: 1.2rem; margin: 0 0 .5rem; }
.sub { color: #5c6270; margin: 0 0 1.5rem; }
section { background: #fff; border: 1px solid #e3e5ea; border-radius: 8px;
  padding: 1.25rem 1.5rem; margin: 0 0 1.25rem; }
.lead { color: #454b57; margin: 0 0 1rem; }
table { border-collapse: collapse; margin: 0 0 1rem; font-size: .93rem; }
caption { text-align: left; color: #5c6270; font-size: .85rem;
  padding-bottom: .35rem; }
th, td { text-align: left; padding: .35rem .9rem .35rem 0;
  border-bottom: 1px solid #eceef2; vertical-align: top; }
th { color: #5c6270; font-weight: 600; }
td:first-child { color: #5c6270; white-space: nowrap; }
table.kv td:last-child { color: #16181d; font-variant-numeric: tabular-nums; }
figure { margin: 0 0 1.25rem; }
figure img { max-width: 100%; height: auto; }
figcaption { color: #5c6270; font-size: .85rem; margin-top: .35rem; }
.chart-title { font-weight: 600; font-size: .95rem; margin: 0 0 .35rem; }
.note { border-left: 4px solid #c5c9d2; background: #f4f5f7; padding: .7rem 1rem;
  border-radius: 0 6px 6px 0; margin: 0 0 1rem; }
.note.good { border-color: #2f855a; background: #eefaf2; }
.note.warn { border-color: #b7791f; background: #fdf6e7; }
.note.bad { border-color: #c53030; background: #fdeceb; }
.verdict { font-size: 1.02rem; }
.verdict strong { display: block; margin-bottom: .3rem; }
details { margin: 0 0 .5rem; }
summary { cursor: pointer; color: #454b57; font-size: .9rem; }
pre { background: #f4f5f7; padding: .8rem 1rem; border-radius: 6px;
  overflow-x: auto; font-size: .82rem; }
nav a { color: #2c5282; margin-right: 1rem; font-size: .9rem; }
footer { color: #767c8a; font-size: .82rem; text-align: center; }
"""

_VERDICT_HEADINGS = {
    "good": "Result looks sound",
    "warn": "Result unverified",
    "bad": "Result not trustworthy",
    "info": "Result",
}


def _e(text: Any) -> str:
    return html.escape(str(text))


def _render_block(block: Block) -> str:
    if isinstance(block, Note):
        return f'<p class="note {_e(block.kind)}">{_e(block.text)}</p>'
    if isinstance(block, Table):
        parts = ["<table" + ("" if block.headers else ' class="kv"') + ">"]
        if block.caption:
            parts.append(f"<caption>{_e(block.caption)}</caption>")
        if block.headers:
            head = "".join(f"<th>{_e(h)}</th>" for h in block.headers)
            parts.append(f"<thead><tr>{head}</tr></thead>")
        parts.append("<tbody>")
        for row in block.rows:
            cells = "".join(f"<td>{_e(cell)}</td>" for cell in row)
            parts.append(f"<tr>{cells}</tr>")
        parts.append("</tbody></table>")
        return "".join(parts)
    if isinstance(block, Chart):
        caption = (
            f"<figcaption>{_e(block.caption)}</figcaption>" if block.caption else ""
        )
        return (
            f'<figure><p class="chart-title">{_e(block.title)}</p>'
            f'<img alt="{_e(block.title)}" src="{block.uri}">{caption}</figure>'
        )
    if isinstance(block, Details):
        return (
            f"<details><summary>{_e(block.summary)}</summary>"
            f"<pre>{_e(block.text)}</pre></details>"
        )
    raise TypeError(f"unknown block type: {type(block)!r}")  # pragma: no cover


def render_html(report: RunReport) -> str:
    """Render a collected report as one self-contained HTML page."""
    nav = " ".join(
        f'<a href="#{_e(s.anchor)}">{_e(s.title)}</a>' for s in report.sections
    )
    body = []
    for section in report.sections:
        lead = f'<p class="lead">{_e(section.lead)}</p>' if section.lead else ""
        blocks = "".join(_render_block(b) for b in section.blocks)
        body.append(
            f'<section id="{_e(section.anchor)}"><h2>{_e(section.title)}</h2>'
            f"{lead}{blocks}</section>"
        )
    verdict = report.verdict
    heading = _VERDICT_HEADINGS.get(verdict.kind, "Result")
    generated = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Yardstick report -- {_e(report.title)}</title>
<style>{_CSS}</style>
</head>
<body>
<main>
<h1>Yardstick report: {_e(report.title)}</h1>
<p class="sub">{_e(report.subtitle)}</p>
<p class="note verdict {_e(verdict.kind)}"><strong>{_e(heading)}</strong>
{_e(verdict.text)}</p>
<nav>{nav}</nav>
{"".join(body)}
<footer>Generated by Yardstick from {_e(report.directory)} on {_e(generated)}.
Regenerate with <code>yardstick report {_e(report.directory)}</code>.</footer>
</main>
</body>
</html>
"""


def generate_report(
    results_dir: Union[str, Path],
    output: Optional[Union[str, Path]] = None,
) -> Path:
    """Write an HTML report for `results_dir` and return the file's path.

    Args:
        results_dir: A directory a run wrote -- CSV exports plus ``run.json``.
        output: Where to write. Defaults to ``<results_dir>/report.html``.

    Raises:
        ReportError: if the directory holds no manifest, or the plotting
            dependencies are missing.
    """
    results_dir = Path(results_dir)
    if not results_dir.is_dir():
        raise ReportError(f"no such results directory: {results_dir}")
    try:
        import pandas  # noqa: F401
    except ImportError as exc:
        raise ReportError(_EXTRA_HINT) from exc
    _mpl()

    report = collect(results_dir)
    path = Path(output) if output else results_dir / REPORT_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_html(report))
    return path


def try_generate_report(results_dir: Union[str, Path]) -> Optional[Path]:
    """Generate a report, or log why not. Never raises.

    This is the form the runner calls: a benchmark that ran and exported its
    metrics must not be turned into a failure by a missing plotting library
    or an unhappy chart.
    """
    try:
        return generate_report(results_dir)
    except ReportError as exc:
        logger.warning("no report written: %s", exc)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("no report written: %s", exc, exc_info=True)
    return None
