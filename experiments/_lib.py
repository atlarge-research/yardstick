"""Notebook helpers shared across experiments/.

Kept as `_lib` (leading underscore) to signal "private to this folder, not
part of the yardstick_benchmark public API".

Jupyter automatically prepends the notebook's directory to sys.path, so a
notebook under experiments/ can import this as ``from _lib import ...``.
"""

import pandas as pd
from influxdb_client.client.influxdb_client import InfluxDBClient

from yardstick_benchmark.monitoring import InfluxDB


def query_influxdb_dataframe(influxdb: InfluxDB, flux: str) -> pd.DataFrame:
    """Run a Flux query against `influxdb` and return the result as a
    pandas DataFrame. Thin wrapper around InfluxDBClient.query_api()
    .query_data_frame() that pulls token/org/url from the InfluxDB
    instance.

    The returned frame's columns match Flux's standard output: at minimum
    `_time`, `_value`, `_field`, `_measurement`, plus any tags. Multi-table
    Flux results come back as a list of DataFrames; for single-table
    queries the caller gets one frame.
    """
    info = influxdb.get_info()
    with InfluxDBClient(
        url=influxdb.url, token=info.token, org=info.organization
    ) as client:
        return client.query_api().query_data_frame(flux, org=info.organization)
