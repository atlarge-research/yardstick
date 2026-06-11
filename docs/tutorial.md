
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

We run the Yardstick benchmark on the [DAS-5 compute cluster](https://www.cs.vu.nl/das5/) at the VU.
To connect to DAS-5, append the following configuration to your SSH configuration file, located at `~/.ssh/config`:

```
Host das5
	HostName fs0.das5.cs.vu.nl
	User DAS_5_USERNAME
```

You should now be able to connect to the DAS-5 using the command `ssh das5`.
SSH will first request your VUnet password, and then your DAS-5 password.

> [!TIP]
> If you connect to the DAS-5 regularly, it is worth switching to public-key authentication using `ssh-keygen` and `ssh-copy-id`. This is left as an exercise for the reader.

> [!TIP]
> Connecting from outside of the university network? You can either use [eduVPN](https://www.eduvpn.org/client-apps/) to connet to the DAS-5 when you're not directly connected to the VU campus network, or use `ssh das5-remote` after adding this to your `~/.ssh/config`:
>
> ```
> Host das5-remote
> 	HostName fs0.das5.cs.vu.nl
> 	User jdonkerv
> 	ProxyJump vu-data
> ```

### VSCode

We will work with a remote [Jupyter Notebook](https://jupyter.org/), which is easy to read and modify through [VSCode](https://code.visualstudio.com/).
If you have not done so already, install VSCode.
Next, use its "Connect to Host..." feature to connect VSCode to DAS-5.

### Yardstick

Now that your VSCode is connected to DAS-5, open a terminal (shortcut: `ctrl+~`) and run the following commands:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone git@github.com:atlarge-research/yardstick.git
cd yardstick
uv sync --extra notebooks
```

## Running Experiments

You are now ready to visit the [world generation experiment](../experiments/world_generation_time.ipynb) and start running experiments with Yardstick.

Open the `yardstick` directory in VSCode (`ctrl+shift+p > File: Open Folder`), and then open `experiments > world_generation_time.ipynb`. Make sure to select the right Python kernel and you will be ready to go.

In the remainder of this section, we will ask you to perform increasingly difficult experiments,
which will make you increasingly adept at using Yardstick specifically, and performing experiments on a distributed system generally.

> [!NOTE]
> Here starts the challenging part of the tutorial. Each subsection can easily take 30 minutes or multiple hours to complete.
> If you are doing this tutorial as part of a lecture or workshop, there may not be sufficient time remaining to complete all exercises.
> This is by design. If you are out of time but remain curious about this work, feel free to explore the remaining sections from home. Your account is likely valid for several weeks.

### Jupyter Notebook Example

We recommend reading the file line by line to develop a sufficiently good understanding of what is going on.
Afterwards, run your first experiment by running all cells in the notebook.
The cell that runs the experiment can take a long time (~10 minutes) to complete.
This is expected.
While the experiment is running, you can run type `preserve -llist` in the terminal to get an overview of node reservations on the DAS-5. You'll likely see a line similar to the one below, with your username:

```
id      user            start           stop            state   nhosts  hosts
351651  core2435        06/21   07:02   06/21   07:18   R       2       node001 node015
```

This shows that user `core2435` has reserved 2 nodes: `node001` and `node015` from 7:02am until 7:18am.

> **Question 1**  
> Which nodes did you reserve? How many nodes are in use by others? How many nodes do they use?

When the experiment has completed, it is time to review the resulting plots.

> **Question 2**  
> Are the results surprising? Why (not)?

### Visualizing Results

Initially, only the CPU utilization is plotted.
However, there is a table containing the server's tick duration.
Add a plot that visualizes the server's tick duration over time.

> **Question 3**  
> Do the tick durations match your expectations?
> Why (not)?

### Compare by Varying the Number of Players

Edit the notebook to run the experiments with a different number of players.

> **Question 4**  
Does changing the number of players have an impact on the game's performance?

### Compare by Changing the Game's Configuration

Edit the notebook to evaluate the impact of changing the view range.

> **Question 5**  
> How does the view distance affect the game's performance?

### Visualize Network Bandwidth Usage

The data used for the previous plots is obtained by querying a InfluxDB database instance containing the experiment measurements.
This database contains several other metrics and measurements.

Use the InfluxDB database and a Flux query to visualize the network bandwidth usage of the server node.

> **Question 6**  
> What does the network usage look like?
> Why does it look like this?

### Evaluate the Impact of Player Workloads

The example uses a player workload called `WorldGeneration`,
in which a variable number of players connect to the server and teleport to new areas to trigger terrain generation.

We suspect that the behavior of players can have a significant impact of the game's performance.

Edit Yardstick's internals and add a new player workload with different player behavior.

> **Question 7**  
> How does the workload affect the game's performance?

### Done Before Time Runs Out?

Explore Yardstick's features freely, or ask the lecture to come up with an ad-hoc exercise to complete.

## BONUS: Connect to the Game Server during Your Experiment

While debugging your experiments, it can be useful to see what the game and its emulated players are doing. Because the DAS-5 worker nodes are not accessible from the Internet, you cannot *directly* connect to the game server with your local Minecraft client.
However, you can easily work around this by creating an SSH tunnel.

Start by running your experiment or by launching the game server manually on a worker node.
Next, use `preserve -llist` to identify which machine (e.g., node0XY) is running the game server.<sup id="a4">[4](#fn4)</sup> Now create two SSH tunnels from your local machine to the worker node that is running the game server, replacing `node0XY` with the correct hostname:

```
ssh -L 25565:node0XY:25565 das5
```
*Working out how this command works exactly is left as an exercise for the reader.*

Finally, start your Minecraft 1.12.2 client on your local machine and connect to the server at `localhost:25565`. You should now be connected to the game server running on the DAS-5.

---

<a name="fn1">1.</a> <https://news.xbox.com/en-us/2020/05/18/minecraft-connecting-more-players-than-ever-before/> [↩](#a1)

<a name="fn2">2.</a> Ibid. [↩](#a2)

<a name="fn3">3.</a> van der Sar, et al. [Yardstick: A Benchmark for Minecraft-like Services](https://atlarge-research.com/pdfs/jvdsar-yardstick-benchmark-icpe-2019.pdf). ICPE 2019 [↩](#a3)

<a name="fn4">4.</a> Eickhoff, et al. [Meterstick: Benchmarking Performance Variability in Cloud and Self-hosted Minecraft-like Games](https://atlarge-research.com/pdfs/2023-jeickhoff-Meterstick-ICPE2023.pdf). ICPE 2023 [↩](#a4)
