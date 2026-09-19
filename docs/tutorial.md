
# Yardstick Tutorial

Minecraft is one of the best-selling games of all time.
It has sold more than 200 million copies,<sup id="a1">[1](#fn1)</sup> and has more than 126 million active monthly players.<sup id="a2">[2](#fn2)</sup>
In contrast to traditional games, Minecraft gives players fine-grained control over the environment.
Players can be creative and alter the environment to their liking.
Players can decide to create buildings, mines, farms, logical circuits, and other constructions.
Minecraft's success has led to the creation of hundreds of similar games, which we collectively refer to as _Minecraft-like games_ (MLGs).

Unfortunately, it is difficult for MLG players to play together due to severe performance limitations.
The modifiable and complex virtual environment is difficult to scale to a large number of players,
resulting in virtual worlds whose scalability reaches only around 200 concurrent players under favorable conditions.
This is orders of magnitudes lower than today's most scalable worlds, such as EVE Online, which can scale to thousands of concurrent players in a single environment.
The only way MLG operators can support their high player numbers and sustain their high popularity is by
splitting players across a large number of small instances, preventing players from playing together in large groups.

In this tutorial, you make your first steps into exploring the performance of MLGs by running performance evaluation experiments with Yardstick,<sup id="a3">[3](#fn3)</sup><sup>,</sup><sup id="a4">[4](#fn4)</sup> our MLG benchmark.

## Setting Up

### SSH

We run the Yardstick benchmark on the [DAS-6 compute cluster](https://www.cs.vu.nl/das/) at the VU.
To connect to DAS-6, append the following configuration to your SSH configuration file, located at `~/.ssh/config`:

```
Host das6
	HostName fs0.das6.cs.vu.nl
	User DAS6_USERNAME
```

You should now be able to connect to the DAS-6 using the command `ssh das6`.
SSH will first request your VUnet password, and then your DAS-6 password.

> [!TIP]
> If you connect to the DAS-6 regularly, it is worth switching to public-key authentication using `ssh-keygen` and `ssh-copy-id`. This is left as an exercise for the reader.

> [!TIP]
> Use [eduVPN](https://www.eduvpn.org/client-apps/) to connet to the DAS-6 when you're not directly connected to the VU campus network.

### VSCode

We will work with a remote [Jupyter Notebook](https://jupyter.org/), which is easy to read and modify through [VSCode](https://code.visualstudio.com/).
If you have not done so already, install VSCode.
Next, use its "Connect to Host..." feature to connect VSCode to DAS6.

### Python Environment

Now that your VSCode is connected to DAS6, open a terminal (shortcut: `ctrl+~`).
We use [uv](https://docs.astral.sh/uv/) to manage Python and Yardstick's
dependencies. It installs as a single binary and needs no administrator rights:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Close (`ctrl+D`) and reopen (`ctrl+~`) your shell so `uv` is on your `PATH`.

> [!IMPORTANT]
> By default, users on DAS6 have limited storage space in their home
> directory, which the container images will exhaust. Point both uv's cache
> and apptainer's at your scratch directory before you start, and add these
> lines to your `~/.bashrc` so they apply to every new shell:
>
> ```bash
> export UV_CACHE_DIR=/var/scratch/`whoami`/uv-cache
> export APPTAINER_CACHEDIR=/var/scratch/`whoami`/apptainer-cache
> ```

Now get Yardstick and its dependencies:

```bash
git clone https://github.com/atlarge-research/yardstick
cd yardstick
uv sync --extra notebooks
```

That creates a `.venv` in the repository with everything the benchmark and
the example notebooks need. There is nothing else to install: the game
server, the metrics database, the metrics agent and the emulated players all
run as [apptainer](https://apptainer.org/) containers, which DAS6 already
provides.

Check that it worked:

```bash
uv run yardstick list
```

## Running Experiments

There are two ways to run Yardstick, and this tutorial uses both.

### Reserving a Node

DAS6 is a shared cluster. The machine you land on when you `ssh das6` is the
*head node*, which everyone shares and which you should never run a benchmark
on -- your measurements would be meaningless and you'd disrupt everyone
else's. Instead you reserve a compute node for yourself.

It is worth being precise about what runs where. Yardstick separates the
**control plane** -- the process that decides what to deploy and when -- from
the **data plane**, the machines actually running the game server, the
emulated players and the metrics stack. On a cluster, the intended
arrangement is Yardstick's `cluster` mode: control plane on the head node,
data plane on the worker nodes you reserved.

> [!NOTE]
> That mode is not implemented yet -- Yardstick cannot currently copy files
> onto a machine other than the one it runs on. So for this tutorial we use
> `local` mode and put *both* planes on a reserved worker node. The head node
> stays free, which is the part that matters.

Reserve a node for 30 minutes and log in to it:

```bash
preserve -np 1 -t 1800
preserve -llist
```

`preserve -llist` gives an overview of reservations on DAS6. You'll see a
line similar to the one below, with your username:

```
id      user            start           stop            state   nhosts  hosts
351651  core2435        06/21   07:02   06/21   07:18   R       2       node001 node015
```

This shows that user `core2435` has reserved 2 nodes: `node001` and `node015`
from 7:02am until 7:18am.

Which node did you reserve? How many nodes are in use by others? How many do
they use?

Once your reservation's state is `R`, connect to your node and go back to the
repository:

```bash
ssh node0XY
cd yardstick
```

> [!IMPORTANT]
> Your reservation ends at the time `preserve -llist` shows, and your
> processes are killed when it does. If a run stops abruptly, check whether
> your reservation expired -- and reserve more time than you think you need.

### Your First Run: a Configuration File

The quickest way to run a benchmark is to describe it in a file. From the
`yardstick` directory on your reserved node:

```bash
uv run yardstick init experiment.toml
```

Open `experiment.toml` and read it -- it is commented, and every setting in
it is one you may want to change later. Then check and run it:

```bash
uv run yardstick validate experiment.toml
uv run yardstick run experiment.toml -v
```

The first run takes a while (~10 minutes): it downloads the container images,
boots a Minecraft server, runs the workload, and collects metrics. This is
expected.

While it runs, open a second terminal on the same node and watch the
containers Yardstick started:

```bash
apptainer instance list
```

When the run finishes it prints a results directory. It contains one CSV per
measurement plus a `run.json` recording exactly what was run:

```bash
ls results/*/
cat results/*/run.json
```

### The Notebook

A configuration file is convenient, but for exploring results you want the
data and the plots in the same place. Open `experiments/tick_latency.ipynb`
in VSCode, connected to your reserved node. When prompted for a kernel, choose the `.venv/bin/python`
interpreter in the repository; VSCode may also offer to install the Jupyter
and Python extensions, which you should accept.

We recommend reading the notebook cell by cell to develop a sufficiently good
understanding of what is going on. Then run all cells.

When the experiment has completed, it is time to review the resulting plots.

Are the numbers surprising? Why (not)?

In the remainder of this section, we will ask you to perform increasingly difficult experiments,
which will make you increasingly adept at using Yardstick specifically, and performing experiments on a distributed system generally.

> [!NOTE]
> Here starts the challenging part of the tutorial. Each subsection can easily take 30 minutes to complete.
> If you are doing this tutorial as part of a lecture or workshop, there may not be sufficient time remaining to complete all exercises.
> This is by design. If you are out of time but remain curious about this work, feel free to explore the remaining sections from home. Your account is likely valid for several weeks.

### Visualize Another Metric

The notebook plots the server's tick duration, which is the headline measure
of how hard the server is working. It is far from the only thing collected:
Telegraf records CPU, memory, disk and network metrics for every node, and
the JVM's heap and garbage-collection behaviour for the server.

Run `uv run yardstick run experiment.toml` and look at the CSV files in the
results directory to see what is available. Then add a cell to the notebook
that plots another metric -- we recommend the network bandwidth usage of the
server node.

A measurement file loads into pandas with:

```python
import pandas as pd
df = pd.read_csv("results/<run>/net.csv", comment="#")
```

### Compare by Varying the Number of Players

Edit the notebook to run the experiment twice in a row with different numbers
of players, and plot both results on the same axes.

Does changing the number of players have an impact on the game's performance?

> [!TIP]
> `experiments/world_generation_time.ipynb` already does this -- it loops over
> several player counts in one run cell. Read it for the pattern.

### Compare by Changing the Game's Configuration

The server's *simulation distance* controls how many chunks around each
player the server actively ticks, so it directly affects how much work each
player creates. It is a setting on the game server:

```toml
[game]
simulation_distance = 4
```

Run the benchmark at a few different simulation distances and compare.

How does this distance affect the game's performance? Is the relationship
what you expected?

> [!TIP]
> Set `seed` in the `[game]` section so every run generates the same world.
> Without it, you are comparing runs over different terrain.

### Evaluate the Impact of Player Workloads

The first experiment uses a player workload called `WalkAround`, in which
players connect and walk around a predefined area. `WorldGeneration` is
another: players teleport to unexplored terrain and wait for the server to
generate it. Run both and compare -- `uv run yardstick list` shows what is
available, and you select one with:

```toml
[workload]
type = "worldgen"
```

How does the workload affect the game's performance? Why would world
generation stress a server differently from walking around?

### Write Your Own Workload

We suspect that the behavior of players can have a significant impact on the
game's performance. Write a workload of your own to find out.

A workload is a Python class plus the JavaScript its emulated players run.
Start from `yardstick_benchmark/games/minecraft/workload/walkaround/`: it is
about a hundred lines, and the base class in `workload/base.py` documents
what a subclass has to supply. Your class does not need to be registered
anywhere -- name it by its import path in the configuration file:

```toml
[workload]
type = "mypackage.MyWorkload"
```

How does your workload affect the game's performance?

### Done Before Time Runs Out?

Explore Yardstick's features freely, or ask the lecture to come up with an ad-hoc exercise to complete.

## BONUS: Connect to the Game Server during Your Experiment

While debugging your experiments, it can be useful to see what the game and its emulated players are doing. Because the DAS-6 worker nodes are not accessible from the Internet, you cannot *directly* connect to the game server with your local Minecraft client.
However, you can easily work around this by creating an SSH tunnel.

Start by running your experiment or by launching the game server manually on a worker node.
Next, use `preserve -llist` to identify which machine (e.g., node0XY) is running the game server.<sup id="a4">[4](#fn4)</sup> Now create two SSH tunnels from your local machine to the worker node that is running the game server, replacing `node0XY` with the correct hostname:

```
ssh -L 25565:node0XY:25565 das6
```
*Working out how this command works exactly is left as an exercise for the reader.*

Finally, start your Minecraft client on your local machine -- matching the version the server runs, which is the `version` setting in the `[game]` section (see `MinecraftServer.DEFAULT_VERSION` for the default) -- and connect to the server at `localhost:25565`. You should now be connected to the game server running on the DAS-6.

---

<a name="fn1">1.</a> <https://news.xbox.com/en-us/2020/05/18/minecraft-connecting-more-players-than-ever-before/> [↩](#a1)

<a name="fn2">2.</a> Ibid. [↩](#a2)

<a name="fn3">3.</a> van der Sar, et al. [Yardstick: A Benchmark for Minecraft-like Services](https://atlarge-research.com/pdfs/jvdsar-yardstick-benchmark-icpe-2019.pdf). ICPE 2019 [↩](#a3)

<a name="fn4">4.</a> Eickhoff, et al. [Meterstick: Benchmarking Performance Variability in Cloud and Self-hosted Minecraft-like Games](https://atlarge-research.com/pdfs/2023-jeickhoff-Meterstick-ICPE2023.pdf). ICPE 2023 [↩](#a4)
