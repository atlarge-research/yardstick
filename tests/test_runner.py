"""The configuration-file runner, exercised with fake components.

The runner is what turns a TOML file into a benchmark, so its wiring is worth
testing: which components get built, in what order they're brought up, what
the workload is told about the server, and whether results are exported
before teardown removes the database. None of that needs a container.
"""

import json
from pathlib import Path

import pytest

from yardstick_benchmark import runner
from yardstick_benchmark.config import BenchmarkConfig
from yardstick_benchmark.model import Node


class FakeComponent:
    """Records lifecycle calls into a shared list."""

    def __init__(self, log, label):
        self._log = log
        self._label = label

    def deploy(self):
        self._log.append(f"{self._label}.deploy")

    def start(self):
        self._log.append(f"{self._label}.start")

    def ready(self):
        self._log.append(f"{self._label}.ready")

    def stop(self):
        self._log.append(f"{self._label}.stop")

    def cleanup(self):
        self._log.append(f"{self._label}.cleanup")


#: Populated by the fakes so tests can inspect what the runner built.
BUILT: dict = {}


class FakeGame(FakeComponent):
    def __init__(self, node, **options):
        super().__init__(BUILT["log"], "game")
        self.node = node
        self.options = options
        self.rcon_password = "hunter2"
        self.game_port = 25565
        self.rcon_port = 25575
        self.jolokia_port = 8778
        self.version = "1.21.11"
        BUILT["game"] = self

    def set_world_spawn(self, x, z):
        self._log.append(f"game.set_world_spawn({x},{z})")

    def start_health_monitor(self):
        self._log.append("game.health_monitor")

    def stop_health_monitor(self):
        pass

    def assert_healthy(self):
        pass


class FakeWorkload:
    def __init__(self, node, **options):
        self.node = node
        self.options = options
        BUILT.setdefault("workloads", []).append(self)

    def deploy(self):
        BUILT["log"].append("workload.deploy")

    def run(self, health_check=None):
        BUILT["log"].append("workload.run")
        assert health_check is not None, "the server health check must be wired up"

    def cleanup(self):
        BUILT["log"].append("workload.cleanup")


class FakeInfo:
    bucket = "yardstick"
    organization = "yardstick"
    urls = ["http://localhost:8086"]
    token = "token"


class FakeInfluxDB(FakeComponent):
    def __init__(self, node, **kwargs):
        super().__init__(BUILT["log"], "influxdb")
        self.node = node
        self.exported = None
        self.info = FakeInfo()
        BUILT["influxdb"] = self

    def get_info(self):
        return self.info

    # The saturation check queries the database directly; answer with no
    # rows, which it reports as "could not check" rather than as healthy.
    def _client(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def query_api(self):
        return self

    def query(self, query=None, org=None):
        BUILT.setdefault("queries", []).append(query)
        return []

    def export_csv(self, dest, start=None, stop=None):
        self._log.append("influxdb.export_csv")
        dest.mkdir(parents=True, exist_ok=True)
        path = dest / "cpu.csv"
        path.write_text("#group,false\n")
        self.exported = dest
        return [path]


class FakeTelegraf(FakeComponent):
    def __init__(self, node, **options):
        super().__init__(BUILT["log"], f"telegraf[{node.host}]")
        self.node = node
        self.options = options
        BUILT.setdefault("telegrafs", []).append(self)

    def set_output_influxdb2(self, info):
        self.output = info


@pytest.fixture(autouse=True)
def fakes(monkeypatch):
    BUILT.clear()
    BUILT["log"] = []
    monkeypatch.setattr(runner, "InfluxDB", FakeInfluxDB)
    monkeypatch.setattr(runner, "Telegraf", FakeTelegraf)
    yield BUILT


def _config(tmp_path, extra="", hosts='["localhost"]'):
    text = f"""
[deployment]
hosts = {hosts}
wd = "{tmp_path / "wd"}"

[game]
type = "tests.test_runner.FakeGame"
max_players = 50

[workload]
type = "tests.test_runner.FakeWorkload"
bots_per_node = 4

[output]
dir = "{tmp_path / "results"}"
{extra}
"""
    path = tmp_path / "experiment.toml"
    path.write_text(text)
    return BenchmarkConfig.from_toml(path)


def test_run_brings_components_up_and_exports_before_teardown(tmp_path):
    results = runner.run(_config(tmp_path))
    log = BUILT["log"]

    # The database must be up before Telegraf, and the server before the
    # workload connects to it.
    assert log.index("influxdb.start") < log.index("telegraf[localhost].start")
    assert log.index("game.start") < log.index("workload.run")
    # Results must be exported while the database is still running.
    assert log.index("influxdb.export_csv") < log.index("influxdb.stop")
    # Everything comes down again.
    assert "game.stop" in log and "influxdb.stop" in log
    assert results.exists()


def test_game_options_from_the_config_reach_the_game(tmp_path):
    runner.run(_config(tmp_path))
    assert BUILT["game"].options["max_players"] == 50


def test_workload_is_told_how_to_reach_the_server(tmp_path):
    runner.run(_config(tmp_path))
    options = BUILT["workloads"][0].options
    assert options["server_host"] == "localhost"
    assert options["rcon_password"] == "hunter2"
    assert options["influxdb_info"] is BUILT["influxdb"].info
    assert options["bots_per_node"] == 4


def test_a_manifest_records_what_was_run(tmp_path):
    results = runner.run(_config(tmp_path))
    manifest = json.loads((results / "run.json").read_text())
    assert manifest["total_bots"] == 4
    assert manifest["server_host"] == "localhost"
    assert manifest["files"] == ["cpu.csv"]
    assert manifest["config"]["game"]["max_players"] == 50
    assert manifest["duration_s"] >= 0


def test_workload_is_cleaned_up_even_when_it_fails(tmp_path, monkeypatch):
    def boom(self, health_check=None):
        BUILT["log"].append("workload.run")
        raise RuntimeError("bots died")

    monkeypatch.setattr(FakeWorkload, "run", boom)
    with pytest.raises(RuntimeError, match="bots died"):
        runner.run(_config(tmp_path))
    log = BUILT["log"]
    assert "workload.cleanup" in log
    # ...and the whole deployment still came down.
    assert "game.stop" in log and "influxdb.stop" in log


def test_monitoring_can_be_switched_off(tmp_path):
    runner.run(_config(tmp_path, extra="\n[monitoring]\nenabled = false\n"))
    assert "telegrafs" not in BUILT


def test_keep_node_data_skips_cleanup(tmp_path):
    runner.run(_config(tmp_path, extra="keep_node_data = true"))
    assert "influxdb.stop" in BUILT["log"]
    assert "influxdb.cleanup" not in BUILT["log"]


def test_one_workload_per_player_node_with_distinct_indices(tmp_path):
    runner.run(_config(tmp_path, hosts='["127.0.0.1", "127.0.0.2", "127.0.0.3"]'))
    workloads = BUILT["workloads"]
    assert len(workloads) == 2
    assert [w.node.host for w in workloads] == ["127.0.0.2", "127.0.0.3"]
    assert sorted(w.options["bot_index"] for w in workloads) == [0, 1]
    # Every workload needs the global total so players can be spread out.
    assert {w.options["total_bots"] for w in workloads} == {8}


def test_telegraf_scrapes_jolokia_only_on_the_server_node(tmp_path):
    """The JVM only exists on the server's node; asking the other nodes'
    agents to scrape Jolokia would just log connection errors."""
    runner.run(_config(tmp_path, hosts='["127.0.0.1", "127.0.0.2"]'))
    by_host = {t.node.host: t.options for t in BUILT["telegrafs"]}
    assert by_host["127.0.0.1"]["jolokia"] is True
    assert by_host["127.0.0.2"]["jolokia"] is False
    assert by_host["127.0.0.2"]["execd_minecraft_ticks"] is False


class FakePool:
    """Stands in for a Provisioner in cloud/cluster mode."""

    def __init__(self, **options):
        self.options = options
        self.released = []
        self.ledger = type("L", (), {"path": "/tmp/ledger.json"})()
        BUILT.setdefault("pools", []).append(self)

    def provision(self, num, wd=None):
        base = len(BUILT.setdefault("provisioned", []))
        nodes = [
            Node(f"198.51.100.{base + i}", Path(wd or "/home/ubi/yardstick"))
            for i in range(num)
        ]
        BUILT["provisioned"].extend(nodes)
        return nodes

    def release(self, nodes):
        self.released.extend(nodes)
        BUILT.setdefault("released", []).extend(nodes)


def _cloud_config(tmp_path, extra=""):
    text = f"""
[deployment]
mode = "cloud"
wd = "/home/ubi/yardstick"

[provisioning]
provider = "tests.test_runner.FakePool"
workload_nodes = 2

[game]
type = "tests.test_runner.FakeGame"

[workload]
type = "tests.test_runner.FakeWorkload"
bots_per_node = 2

[output]
dir = "{tmp_path / "results"}"
{extra}
"""
    path = tmp_path / "cloud.toml"
    path.write_text(text)
    return BenchmarkConfig.from_toml(path)


def test_cloud_mode_provisions_a_server_and_workload_machines(tmp_path):
    runner.run(_cloud_config(tmp_path))
    provisioned = BUILT["provisioned"]
    assert len(provisioned) == 3, "one server plus two workload machines"
    # The game server gets a machine to itself, so players never compete with
    # it for CPU.
    assert BUILT["game"].node.host == provisioned[0].host
    assert {w.node.host for w in BUILT["workloads"]} == {
        n.host for n in provisioned[1:]
    }


def test_cloud_mode_releases_every_machine_afterwards(tmp_path):
    runner.run(_cloud_config(tmp_path))
    assert len(BUILT["released"]) == 3


def test_cloud_machines_are_released_even_when_the_run_fails(tmp_path, monkeypatch):
    """A leaked VM bills until someone notices."""

    def boom(self, health_check=None):
        raise RuntimeError("workload exploded")

    monkeypatch.setattr(FakeWorkload, "run", boom)
    with pytest.raises(RuntimeError, match="exploded"):
        runner.run(_cloud_config(tmp_path))
    assert len(BUILT["released"]) == 3, "machines must be given back regardless"


def test_server_and_workload_groups_get_their_own_provisioner_options(tmp_path):
    config = _cloud_config(
        tmp_path,
        extra="\n[provisioning.server]\nsize = 'big'\n"
        "\n[provisioning.workload]\nsize = 'small'\n",
    )
    runner.run(config)
    # validate() constructs each provider too, to run its own guards, so the
    # pools that actually provisioned are the last two.
    sizes = [pool.options.get("size") for pool in BUILT["pools"][-2:]]
    assert sizes == ["big", "small"]


def test_saturation_is_checked_and_recorded_in_the_manifest(tmp_path):
    results = runner.run(_config(tmp_path))
    manifest = json.loads((results / "run.json").read_text())
    assert "workload_saturation" in manifest
    # The fake database returns no rows, which must read as "could not
    # check" rather than as a clean bill of health.
    assert manifest["workload_saturation"]["checked"] is False
    assert manifest["workload_saturation"]["ok"] is False


def test_telegraf_tags_identify_the_node_and_its_role(tmp_path):
    runner.run(_config(tmp_path, hosts='["127.0.0.1", "127.0.0.2"]'))
    tags = {t.node.host: t.options["tags"] for t in BUILT["telegrafs"]}
    assert tags["127.0.0.1"]["yardstick_role"] == "server"
    assert tags["127.0.0.2"]["yardstick_role"] == "workload"
    assert tags["127.0.0.2"]["yardstick_node"] == "127.0.0.2"
