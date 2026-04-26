# Experiments

Cookbook-style notebooks. Each notebook is a self-contained experiment:
deploy a configuration, run a workload, query InfluxDB, plot something.

## Naming

`<plotted_metric>[_vs_<sweep_variable>].ipynb`

- `tick_latency.ipynb` — single configuration, plotted over time.
- `tick_latency_vs_bot_count.ipynb` — sweep bot count, line per value.
- `tick_latency_vs_game.ipynb` — compare games (when more than one exists).
- `cpu_utilization_vs_node_count.ipynb` — multi-node setup, plot CPU vs N.

The configuration that's held *constant* for a notebook (which game, which
workload, hardware, etc.) is described in the notebook's intro markdown,
since the filename only carries the variable axis.

## Running a notebook

The base `yardstick-benchmark` install doesn't pull in matplotlib /
pandas / ipykernel. Install the `notebooks` extra:

```sh
uv sync --extra notebooks
```

Pick a frontend:

- **VS Code**: open any `experiments/*.ipynb`. When prompted, select the
  `.venv/bin/python` interpreter (the one matching this project). VS Code
  may also prompt to install `pip` into the venv -- click *Install* (uv
  doesn't seed pip into venvs by default; pip is what the editor uses to
  manage kernel installs).
- **JupyterLab / Notebook**: install one and launch:

  ```sh
  uv pip install jupyterlab          # or `jupyter notebook`
  uv run jupyter lab experiments/tick_latency.ipynb
  ```

Run cells top-to-bottom. The deploy/run cell takes a few minutes (image
pulls on first run, Minecraft boot, workload duration, plus a Telegraf
flush margin). The query cell captures the data into a DataFrame *before*
teardown, so the plot cell can be re-run independently -- iterate on
matplotlib styling without re-running the whole experiment.

## Shared helpers

`_lib.py` holds helpers used across notebooks (currently:
`query_influxdb_dataframe(influxdb, flux)` returns a pandas DataFrame).
The leading underscore signals "private to this folder, not part of the
`yardstick_benchmark` public API". Jupyter prepends each notebook's
directory to `sys.path` automatically, so `from _lib import ...` works
without further setup.

## Adding a new experiment

The standard structure (see `tick_latency.ipynb` for a concrete example):

1. **Intro markdown.** What's the configuration, what's being measured,
   what's the sweep (if any).
2. **Setup cell.** Imports + parameters as module-level constants
   (`NODE`, `WORKLOAD_DURATION`, `BOTS`, etc.).
3. **Run cell.** Deploy + start everything in a `try`, run the workload,
   capture the InfluxDB data into a DataFrame variable *inside* the try,
   tear down in `finally`. Capturing inside the try is what makes the
   plot cell re-runnable.
4. **Plot cell(s).** Pure DataFrame -> matplotlib. No deployment side
   effects here.

For a comparison (`_vs_X`) experiment the run cell becomes a loop over
the sweep values; tag the InfluxDB writes with the sweep value (e.g. via
a Telegraf `[global_tags]` entry rendered into the config) so a single
Flux query returns all runs grouped by the sweep variable.
