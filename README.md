# Yardstick Gaming Benchmark

Yardstick is a benchmark for Modifiable Virtual Environments (MVEs) such as
Minecraft. It deploys a game server, runs a workload of emulated players
against it, collects performance metrics, and writes them out for analysis.

New to this? Start with the [tutorial](docs/tutorial.md).

## Requirements

- [apptainer](https://apptainer.org/) on every machine that runs a component.
  Everything -- game server, database, metrics agent, emulated players --
  runs in an unmodified upstream container image, so there is nothing to
  build or install beyond apptainer itself.
- [uv](https://docs.astral.sh/uv/getting-started/installation/) to manage
  Python and dependencies.

> [!IMPORTANT]
> Yardstick currently runs everything on `localhost`. Staging files to a
> remote node is not implemented (see `yardstick_benchmark.util.stage`), so a
> configuration naming other hosts will fail with an explicit error. The
> single-machine path is complete and is what the tutorial uses.

## Install

```sh
git clone https://github.com/atlarge-research/yardstick
cd yardstick
uv sync --extra notebooks
```

The `notebooks` extra adds matplotlib, pandas, seaborn, ipykernel and
nbstripout; leave it off for a deployment that only needs to run benchmarks.

## Running a benchmark

There are two ways in, depending on how much you want to change.

### From a configuration file

For the standard run -- one game, one workload, metrics written out -- write
a TOML file:

```sh
uv run yardstick init experiment.toml    # write a commented starter config
uv run yardstick validate experiment.toml
uv run yardstick run experiment.toml
```

A configuration looks like this:

```toml
[deployment]
hosts = ["localhost"]
wd = "/tmp/yardstick"

[game]
type = "minecraft"
seed = "yardstick"        # pin the world so runs are comparable
max_players = 100
simulation_distance = 10

[workload]
type = "worldgen"
bots_per_node = 8
teleports = 32

[output]
dir = "results"
```

Keys other than `type` go straight to the corresponding class's constructor,
so everything the Python API exposes is configurable here. A misspelled
option is rejected immediately, with the list of names that would have
worked. Durations accept `"90s"`, `"5m"`, `"1h"` or a plain number of
seconds.

`uv run yardstick list` shows the built-in games and workloads. `type` also
takes a dotted import path, so a class of your own needs no registration:

```toml
[workload]
type = "mypackage.workloads.MyWorkload"
```

Results land in `results/<workload>-<timestamp>/`: one CSV per measurement,
plus a `run.json` manifest recording the configuration, timings and files
produced. Load a measurement with:

```python
import pandas as pd
df = pd.read_csv("results/worldgen-20260919-101500/minecraft_tick.csv", comment="#")
```

### From Python

For an experiment the configuration file doesn't cover -- sweeping a
parameter, comparing configurations, adding a component -- compose the
deployment yourself. Every component has the same lifecycle (`deploy`,
`start`, `stop`, `cleanup`), and `Deployment` runs it for a group of them in
order, guaranteeing teardown:

```python
from pathlib import Path
from yardstick_benchmark.deployment import Deployment
from yardstick_benchmark.games.minecraft.server import MinecraftServer
from yardstick_benchmark.games.minecraft.workload import WorldGeneration
from yardstick_benchmark.model import Node
from yardstick_benchmark.monitoring import InfluxDB, Telegraf

node = Node("localhost", Path("/tmp/yardstick"))

influxdb = InfluxDB(node)
telegraf = Telegraf(node, jolokia=True, execd_minecraft_ticks=True)
telegraf.set_output_influxdb2(influxdb.get_info())
server = MinecraftServer(node, seed="yardstick", simulation_distance=10)

with Deployment(influxdb, server, telegraf):
    server.set_world_spawn(0, 0)
    server.start_health_monitor()

    workload = WorldGeneration(
        node,
        server_host=node.host,
        influxdb_info=influxdb.get_info(),
        rcon_password=server.rcon_password,
        bots_per_node=8,
    )
    workload.deploy()
    try:
        workload.run(health_check=server.assert_healthy)
    finally:
        workload.cleanup()

    influxdb.export_csv(Path("results/my-run"))
```

Components come up in the order given and go down in reverse, so list them in
dependency order. Teardown runs whatever happens, including a failure partway
through startup. Export results *inside* the block: teardown stops the
database and removes its storage.

`example.py` is this, end to end and runnable.
`yardstick_benchmark/runner.py` is the same thing driven by a configuration
file, and is meant to be read.

Adding a component of your own needs no registration either -- anything with
`deploy`/`start`/`stop`/`cleanup` can join a `Deployment`. An optional
`ready()` is awaited after `start()`.

### From a notebook

`experiments/` holds cookbook-style notebooks that deploy, run, query and
plot in one place. See [experiments/README.md](experiments/README.md) for how
to run and add them.

## What gets measured

- **System metrics** (CPU, memory, disk, network) from Telegraf's standard
  inputs, on every node.
- **JVM metrics** (heap, GC, threads) from the game server, scraped over the
  Jolokia agent that Yardstick bind-mounts into the server container.
- **Minecraft tick durations**, sampled by a small Go collector
  (`yardstick_benchmark/monitoring/jolokia_get_minecraft_tick.go`) that
  Telegraf runs as an `execd` input. This is the headline server-performance
  metric.
- **Workload metrics** written directly by the emulated players, for
  workloads that produce them -- `worldgen` records per-player and
  per-teleport world-generation latency.

Everything lands in InfluxDB during a run and is exported to CSV at the end.

## Development

```sh
uv run pytest -m "not slow"   # fast tests: no containers, no network
uv run pytest -m slow         # integration tests; needs apptainer
uv run ruff check .
uv run ruff format .
```

CI runs the fast tests, lint and format checks, verifies notebooks are
committed without outputs, and compiles the Go collector.

### Notebook outputs

Committed notebooks are stored **without** cell outputs. This is automated
with [nbstripout](https://github.com/kynan/nbstripout) as a git filter, which
is configured per clone -- enable it once after cloning:

```sh
uv run nbstripout --install --attributes .gitattributes
```

Your working copy keeps its outputs; only the staged copy is stripped.

### The Go tick collector

It is committed as a compiled binary, because Telegraf runs it inside an
unmodified upstream container. After changing the source:

```sh
cd yardstick_benchmark/monitoring && make build
```

and commit the rebuilt binary.
