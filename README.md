
# Yardstick - A Benchmark for Minecraft-like Services

Yardstick is a benchmark for Minecraft-like services. Using Yardstick, we showed that Minecraft-like services do not scale beyond 200-300 players, under favorable conditions. Please read our [ICPE 2019 article](https://atlarge-research.com/pdfs/jvdsar-yardstick-benchmark-icpe-2019.pdf) to learn more about Yardstick and the limited scalability of Minecraft-like services.

## Installation

### Building from Source

#### Player Emulation

Requirements:

1. Maven and Java 10+ JDK

Yardstick's player emulation component is written in Java and is build using Maven.
To build Yardstick's player emulation component, clone this repository, navigate to the player emulation component, and build using Maven:

```
git clone git@github.com:atlarge-research/yardstick.git && cd yardstick/yardstick && mvn verify
```

This produces a runnable JAR archive in `yardstick/yardstick/target`.

#### Experiment Runner

1. Go >=1.17
2. SSH available on $PATH

Yardstick's experiment runner depends on Yardstick's player emulation. To use the experiment runner, first install the player emulation as described above. 

The experiment runner is written in Go. To build it, navigate to the experiment runner component, and build:

```
cd yardstick/ys && go install
```

This creates a local installation of the experiment runner, accessible via the `ys` command.

> TIP: If `ys` is not available after installation, verify that Go's installation directory is added to your `$PATH` environment variable.

## Usage

The Yardstick benchmark consists of two main parts: a *player emulation* component, which connects to a Minecraft-like game and emulates real players, and a *benchmark runner*, which deploys and runs distributed benchmarks on Minecraft-like services. The benchmark runner uses the player emulation component internally.

Which component you want to use depends on your use-case. If you want to benchmark a Minecraft-like service, we recommend using the benchmark runner.
If you want to test player emulation and player behavior, we recommend using the player emulation component directly.

Both components use HOCON for their configuration and look for an `application.conf` file in the working directory for their configuration. See [`example.conf`](example.conf) for an example configuration file.

### Player Emulation

Yardstick's player emulation emulates players that connect to a Minecraft-like service and perform certain behavior. How many players are emulated, and which kind of behavior the players perform, depends on you configure Yardstick.

Next to the player emulation configuration provided in an `application.conf` file, the player emulation requires two command line arguments:

1. `--address` specifies the address of the Minecraft-like service.
	2. For traditional Minecraft-like services, this is the IP address and port number on which to connect Minecraft players.
	3. For the Serverless game prototype, this is an HTTP URL pointing to the game's naming service.
4. `--nodeID` specifies the ID of the player emulation node. This is used by some [player emulation programs](#player-emulation-programs) to coordinate behavior when running on multiple nodes.

When using the benchmark runner, these command line arguments are provided automatically.

Although Yardstick's player emulation has been used to evaluate Minecraft-like services with varying protocol versions, only its compatibility is only guaranteed for the protocol version used in Minecraft 1.12. Other protocol versions are not guaranteed to work out-of-the-box and may require modifying the Yardstick source code.

#### Player Emulation Programs

Player behaviors are organized as parameterized programs known as "experiments". When using Yardstick, you indicate which experiment Yardstick should run, and specify the necessary parameters. Each experiment is identified using a numerical ID. An overview of the experiments is available below.

- 8
	- **Description**: This program makes a specified number of players walk around in the virtual environment.
	- **Requirements**: None.
	- **Parameters**:
		- `bots` the total number of players to connect.
		- `botsperjoin` the number of players to connect at once.
		- `joininterval` the amount of time to wait before connecting a new batch of players.
		- `duration` the duration of the program. Players disconnect and the program exits after this amount of time.
- 11
	- **Description**: This program measures the response time of the Minecraft-like service under low load. The experiment involves two players. The first player starts a timer and places or removes a block. The second player stops the timer when they receive the block change message from the Minecraft-like service. This process continues until the user stops the player emulation.
	- **Requirements**: Minecraft-like service runs in CREATIVE mode, on a FLAT world.
	- **Parameters**: None.
- 12
	- **Description**: This program combines programs 8 and 12, providing an easy method for measuring game response time when simulating a specified number of players.
	- **Requirements**: Minecraft-like service runs in CREATIVE mode, on a FLAT world.
	- **Parameters**: All parameters from experiment 8. The `bots` parameter does not include the two players which measure response time, as connected by program 11.

If your evaluation requires player behavior different from the behavior provided by existing programs, you are encouraged to implement your own and add it to Yardstick through a pull request.

#### Player Emulation as a Library

Yardstick's player emulation works by running the "[experiments](#player-emulation-programs)" mentioned above and is currently not available as a stand-alone library. Pull requests that make Yardstick's player emulation available as a stand-alone library are welcome.

### Benchmark Runner

The benchmark runner takes care of (repeatedly) deploying and running the Minecraft-like game under test and Yardstick's player emulation component, and gathering the results afterwards. It does not perform a predetermined set of tests, but instead lets the user specify which parameters they want to vary in their performance evaluation.

For usage examples, see [`example.conf`](example.conf)

## Contributing

Please fork this repository and submit a pull request (PR) with your changes. We would be happy to review and merge them! PRs that make it easier to script and debug player behavior have priority.

Yardstick uses [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) and some [additional conventions](https://chris.beams.io/posts/git-commit/) for writing git commit messages. Please do the same in your PR.

## License

Yardstick is distributed under the LGPL-3.0 license. See [LICENSE](./LICENSE).
