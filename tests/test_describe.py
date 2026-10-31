"""What a game server and a workload say about themselves for run.json.

The manifest is what gets shared, so these descriptions are allow-lists:
the tests pin that a secret or an address cannot appear in one, and that
values only known at runtime (heap size, world seed) are filled in.
"""

from datetime import timedelta
from pathlib import Path

from yardstick_benchmark.games.minecraft.server import MinecraftServer
from yardstick_benchmark.games.minecraft.workload.walkaround import WalkAround
from yardstick_benchmark.model import Node


def _server(**options):
    return MinecraftServer(Node("10.0.0.2", Path("/wd")), name="mc", **options)


def test_the_description_holds_no_secret_and_no_address():
    server = _server(rcon_password="hunter2")
    text = str(server.describe())
    assert "hunter2" not in text
    assert "10.0.0.2" not in text
    assert "mc" not in server.describe()


def test_a_configured_seed_is_recorded_as_it_was_given():
    assert _server(seed="1234").describe()["seed"] == "1234"


def test_the_seed_is_unknown_until_the_server_reports_it():
    assert _server().describe()["seed"] is None


def test_the_seed_is_read_back_from_the_server():
    server = _server()
    server.rcon = lambda *commands: "Seed: [-4172144997902289642]\n"
    server._learn_seed()
    assert server.describe()["seed"] == "-4172144997902289642"


def test_a_server_that_cannot_report_its_seed_does_not_fail_the_run():
    server = _server()

    def broken(*commands):
        raise RuntimeError("rcon refused")

    server.rcon = broken
    server._learn_seed()
    assert server.describe()["seed"] is None


def test_a_configured_seed_is_not_asked_for_again():
    server = _server(seed="7")
    server.rcon = lambda *commands: (_ for _ in ()).throw(AssertionError("asked"))
    server._learn_seed()


def test_an_explicit_heap_size_is_recorded():
    assert _server(memory="4G").describe()["memory"] == "4G"


def test_a_derived_heap_size_is_recorded_once_resolved():
    server = _server()

    class Cat:
        def __getitem__(self, path):
            return lambda: "MemTotal:  16777216 kB\n"

    server.resolved_memory = server._resolve_memory({"cat": Cat()})
    assert server.describe()["memory"] == "8192M"


def test_a_workload_describes_its_parameters_in_plain_units():
    node = Node("10.0.0.3", Path("/wd"))
    workload = WalkAround(
        node,
        server_host="10.0.0.2",
        duration=timedelta(seconds=90),
        bots_per_node=5,
    )
    described = workload.describe()
    assert described["type"] == "walkaround"
    assert described["duration_s"] == 90
    assert described["bots_per_node"] == 5
    assert "10.0.0.2" not in str(described)
