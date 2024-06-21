
# Yardstick Tutorial

Minecraft is one of the best-selling games of all time.
It has sold more than 200 million copies,<sup id="a1">[1](#fn1)</sup> and has more than 126 million active monthly players.<sup id="a2">[2](#fn2)</sup>
In contrast to traditional games, Minecraft gives players fine-grained control over the environment.
Players can be creative and alter the environment to their liking.
Players can decide to create buildings, mines, farms, logical circuits, and other constructions.
Minecraft's success has led to the creation of hundreds of similar games, which we collectively refer to as _Minecraft-like games_.


## Setting Up

### SSH

We run the Yardstick benchmark on the [DAS-6 compute cluster](https://www.cs.vu.nl/das/) at the VU.
To connect to DAS-6, append the following configuration to your SSH configuration file, located at `~/.ssh/config`:

```
Host das6
	HostName fs0.das6.cs.vu.nl
	User DAS5_USERNAME
```

You should now be able to connect to the DAS-6 using the command `ssh das6`.
SSH will first request your VUnet password, and then your DAS-6 password.

> PRO TIP: If you connect to the DAS-6 regularly, it is worth switching to public-key authentication using `ssh-keygen` and `ssh-copy-id`. This is left as an exercise for the reader.

> PRO TIP: Use [eduVPN](https://www.eduvpn.org/client-apps/) to connet to the DAS-6 when you're not directly connected to the VU campus network.

### VSCode

We will work with a remote [Jupyter Notebook](https://jupyter.org/), which is easy to read and modify through [VSCode](https://code.visualstudio.com/).
If you have not done so already, install VSCode.
Next, use its "Connect to Host..." feature to connect VSCode to DAS6.

### Python Environment

Now that your VSCode is connected to DAS6, open a terminal (shortcut: `ctrl ~`).
We will proceed by installing Miniconda, which we use to manage Python and native dependencies required for Yardstick to run.

You can follow the steps outlined on their [Web page](https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh), or follow the commands listed below:

> IMPORTANT: When asked for an installation location, make sure to use the `target_dir` location shown below, where `whoami`, including back ticks, is replaced by your DAS6 username.
>
> The installation location is important because, by default, users on DAS6 have limited storage space available in their home directory, the default installation location, which can lead to errors during or after the installation process.

Run these commands to install Miniconda:

```bash
target_dir=/var/scratch/`whoami`/miniconda3
mkdir -p $target_dir
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O $target_dir/miniconda.sh
bash $target_dir/miniconda.sh -b -u -p $target_dir
rm -rf $target_dir/miniconda.sh
```

Follow the instructions to create and activate a new conda environment called `yardstick`.
Once activated, run the following commands to obtain Yardstick and its dependencies:

```bash
conda install jupyter pandas seaborn
pip install yardstick
```

## Running Experiments

You are now ready to visit the [example experiment]() and start running experiments with Yardstick.
In the remainder of this section, we will ask to to perform increasingly difficult experiments,
which will make you increasingly adept at using Yardstick specifically, and performing experiments on a distributed system generally.

> PRO TIP: Here starts the challenging part of the tutorial. Each subsection can easily take 30 minutes to complete.
> If you are doing this tutorial as part of a lecture or workshop, there may not be sufficient time remaining to complete all exercises.
> This is by design. If you are out of time but remain curious about this work, feel free to explore the remaining sections from home. Your account is likely valid for several weeks.

### Jupyter Notebook Example

We recommend reading the file line by line to develop a sufficiently good understanding of what is going on.
Afterwards, run your first experiment by running all cells in the notebook.
The cell that runs the experiment can take a long time (~10 minutes) to complete.
This is expected.

Review the resulting plots.
Are the numbers surprising? Why (not)?

### Visualizing Results

Initiall, only the CPU utilization is plotted.
However, there is a table containing the server's tick duration.
Add a plot that visualizes the server's tick duration over time.

Do the tick durations match your expectations?
Why (not)?

### Visualize Network Bandwidth Usage

The data used for the previous plots is obtained by reading `csv` files in the experiment's output directory.
This directory contains several other files containing other metrics.

Load one of the output files to visualize another metric. We recommend visualizing the network bandwidth usage of the server node.

### Compare by Varying the Number of Players

Edit the notebook to run the experiments twice in a row with varying numbers of players.


Does changing the number of players have an impact on the game's performance?

### Compare by Changing the Game's Configuration

Edit Yardstick's internals and change the game's configuration file to evaluate the impact of changing the simulation distance of the game server.

How does this distance affect the game's performance?

### Evaluate the Impact of Player Workloads

The example uses a player workload called `WalkAround`,
in which a variable number of players connect to the server and walk around a predefined area.
However, we suspect that the behavior of players can have a significant impact of the game's performance.

Edit Yardstick's internals and add a new player workload with different player behavior.

How does the workload affect the game's performance?

### Done Before Time Runs Out?

Explore Yardstick's features freely, or ask the lecture to come up with an ad-hoc exercise to complete.

## BONUS: Connect to the Game Server during Your Experiment

While debugging your experiments, it can be useful to see what the game and its emulated players are doing. Because the DAS-6 worker nodes are not accessible from the Internet, you cannot *directly* connect to the game server with your local Minecraft client.
However, you can easily work around this by creating an SSH tunnel.

Start by running your experiment or by launching the game server manually on a worker node.
Next, use `preserve -llist` to identify which machine (e.g., node0XY) is running the game server.<sup id="a4">[4](#fn4)</sup> Now create two SSH tunnels from your local machine to the worker node that is running the game server, replacing `node0XY` with the correct hostname:

```
ssh -L 25565:node0XY:25565 das5
```
*Working out how this command works exactly is left as an exercise for the reader.*

Finally, start your Minecraft 1.12.2 client on your local machine and connect to the server at `localhost:25565`. You should now be connected to the game server running on the DAS-6.

---

<a name="fn1">1.</a> <https://news.xbox.com/en-us/2020/05/18/minecraft-connecting-more-players-than-ever-before/> [↩](#a1)

<a name="fn2">2.</a> Ibid. [↩](#a2)

<a name="fn3">3.</a> van der Sar, et al. Yardstick: A Benchmark for Minecraft-like Services. ICPE 2019 [↩](#a3)

<a name="fn4">4.</a> When you run an experiment, the hostname of the node running the server will become visible in the output from Ansible. [↩](#a4)