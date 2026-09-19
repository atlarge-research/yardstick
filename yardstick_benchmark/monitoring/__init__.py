"""Metric collection: an InfluxDB v2 time-series database and Telegraf agents.

A typical deployment runs one :class:`InfluxDB` (on any node) and one
:class:`Telegraf` per node under measurement, each pointed at that database
with :meth:`Telegraf.set_output_influxdb2`.
"""

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from jinja2 import Template

from influxdb_client.client.influxdb_client import InfluxDBClient

from yardstick_benchmark.model import Node
from yardstick_benchmark.util import random_string, remote, stage, wait_for_url


# Default port the Minecraft server's Jolokia agent listens on. Kept in step
# with MinecraftServer.JOLOKIA_PORT, but defined here so configuring Telegraf
# doesn't require importing the game package.
JOLOKIA_PORT = 8778


@dataclass(frozen=True)
class InfluxDBInfo:
    urls: List[str]
    token: str
    organization: str = "yardstick"
    bucket: str = "yardstick"


class InfluxDB(object):
    """A single InfluxDB v2 deployment on one node.

    To run multiple independent InfluxDB instances (rare), construct one
    `InfluxDB` per target node with a distinct `name`. To have several
    Telegraf agents write to the *same* InfluxDB, share the same instance's
    `get_info()` with each Telegraf.

    The database's storage is bind-mounted from ``node.wd``. This matters:
    the containers run with ``--compat``, which implies ``--writable-tmpfs``,
    so without an explicit bind the entire database would live in a
    memory-backed overlay that is capped at a few tens of MB and is discarded
    the moment the instance stops.
    """

    DEFAULT_IMAGE_URL = "docker://influxdb:2.8"
    DEFAULT_PORT = 8086

    def __init__(
        self,
        node: Node,
        name: str = "influxdb",
        admin_password: str = "password",
        admin_token: Optional[str] = None,
        port: int = DEFAULT_PORT,
        image_url: str = DEFAULT_IMAGE_URL,
    ):
        """
        Args:
            node: Node to run the database on.
            name: Apptainer instance name. Override it to run more than one
                database, or to avoid clashing with another user's instance
                on a shared node.
            admin_password: Initial admin password.
            admin_token: Initial admin token. Generated if not given.
            port: HTTP port the database listens on.
            image_url: Container image to run.
        """
        self.node = node
        self.name = name
        self.image_url = image_url
        self.admin_password = admin_password
        self.admin_token = admin_token or random_string(16)
        self.port = port
        self.wd = f"{node.wd}/{name}"
        self.data_dir = f"{self.wd}/data"
        self.config_dir = f"{self.wd}/config"

    @property
    def url(self) -> str:
        return f"http://{self.node.host}:{self.port}"

    def deploy(self) -> None:
        """Create the database's storage directories on the node."""
        with remote(self.node.host) as machine:
            machine["mkdir"]["-p", self.data_dir, self.config_dir]()

    def _initialised(self, machine) -> bool:
        """True if this data directory already holds a set-up database.

        Re-running the image's ``setup`` init mode against an existing
        database makes it exit with "has already been set up", so a restart
        against persisted data has to skip the DOCKER_INFLUXDB_INIT_* vars.
        """
        return machine.path(f"{self.data_dir}/influxd.bolt").exists()

    def start(self) -> None:
        with remote(self.node.host) as machine:
            machine["mkdir"]["-p", self.data_dir, self.config_dir]()
            args = [
                "instance",
                "run",
                "--no-https",
                "--compat",
                "--bind",
                f"{self.data_dir}:/var/lib/influxdb2",
                "--bind",
                f"{self.config_dir}:/etc/influxdb2",
                "--env",
                f"INFLUXD_HTTP_BIND_ADDRESS=:{self.port}",
            ]
            if not self._initialised(machine):
                args += [
                    "--env",
                    "DOCKER_INFLUXDB_INIT_MODE=setup",
                    "--env",
                    "DOCKER_INFLUXDB_INIT_USERNAME=admin",
                    "--env",
                    f"DOCKER_INFLUXDB_INIT_PASSWORD={self.admin_password}",
                    "--env",
                    "DOCKER_INFLUXDB_INIT_ORG=yardstick",
                    "--env",
                    "DOCKER_INFLUXDB_INIT_BUCKET=yardstick",
                    "--env",
                    f"DOCKER_INFLUXDB_INIT_ADMIN_TOKEN={self.admin_token}",
                ]
            args += [self.image_url, self.name]
            machine["apptainer"][args]()

    def stop(self) -> None:
        with remote(self.node.host) as machine:
            machine["apptainer"]["instance", "stop", self.name].run(retcode=None)

    def cleanup(self) -> None:
        """Remove the database's storage directory."""
        with remote(self.node.host) as machine:
            machine["rm"]["-rf", self.wd](retcode=None)

    def ready(self, timeout_s: float = 120) -> None:
        """Block until the database answers on its /health endpoint.

        Deployment calls this automatically after start(); Telegraf's first
        write batch fails if it beats the database to readiness.
        """
        wait_for_url(f"{self.url}/health", timeout_s=timeout_s)

    def get_info(self) -> InfluxDBInfo:
        return InfluxDBInfo([self.url], self.admin_token)

    def _client(self) -> InfluxDBClient:
        info = self.get_info()
        return InfluxDBClient(url=self.url, token=info.token, org=info.organization)

    def measurements(self, lookback: str = "-24h") -> List[str]:
        """List the measurement names present in the bucket."""
        info = self.get_info()
        query = f'''
import "influxdata/influxdb/schema"
schema.measurements(bucket: "{info.bucket}", start: {lookback})
'''
        names: List[str] = []
        with self._client() as client:
            tables = client.query_api().query(query=query, org=info.organization)
            for table in tables:
                for record in table.records:
                    value = record.get_value()
                    if value is not None:
                        names.append(str(value))
        return sorted(set(names))

    def verify_data(
        self,
        expected_measurements: Optional[List[str]] = None,
        lookback: str = "-5m",
    ) -> Dict[str, int]:
        info = self.get_info()
        query = f'''
from(bucket: "{info.bucket}")
  |> range(start: {lookback})
  |> group(columns: ["_measurement"])
  |> count()
  |> keep(columns: ["_measurement", "_value"])
'''
        counts: Dict[str, int] = {}
        with self._client() as client:
            tables = client.query_api().query(query=query, org=info.organization)
            for table in tables:
                for record in table.records:
                    measurement = record.values.get("_measurement")
                    if measurement is None:
                        continue
                    counts[measurement] = counts.get(measurement, 0) + int(
                        record.get_value() or 0
                    )

        if expected_measurements:
            missing = [m for m in expected_measurements if counts.get(m, 0) == 0]
            if missing:
                raise RuntimeError(
                    f"InfluxDB verification failed: no points for {missing} in bucket "
                    f"'{info.bucket}' within {lookback}. Counts observed: {counts}"
                )
        return counts

    def export_csv(
        self,
        dest: Path,
        measurements: Optional[Sequence[str]] = None,
        start: str = "-24h",
        stop: str = "now()",
    ) -> List[Path]:
        """Write each measurement in the bucket to ``dest/<measurement>.csv``.

        The database itself is torn down at the end of a run, so this is how
        results leave a benchmark in a durable, re-analysable form: the CSVs
        are plain Flux-annotated output and load straight into pandas with
        ``pd.read_csv(path, comment="#")``.

        Args:
            dest: Local directory to write into. Created if missing.
            measurements: Measurement names to export. Defaults to every
                measurement present in the bucket.
            start: Flux range start (e.g. "-24h", or an RFC3339 timestamp).
            stop: Flux range stop.

        Returns:
            The list of files written, one per non-empty measurement.
        """
        info = self.get_info()
        dest.mkdir(parents=True, exist_ok=True)
        names = list(measurements) if measurements is not None else self.measurements()
        written: List[Path] = []
        with self._client() as client:
            query_api = client.query_api()
            for name in names:
                query = f'''
from(bucket: "{info.bucket}")
  |> range(start: {start}, stop: {stop})
  |> filter(fn: (r) => r._measurement == "{name}")
'''
                csv = query_api.query_raw(query, org=info.organization)
                if hasattr(csv, "read"):
                    csv = csv.read()
                if isinstance(csv, bytes):
                    csv = csv.decode("utf-8", errors="replace")
                # An empty result is a couple of blank lines; don't leave a
                # file behind that looks like data.
                if not csv.strip():
                    continue
                path = dest / f"{name}.csv"
                path.write_text(csv)
                written.append(path)
        return written


class Telegraf(object):
    """Runs the Telegraf metric collection tool on a single node.

    To run Telegraf across multiple nodes, construct one instance per node
    (and fan out via util.fan_out). Per-node toggles like the Jolokia and
    execd inputs are constructor flags rather than runtime add_input calls.
    """

    DEFAULT_IMAGE_URL = "docker://telegraf:1.37-alpine"

    def __init__(
        self,
        node: Node,
        name: str = "telegraf",
        image_url: str = DEFAULT_IMAGE_URL,
        jolokia: bool = False,
        jolokia_port: int = JOLOKIA_PORT,
        execd_minecraft_ticks: bool = False,
    ):
        """Configure a Telegraf agent for one node.

        Args:
            node: The node on which to run Telegraf.
            name: Apptainer instance name. Override it to run more than one
                agent on a node, or to avoid clashing with another user's
                instance on a shared node.
            image_url: Container image to run. Defaults to the upstream
                Telegraf image on Docker Hub.
            jolokia: If True, render a `jolokia2_agent` input pointing at
                the Jolokia agent on this node.
            jolokia_port: Port the Jolokia agent is listening on; must match
                the server's `jolokia_port`.
            execd_minecraft_ticks: If True, ship the
                jolokia_get_minecraft_tick Go binary to the node's wd and
                bind-mount it into the Telegraf container at
                /opt/jolokia_get_minecraft_tick, where the rendered execd
                input plugin will run it.
        """
        self.node = node
        self.name = name
        self.image_url = image_url
        self.jolokia = jolokia
        self.jolokia_port = jolokia_port
        self.execd_minecraft_ticks = execd_minecraft_ticks
        self.influxdb_info: Optional[InfluxDBInfo] = None
        self.config_template = os.path.join(
            os.path.dirname(__file__), "telegraf.conf.j2"
        )
        self.wd = f"{node.wd}/{name}-{random_string(8)}"

    def set_output_influxdb2(self, info: InfluxDBInfo) -> None:
        self.influxdb_info = info

    def deploy(self) -> None:
        if self.influxdb_info is None:
            raise RuntimeError(
                "Telegraf has no output configured; call "
                "set_output_influxdb2(influxdb.get_info()) before deploy()"
            )
        mc_ticks_binary = Path(__file__).parent / "jolokia_get_minecraft_tick"
        with remote(self.node.host) as machine:
            with open(self.config_template) as f:
                template = Template(f.read())
            fd, name = tempfile.mkstemp()

            with os.fdopen(fd, mode="w+t") as out:
                out.write(
                    template.render(
                        outputs_influxdb_v2=True,
                        outputs_influxdb_v2_urls=self.influxdb_info.urls,
                        outputs_influxdb_v2_token=self.influxdb_info.token,
                        outputs_influxdb_v2_organization=self.influxdb_info.organization,
                        outputs_influxdb_v2_bucket=self.influxdb_info.bucket,
                        jolokia=self.jolokia,
                        jolokia_url=f"http://localhost:{self.jolokia_port}/jolokia",
                        jolokia_to_mc_ticks_script=self.execd_minecraft_ticks,
                    )
                )

            stage(machine, name, f"{self.wd}/telegraf.conf")
            os.remove(name)

            if self.execd_minecraft_ticks:
                # stage() carries the binary's executable bit over to the
                # node (scp would otherwise drop it), so Telegraf's execd
                # input can run it straight from the bind mount.
                stage(
                    machine,
                    mc_ticks_binary,
                    f"{self.wd}/jolokia_get_minecraft_tick",
                )

    def start(self) -> None:
        with remote(self.node.host) as machine:
            binds = [f"{self.wd}/telegraf.conf:/etc/telegraf/telegraf.conf"]
            if self.execd_minecraft_ticks:
                binds.append(
                    f"{self.wd}/jolokia_get_minecraft_tick:/opt/jolokia_get_minecraft_tick"
                )
            bind_args: List[str] = []
            for bind in binds:
                bind_args += ["--bind", bind]

            args = (
                ["instance", "run", "--no-https", "--compat"]
                + bind_args
                + [self.image_url, self.name]
            )
            machine["apptainer"][args]()

    def stop(self) -> None:
        with remote(self.node.host) as machine:
            machine["apptainer"]["instance", "stop", self.name].run(retcode=None)

    def cleanup(self) -> None:
        with remote(self.node.host) as machine:
            machine["rm"]["-rf", self.wd](retcode=None)
