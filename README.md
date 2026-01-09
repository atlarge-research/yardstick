
# Yardstick Gaming Benchmark

Yardstick is a benchmark for Modifiable Virtual Environments (MVEs).
Learn how to benchmark your MVE by reading the [tutorial](docs/tutorial.md).

## Usage

To run Yardstick in your own environment, you can:

1. [Run the provided workloads](#run-provided-workloads).
2. [Build your own workloads](#build-your-own-workloads).

Both approaches are explained below.

### Run Provided Workloads

1. Install the `uv` python package manager by following the official instructions: https://docs.astral.sh/uv/getting-started/installation/
2. Clone this repository into `yardstick`
3. In the `yardstick` directory, run `uv sync` to install dependencies.
4. Open `example.ipynb` in [VSCode](https://code.visualstudio.com/) and install the necessary plugins for running Jupyter Notebooks. VSCode should suggest the necessary plugins automatically.
5. Run all cells.

### Build Your Own Workloads

1. Create your own Python project. 
2. Add `yardstick-benchmark` to the dependencies of your project.
2. Configure and run your workloads using Python!
