"""Every apptainer bind source must be a path on the *node*.

Components run containers on a remote machine but are constructed on the
machine running Yardstick, so it is easy to bind-mount a file that exists
only here -- a jar or a binary shipped inside this Python package. That works
perfectly in local mode and fails on a real remote node with an opaque
"mount source doesn't exist", minutes into a run.

This is exactly how the Jolokia agent bug got as far as a provisioned VM:
MinecraftServer.start() bound the jar straight from the installed package
path, which the node had never seen.
"""

from datetime import timedelta
from pathlib import Path

import pytest

from yardstick_benchmark.games.minecraft.server import MinecraftServer
from yardstick_benchmark.games.minecraft.workload import WalkAround, WorldGeneration
from yardstick_benchmark.model import Node
from yardstick_benchmark.monitoring import InfluxDB, InfluxDBInfo, Telegraf


NODE_WD = "/remote/wd"


def _bind_sources(args):
    """Source paths from every `--bind src:dst` pair in an argument list."""
    sources = []
    for index, arg in enumerate(args):
        if arg == "--bind" and index + 1 < len(args):
            sources.append(str(args[index + 1]).split(":", 1)[0])
    return sources


def _components(node):
    influx_info = InfluxDBInfo(["http://10.0.0.1:8086"], "token")
    telegraf = Telegraf(node, jolokia=True, execd_minecraft_ticks=True)
    telegraf.set_output_influxdb2(influx_info)
    return [
        MinecraftServer(node, name="mc"),
        InfluxDB(node),
        telegraf,
        WalkAround(node, server_host="10.0.0.1", duration=timedelta(seconds=5)),
        WorldGeneration(
            node,
            server_host="10.0.0.1",
            influxdb_info=influx_info,
            rcon_password="secret",
        ),
    ]


def _args_for(component):
    """The container arguments a component would run, without running them."""
    if isinstance(component, MinecraftServer):
        captured = {}

        class FakeMachine:
            def __getitem__(self, name):
                # start() reads /proc/meminfo to size the JVM heap from the
                # node's own RAM, so the fake has to answer that.
                output = "MemTotal:       16000000 kB\n" if name == "cat" else ""

                class Cmd:
                    def __getitem__(self, args):
                        captured["args"] = list(args)
                        return self

                    def __call__(self, *a, **k):
                        return output

                return Cmd()

        # Only the argument list matters here, not the side effects.
        import yardstick_benchmark.games.minecraft.server as server_module

        real_remote, real_stage = server_module.remote, server_module.stage
        server_module.stage = lambda *a, **k: None

        from contextlib import contextmanager

        @contextmanager
        def fake_remote(host, user=None):
            yield FakeMachine()

        server_module.remote = fake_remote
        try:
            component.start()
        finally:
            server_module.remote, server_module.stage = real_remote, real_stage
        return captured.get("args", [])
    if hasattr(component, "_container_args"):
        return component._container_args()
    if hasattr(component, "_bind_args"):
        return component._bind_args()
    return []


@pytest.mark.parametrize("index", range(5))
def test_bind_sources_live_on_the_node(index):
    node = Node("10.0.0.2", Path(NODE_WD), user="ubi")
    component = _components(node)[index]
    args = _args_for(component)
    sources = _bind_sources(args)
    assert sources, f"{type(component).__name__} binds nothing; check the probe"
    for source in sources:
        assert source.startswith(NODE_WD), (
            f"{type(component).__name__} bind-mounts {source!r}, which is a "
            f"path on the machine running Yardstick, not on the node. It has "
            f"to be staged under node.wd first."
        )


def test_minecraft_server_stages_the_jolokia_agent():
    """The agent ships inside this package, so the node only has it if we
    put it there."""
    node = Node("10.0.0.2", Path(NODE_WD), user="ubi")
    server = MinecraftServer(node, name="mc")
    assert server.jolokia_jar.startswith(NODE_WD)

    staged = []
    import yardstick_benchmark.games.minecraft.server as server_module

    real_stage = server_module.stage
    server_module.stage = lambda machine, src, dst: staged.append((str(src), dst))

    class FakeMachine:
        def __getitem__(self, name):
            class Cmd:
                def __getitem__(self, args):
                    return self

                def __call__(self, *a, **k):
                    return ""

            return Cmd()

    try:
        server._stage(FakeMachine())
    finally:
        server_module.stage = real_stage

    assert staged, "deploy() must copy the agent to the node"
    src, dst = staged[0]
    assert src.endswith(".jar")
    assert dst == server.jolokia_jar
