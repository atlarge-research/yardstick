"""Reading the CSV files a benchmark run exports.

:meth:`~yardstick_benchmark.monitoring.InfluxDB.export_csv` writes Flux's
annotated CSV, which is not a flat table. One file holds several *result
tables*, each introduced by its own ``#datatype``/``#group``/``#default``
annotations and its own header row -- and different tables in the same file
can have different columns, because the tag set varies between series.

That means the obvious ``pd.read_csv(path, comment="#")`` silently produces
garbage: the annotation lines vanish, but each table's header row survives as
data, and columns from tables with different shapes land on top of each
other. It is easy not to notice -- you get a DataFrame, it has plausible
column names, and some of the rows are even right.

:func:`read_csv` parses the file the way the format actually works: split it
into tables, read each with its own header, then align them by column name.
"""

import csv
import io
from pathlib import Path
from typing import Iterator, List, Optional, Union

try:
    import pandas as pd
except ImportError as exc:  # pragma: no cover - depends on the extra
    raise ImportError(
        "reading results needs pandas; install the 'notebooks' extra "
        "(uv sync --extra notebooks)"
    ) from exc


ANNOTATIONS = ("#datatype", "#group", "#default")


def _tables(text: str) -> Iterator[str]:
    """Split annotated CSV into one chunk per result table."""
    current: List[str] = []
    seen_data = False
    for line in text.splitlines():
        if line.startswith("#datatype") and seen_data:
            # A new table begins; emit what we have.
            yield "\n".join(current)
            current, seen_data = [], False
        if line.startswith(ANNOTATIONS):
            continue
        if not line.strip():
            continue
        current.append(line)
        seen_data = True
    if current:
        yield "\n".join(current)


def read_csv(
    path: Union[str, Path],
    field: Optional[str] = None,
    numeric: bool = True,
) -> "pd.DataFrame":
    """Read one exported measurement into a DataFrame.

    Args:
        path: An exported ``<measurement>.csv``.
        field: Keep only this ``_field``. A measurement usually holds several
            (``cpu`` carries ``usage_idle``, ``usage_user`` and a dozen
            more), and mixing them in one frame is rarely what you want.
        numeric: Coerce ``_value`` to numbers and ``_time`` to timestamps,
            dropping rows where that fails.

    Returns:
        A DataFrame with Flux's columns -- ``_time``, ``_value``, ``_field``,
        ``_measurement`` -- plus whatever tags the series carried, including
        Yardstick's ``yardstick_node`` and ``yardstick_role``.
    """
    text = Path(path).read_text()
    frames = []
    for chunk in _tables(text):
        reader = csv.reader(io.StringIO(chunk))
        rows = list(reader)
        if len(rows) < 2:
            continue
        header = [c.strip() for c in rows[0]]
        frame = pd.DataFrame(rows[1:], columns=header)
        # Flux's leading empty column carries nothing.
        frame = frame.loc[:, [c for c in frame.columns if c != ""]]
        frames.append(frame)
    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True, sort=False)
    if field is not None and "_field" in df.columns:
        df = df[df["_field"] == field]
    if numeric:
        if "_value" in df.columns:
            df["_value"] = pd.to_numeric(df["_value"], errors="coerce")
        if "_time" in df.columns:
            df["_time"] = pd.to_datetime(df["_time"], errors="coerce", format="mixed")
        subset = [c for c in ("_value", "_time") if c in df.columns]
        if subset:
            df = df.dropna(subset=subset)
    return df.reset_index(drop=True)


def elapsed(df: "pd.DataFrame", column: str = "_time") -> "pd.Series":
    """Seconds since the first sample -- a friendlier x-axis than wall clock."""
    return (df[column] - df[column].min()).dt.total_seconds()
