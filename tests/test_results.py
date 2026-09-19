"""Reading exported results.

Flux's annotated CSV holds several result tables per file, each with its own
header, and tables in one file can have different columns. The naive
`pd.read_csv(path, comment="#")` therefore produces a DataFrame that looks
fine and is wrong: header rows survive as data, and columns from
differently-shaped tables land on top of each other.

That is not hypothetical -- it is how a real run's `cpu-total` rows went
missing and hostnames turned up in the `cpu` column.
"""

import pytest

pd = pytest.importorskip("pandas")

from yardstick_benchmark.results import elapsed, read_csv  # noqa: E402


# Two tables, different shapes: the second carries an extra `cpu` tag. This
# is what a single measurement's export actually looks like.
TWO_TABLES = """#datatype,string,long,dateTime:RFC3339,double,string,string,string
#group,false,false,false,false,true,true,true
#default,_result,,,,,,
,result,table,_time,_value,_field,_measurement,yardstick_node
,,0,2026-09-19T02:22:35Z,1.5,usage_idle,cpu,10.0.0.1
,,0,2026-09-19T02:22:45Z,2.5,usage_idle,cpu,10.0.0.1
#datatype,string,long,dateTime:RFC3339,double,string,string,string,string
#group,false,false,false,false,true,true,true,true
#default,_result,,,,,,,
,result,table,_time,_value,_field,_measurement,yardstick_node,cpu
,,1,2026-09-19T02:22:35Z,3.5,usage_idle,cpu,10.0.0.2,cpu-total
,,1,2026-09-19T02:22:45Z,4.5,other_field,cpu,10.0.0.2,cpu-total
"""


def _write(tmp_path, text, name="cpu.csv"):
    path = tmp_path / name
    path.write_text(text)
    return path


def test_reads_every_table_in_the_file(tmp_path):
    df = read_csv(_write(tmp_path, TWO_TABLES))
    assert len(df) == 4


def test_header_rows_do_not_leak_into_the_data(tmp_path):
    """The failure mode of comment='#': each table's header survives as a row."""
    df = read_csv(_write(tmp_path, TWO_TABLES))
    assert "_value" not in set(df["_value"].astype(str))
    assert df["_value"].dtype.kind == "f"


def test_columns_from_differently_shaped_tables_stay_aligned(tmp_path):
    """The table without a `cpu` tag must not shift another column into it."""
    df = read_csv(_write(tmp_path, TWO_TABLES))
    first = df[df["yardstick_node"] == "10.0.0.1"]
    second = df[df["yardstick_node"] == "10.0.0.2"]
    assert first["cpu"].isna().all(), "a tag it never had was invented for it"
    assert set(second["cpu"]) == {"cpu-total"}


def test_field_filter(tmp_path):
    df = read_csv(_write(tmp_path, TWO_TABLES), field="usage_idle")
    assert len(df) == 3
    assert set(df["_field"]) == {"usage_idle"}


def test_times_are_parsed(tmp_path):
    df = read_csv(_write(tmp_path, TWO_TABLES))
    assert df["_time"].dtype.kind == "M"


def test_elapsed_starts_at_zero(tmp_path):
    df = read_csv(_write(tmp_path, TWO_TABLES))
    assert elapsed(df).min() == 0


def test_an_empty_export_is_not_an_error(tmp_path):
    assert read_csv(_write(tmp_path, "")).empty
