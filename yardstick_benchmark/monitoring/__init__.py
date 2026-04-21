from yardstick_benchmark.model import Node
from yardstick_benchmark.util import is_localhost, random_string
import os
from plumbum import local, SshMachine
from typing import Dict, List, Optional
from jinja2 import Template
import tempfile
from pathlib import Path
from dataclasses import dataclass

from influxdb_client import InfluxDBClient


@dataclass(frozen=True)
class InfluxDBInfo:
    urls: List[str]
    token: str
    organization: str = "yardstick"
    bucket: str = "yardstick"


class InfluxDB(object):
    def __init__(self, nodes: List[Node]):
        self.nodes = nodes
        self.image_url = "docker://influxdb:2.8"
        self.admin_password = "password"  # random_string(16)
        self.admin_token = random_string(16)

    def deploy(self) -> None:
        for node in self.nodes:
            host = node.host
            machine = SshMachine(host) if not is_localhost(host) else local
            try:
                pass
                # machine["apptainer"]["pull", "/dev/null", self.image_url]()
                # TODO save local storage of database in some local file that we can pull before cleanup.
            finally:
                if isinstance(machine, SshMachine):
                    machine.close()

    def start(self) -> None:
        for node in self.nodes:
            host = node.host
            machine = SshMachine(host) if not is_localhost(host) else local
            try:
                machine["apptainer"][
                    "instance",
                    "run",
                    "--compat",
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
            finally:
                if isinstance(machine, SshMachine):
                    machine.close()

    def stop(self) -> None:
        for node in self.nodes:
            host = node.host
            machine = SshMachine(host) if not is_localhost(host) else local
            try:
                machine["apptainer"]["instance", "stop", "influxdb"]()
            finally:
                if isinstance(machine, SshMachine):
                    machine.close()

    def cleanup(self) -> None:
        pass

    def get_info(self, nodes: List[Node]) -> InfluxDBInfo:
        return InfluxDBInfo(
            [f"http://{node.host}:8086" for node in nodes], self.admin_token
        )

    def verify_data(
        self,
        expected_measurements: Optional[List[str]] = None,
        lookback: str = "-5m",
        target_node: Optional[Node] = None,
    ) -> Dict[str, int]:
        info = self.get_info(self.nodes)
        target = target_node or self.nodes[0]
        url = f"http://{target.host}:8086"

        query = f'''
from(bucket: "{info.bucket}")
  |> range(start: {lookback})
  |> group(columns: ["_measurement"])
  |> count()
  |> keep(columns: ["_measurement", "_value"])
'''
        counts: Dict[str, int] = {}
        with InfluxDBClient(url=url, token=info.token, org=info.organization) as client:
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
    """Runs the Telegraf metric collection tool
    (https://www.influxdata.com/time-series-platform/telegraf/) on remote nodes.
    """

    DEFAULT_IMAGE_URL = "docker://telegraf:1.37-alpine"

    def __init__(
        self,
        nodes: List[Node],
        image_url: str = DEFAULT_IMAGE_URL,
    ):
        """Create a new instance to run Telegraf on the given nodes.

        Args:
            nodes (list[Node]): The nodes on which to run Telegraf
            image_url: Container image to run. Defaults to the upstream
                Telegraf image on Docker Hub. Override with e.g.
                ``"docker://localhost:5000/telegraf:1.37"`` to pull from a
                private registry instead.
        """
        self.nodes = nodes
        self.image_url = image_url
        self.config_template = os.path.join(
            os.path.dirname(__file__), "telegraf.conf.j2"
        )

        self.jolokia_to_mcticks_script_path = os.path.join(
            os.path.dirname(__file__), "jolokia_get_minecraft_tick.py"
        )

        self.wds = {}
        for node in nodes:
            self.wds[node] = f"{node.wd}/telegraf-{random_string(8)}"

        # TODO we do nothing with these settings at the moment
        self.config_nodes_jolokia_enabled = set()
        self.config_nodes_jolokia_mc_ticks_enabled = set()

    def add_input_jolokia_agent(self, node: Node):
        """Configure Telegraf to run the Jolokia agent input on the given node.
        The node should be present in the list of nodes given when constructing
        this Telegraf object.

        Args:
            node (Node): The node on which to run the Jolokia agent input
        """
        assert node in self.nodes
        self.config_nodes_jolokia_enabled.add(node)

    def add_input_execd_minecraft_ticks(self, node: Node):
        """Configure Telegraf to run an execd input on the given node to collect
        the tick duration metric from a Minecraft server.

        Args:
            node (Node): The node on which to run the execd input
        """
        assert node in self.nodes
        self.config_nodes_jolokia_mc_ticks_enabled.add(node)

    def set_output_influxdb2(self, info: InfluxDBInfo) -> None:
        self.influxdb_info = info

    def deploy(self) -> None:
        mc_ticks_binary = Path(__file__).parent / "jolokia_get_minecraft_tick"
        for node in self.nodes:
            host = node.host
            machine = SshMachine(host) if not is_localhost(host) else local
            try:
                with open(self.config_template) as f:
                    template = Template(f.read())
                fd, name = tempfile.mkstemp()

                jolokia = node in self.config_nodes_jolokia_enabled
                jolokia_to_mc_ticks_script = (
                    node in self.config_nodes_jolokia_mc_ticks_enabled
                )
                with os.fdopen(fd, mode="w+t") as out:
                    out.write(
                        template.render(
                            outputs_influxdb_v2=True,
                            outputs_influxdb_v2_urls=self.influxdb_info.urls,
                            outputs_influxdb_v2_token=self.influxdb_info.token,
                            outputs_influxdb_v2_organization=self.influxdb_info.organization,
                            outputs_influxdb_v2_bucket=self.influxdb_info.bucket,
                            jolokia=jolokia,
                            jolokia_to_mc_ticks_script=jolokia_to_mc_ticks_script,
                        )
                    )

                dst = f"{self.wds[node]}/telegraf.conf"
                local.path(name).copy(machine.path(dst))
                os.remove(name)

                if jolokia_to_mc_ticks_script:
                    dst = f"{self.wds[node]}/jolokia_get_minecraft_tick"
                    local.path(mc_ticks_binary).copy(machine.path(dst))
                    machine["chmod"]["+x", dst]()
            finally:
                if isinstance(machine, SshMachine):
                    machine.close()

    def start(self) -> None:
        for node in self.nodes:
            host = node.host
            machine = SshMachine(host) if not is_localhost(host) else local
            try:
                wd = self.wds[node]
                binds = [f"{wd}/telegraf.conf:/etc/telegraf/telegraf.conf"]
                if node in self.config_nodes_jolokia_mc_ticks_enabled:
                    binds.append(
                        f"{wd}/jolokia_get_minecraft_tick:/opt/jolokia_get_minecraft_tick"
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
            finally:
                if isinstance(machine, SshMachine):
                    machine.close()

    def stop(self) -> None:
        for node in self.nodes:
            host = node.host
            machine = SshMachine(host) if not is_localhost(host) else local
            try:
                machine["apptainer"]["instance", "stop", "telegraf"]()
            finally:
                if isinstance(machine, SshMachine):
                    machine.close()

    def cleanup(self) -> None:
        for node in self.nodes:
            host = node.host
            machine = SshMachine(host) if not is_localhost(host) else local
            try:
                wd = self.wds[node]
                machine.path(wd[node]).delete()
            finally:
                if isinstance(machine, SshMachine):
                    machine.close()
