from yardstick_benchmark.model import Node
from yardstick_benchmark.util import random_string, remote, upload
import os
from typing import Dict, List, Optional
from jinja2 import Template
import tempfile
from pathlib import Path
from dataclasses import dataclass

from influxdb_client.client.influxdb_client import InfluxDBClient


@dataclass(frozen=True)
class InfluxDBInfo:
    urls: List[str]
    token: str
    organization: str = "yardstick"
    bucket: str = "yardstick"


class InfluxDB(object):
    """A single InfluxDB v2 deployment on one node.

    To run multiple independent InfluxDB instances (rare), construct one
    `InfluxDB` per target node. To have several Telegraf agents write to the
    *same* InfluxDB, share the same instance's `get_info()` with each Telegraf.
    """

    def __init__(
        self,
        node: Node,
        admin_password: str = "password",
        admin_token: Optional[str] = None,
    ):
        self.node = node
        self.image_url = "docker://influxdb:2.8"
        self.admin_password = admin_password
        self.admin_token = admin_token or random_string(16)
        # Persist InfluxDB's data to a host dir bind-mounted into the container
        # (at /var/lib/influxdb2), so it survives container stop/start and
        # kernel restarts instead of vanishing with the container's tmpfs.
        # Lives under the node's working dir; remove it with cleanup().
        self.data_dir = f"{node.wd}/influxdb-data"

    @property
    def url(self) -> str:
        return f"http://{self.node.host}:8086"

    def deploy(self) -> None:
        with remote(self.node.host):
            pass
            # machine["apptainer"]["pull", "/dev/null", self.image_url]()
            # TODO save local storage of database in some local file that we can pull before cleanup.

    def start(self) -> None:
        with remote(self.node.host) as machine:
            # Stage the persistent data dir on the node; the influxdb image
            # skips first-time setup when this already holds an initialised DB,
            # so restarts reuse prior data.
            machine["mkdir"]["-p", self.data_dir]()
            machine["apptainer"][
                "instance",
                "run",
                "--compat",
                "--bind",
                f"{self.data_dir}:/var/lib/influxdb2",
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
                self.image_url,
                "influxdb",
            ]()

    def stop(self) -> None:
        with remote(self.node.host) as machine:
            machine["apptainer"]["instance", "stop", "influxdb"]()

    def cleanup(self) -> None:
        """Delete the persistent data dir (call after stop() to wipe the DB)."""
        with remote(self.node.host) as machine:
            machine["rm"]["-rf", self.data_dir](retcode=None)

    def get_info(self) -> InfluxDBInfo:
        return InfluxDBInfo([self.url], self.admin_token)

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
        with InfluxDBClient(url=self.url, token=info.token, org=info.organization) as client:
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
        image_url: str = DEFAULT_IMAGE_URL,
        jolokia: bool = False,
        execd_minecraft_ticks: bool = False,
    ):
        """Configure a Telegraf agent for one node.

        Args:
            node: The node on which to run Telegraf.
            image_url: Container image to run. Defaults to the upstream
                Telegraf image on Docker Hub.
            jolokia: If True, render a `jolokia2_agent` input pointing at
                `localhost:8778` (matches MinecraftServer's default Jolokia
                port).
            execd_minecraft_ticks: If True, ship the
                jolokia_get_minecraft_tick Go binary to the node's wd and
                bind-mount it into the Telegraf container at
                /opt/jolokia_get_minecraft_tick, where the rendered execd
                input plugin will run it.
        """
        self.node = node
        self.image_url = image_url
        self.jolokia = jolokia
        self.execd_minecraft_ticks = execd_minecraft_ticks
        self.config_template = os.path.join(
            os.path.dirname(__file__), "telegraf.conf.j2"
        )
        self.wd = f"{node.wd}/telegraf-{random_string(8)}"

    def set_output_influxdb2(self, info: InfluxDBInfo) -> None:
        self.influxdb_info = info

    def deploy(self) -> None:
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
                        jolokia_to_mc_ticks_script=self.execd_minecraft_ticks,
                    )
                )

            # scp (the remote upload path) won't create the wd, so make it
            # first; upload() scp's the file when the node is remote.
            machine["mkdir"]["-p", self.wd]()
            dst = f"{self.wd}/telegraf.conf"
            upload(machine, name, dst)
            os.remove(name)

            if self.execd_minecraft_ticks:
                dst = f"{self.wd}/jolokia_get_minecraft_tick"
                upload(machine, mc_ticks_binary, dst)
                machine["chmod"]["+x", dst]()

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
                + [self.image_url, "telegraf"]
            )
            machine["apptainer"][args]()

    def stop(self) -> None:
        with remote(self.node.host) as machine:
            machine["apptainer"]["instance", "stop", "telegraf"]()

    def cleanup(self) -> None:
        with remote(self.node.host) as machine:
            machine["rm"]["-rf", self.wd](retcode=None)
