# How to run Experiments using Yardstick: the Present and the Future

If you want to understand how to use Yardstick for your experiments, this document is for you. If you want to know more about *why* or the *what*, please contact one of the Opencraft team members.

This document is split into two parts, the first describes the current setup used to run experiments using Yardstick. The second describes how to run experiments with the next (yet to be released) version of Yardstick.

## Running Experiments using Yardstick 1.0

### The Toolbox

At the time of writing, the Yardstick benchmark consists of the following tools:
1. Yardstick <https://atlarge.ewi.tudelft.nl/gitlab/opencraft/benchmark-mc>
2. Dastools <https://atlarge.ewi.tudelft.nl/gitlab/opencraft/dastools>

Together, they offer the following features:
1. Reserve nodes on the DAS-5 for an experiment.
2. Declare different types of nodes.
3. Run a command (which can point to any executable or script) on each of these nodes. Each node type executes its own command.
5. Run Prometheus on (some of) these nodes to monitor the system.
6. Connect to a Minecraft-like server and emulate multiple players.

Of these features, only the last one is provided by the Yardstick code. The others are provided by Dastools.

The remainder of this section explains how run an experiment with these tools. The next section explains some of the drawbacks and the proposed solution.

### Setting up an Experiment

This section will take you step-by-step through setting up an experiment. After running your own experiments, you might end up with a something that looks like [this](https://atlarge.ewi.tudelft.nl/gitlab/opencraft/experiments/tree/e8f3b4b2126e63f3ce47c1be7351dd48410b9f86/yardstick-fixed-bots). All examples used below are taken from this directory.

#### Step 1: Moving files to the DAS-5

Move all files that should be read or executed to the DAS-5. In our case, these files include:
1. One or multiple Minecraft-like game server executable (JAR) files.
2. The corresponding configuration files for these games.
3. The Yardstick executable JAR file.
4. The Prometheus executable.
5. The Prometheus configuration file.
6. The Prometheus Node Exporter executable.
7. The Prometheus Push Gateway executable.
8. ... Additional files depending on your experiment.

If you want others to repeat your experiment, make sure that the directory where the files are located are readable by other users.

#### Step 2: Create an experiment directory

Dastools allows you to specify arbitrary node types. Each node type runs its own program. To find the right program for the right node, Dastools requires the following directory layout for any experiment:

```
experiment-folder
+-- programs
```

`programs` is a directory that must contain an *executable*[^1] file for each type of node that you specify in your experiment. For example, if your experiment includes `mcserver` and `yardstick` node types, your directory tree would look like:

```
experiment-folder
+-- programs
    +-- 0-mcserver-a
    +-- 1-yardstick-c
```

The next section talks about what these files should look like. The remainder of this section talks about the naming convention used for these files, and why this matters.

Each executable file in this directory follows the naming convention [number]-[node type]-[a/s/c].

The number indicates *when* to execute the program and is known as the run level. Programs are executed in ascending order. Programs with the same number are executed simultaneously.

The letter 'a', 's', or 'c' at the end indicates *how* to execute the program.
- 'a' stands for **a**synchronous. In practice, this means fire-and-forget: the program is started and promptly forgotten by Dastools. Even if the program returns an error code directly after it is started, Dastools considers it a job well-done.
- 's' stands for **s**ynchronous. These programs block Dastools from advancing to the next run level.
- 'c' stands for **c**ompletion. These programs can be thought of as synchronous programs with an additional property: when all completion programs have terminated, Dastools assumes the experiment is complete and will terminate all other programs.

#### Step 3: Provide instructions for each node type

Now that you have moved all necessary configuration files and executables to the DAS-5, and have created the required directory structure for the experiment, you can specify what each node type should do specifically.

Although the executable files in the `programs` directory can be any type of executable that can be interpreted by the shell, we will assume here that these file are BASH scripts.

In this case, the file `0-mcserver-a` might look like this:
```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

java -Xmx50G -Xms1024M -Dyardstick.gateway.host=${PROMHOST} -Dyardstick.gateway.port=${PROMPORT} -jar server.jar nogui
```

#### Step 4: Write an experiment-runner script

Now that all nodes know what they have to do, it is time to orchestrate the entire bunch. To do so, you'll need to write yet another script. You can find an example [here](https://atlarge.ewi.tudelft.nl/gitlab/opencraft/experiments/blob/e8f3b4b2126e63f3ce47c1be7351dd48410b9f86/yardstick-fixed-bots/run.sh). In short, this example script does the following:


1. Repeat the 'experiment' multiple times for a varying number of players and Mincraft-like games.
2. Repeat each of these configurations multiple times to increase the reliability of the results.
3. Run the experiment. Wait for it to complete. Move all output to a single directory. Create an archive from that directory. Clean up the original output. Repeat.

#### Step 5: Run the experiment

After ...
1. all executables and configuration files are moved to the DAS-5. 
2. you have checked for each of these files that it is *accessible* and *executable* (if needed).
3. you have created an experiment directory with the correct layout.
4. you have written a program file for each node type in the `programs` directory.
5. these programs are set to be executable (`chmod +x filename`).
6. you have written an experiment-runner script that takes care of:
    1. looping through all desired experiment configurations.
    2. storing the output data.
    3. cleaning up files that might conflict with files generated in new experiment runs.

... you are finally ready to run your experiment!

#### Step 6: Visualizing the results

Bad news. Neither Yardstick nor Dastools provide any help in visualizing the obtained results. Unpacking all the data, transforming it to the required format, and creating the desired plots requires you to either write your own code or copy it from someone else.

There are a number of scripts in Jesse's experiments repository that you could use (for inspiration). Almost all directories in [this repository](https://atlarge.ewi.tudelft.nl/gitlab/opencraft/experiments/tree/e8f3b4b2126e63f3ce47c1be7351dd48410b9f86) contain a file called `make-plots.py`, or something similar, which create plots from a collection of CSV files. One of the more up-to-date ones can be found [here](https://atlarge.ewi.tudelft.nl/gitlab/opencraft/experiments/blob/e8f3b4b2126e63f3ce47c1be7351dd48410b9f86/yardstick-fixed-bots/graphs/make-old-plots.py).

These CSV files are generated mainly from the Prometheus data present in the output archive. To perform this conversion, Jesse used [this](https://atlarge.ewi.tudelft.nl/gitlab/opencraft/experiments/blob/e8f3b4b2126e63f3ce47c1be7351dd48410b9f86/makeplots) script, which in turn calls a number of other scripts that can be found in the same repository.

Depending on the amount of time you have, you could consider rewriting the visualization code. If you do, consider that it takes more time than you think.

If you do decide to write your own visualization code think in advance about the desired data format you want to use for your input, then write separate scripts for both the data transformation and the actual visualization. This makes it much easier to create the same plots at a later point in time when your output data has changed. (This can happen when, for example, you decide that you no longer want to use Prometheus to perform measurements.)

Good luck. If you need any help, please send me a message on Slack or an email at <j.donkervliet@gmail.com>.

## Running Experiments using (the not yet released) Yardstick 2.0

At the time of writing, running Yardstick experiments is both cumbersome and volatile for at least two reasons:
1. Although Dastools takes care of part of the deployment, a large part of the work is still done manually. These manual tasks include:
    1. Placing all configuration files and executables on a location on disk where Dastools can access them. There is no default location for these files—the user needs to point to the correct location for each of these files.
    2. Making sure that all executables are are configured as 'executable' on disk.
    3. Creating a location to store the output.
    4. Creating an archive of the results and moving it to a safe location.
    5. Cleaning up the files created during the experiment.
    6. Looping experiments for multiple configurations.
    7. Visualizing the results.
3. Dastools is built only for the DAS-5, which means that testing the experimental setup locally is impossible. Using a cluster without a shared network drive is not possible at the time of writing.

To allow more thinking time on how to scale up Minecraft-like games, we have to make it easier set up and run experiments. We want to achieve this by first integrating the good parts of Dastools into Yardstick, and then adding additional features.

Dastools has two important 'good parts' that should be integrated into Yardstick.
First, Dastools automatically provisions machines to use for running distributed systems. Second, it automatically deploys Prometheus monitoring to perform system measurements.
Automating these tasks already saves time for the user.
Implementing these features in Yardstick directly allows the user to use only one system instead of two, and makes Yardstick itself a truly distributed benchmarking system.

However, even if these tasks can be performed by Yardstick, a large number of manual tasks remain. We are currently working on automating all the manual tasks listed above.

Adding these features to Yardstick is an ongoing effort. You can track our progress [here](https://atlarge.ewi.tudelft.nl/gitlab/opencraft/benchmark-mc/merge_requests/3).

[^1]: Your experiment will fail if these files are *not* executable. This can happen when copying such files from your local machine to the DAS-5 using `scp` or other tools.
