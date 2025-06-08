# Luanti Engine Benchmarking with Yardstick

This document explains how to set up and run Yardstick benchmarks with Luanti Engine, which powers various game modes including Minetest and Extra Ordinance.

## Prerequisites

- A local installation of Python 3.9+
- Access to the DAS-6 computing cluster (for running the actual benchmarks)
- Optional: A local installation of Luanti Engine for testing

## Installing Luanti Engine Locally

### Linux

```bash
# Ubuntu/Debian
sudo apt install minetest

# Fedora
sudo dnf install minetest

# Arch Linux
sudo pacman -S minetest
```

### macOS

Download the Luanti Engine app from the official website: https://www.minetest.net/downloads/

Or download the precompiled client directly:

```bash
mkdir -p ~/luanti
curl -L https://github.com/luanti-org/luanti/releases/download/5.11.0/luanti_5.11.0-macos11.3_x86_64_flag_O1.zip -o ~/luanti/luanti.zip
unzip ~/luanti/luanti.zip -d ~/luanti
```

Or build from source:

```bash
# Install dependencies
brew install cmake irrlicht libogg libvorbis libjpeg freetype gettext hiredis luajit

# Clone repository
git clone --depth=1 https://github.com/minetest/minetest.git
cd minetest

# Build
mkdir build
cd build
cmake ..
make -j$(nproc)
```

### Windows

Download the installer from the official website: https://www.minetest.net/downloads/

## Supported Game Modes

Luanti Engine supports various game modes, each with different gameplay mechanics. Our benchmarking integration supports:

### Minetest (Default)

The default sandbox game, similar to Minecraft, focusing on mining and crafting.

### Extra Ordinance

A top-down shooter with destructible terrain, featuring:

- Intense combat with giant bugs that tunnel through walls
- Multiple weapon loadouts and difficulty settings
- Varied gameplay with objectives to complete

### Custom Games

You can also benchmark custom games by providing the URL to the game repository.

## Yardstick Integration

The Yardstick integration for Luanti consists of several components:

1. **Server Implementation**: Manages deployment, starting, stopping, and cleanup of Luanti servers
2. **Workload Implementation**: Simulates player activity with the WalkAround workload
3. **Metrics Collection**: Captures server performance metrics using a Lua mod

### Directory Structure

The integration follows this structure:

```
yardstick_benchmark/
├── games/
│   ├── luanti/
│   │   ├── server/
│   │   │   ├── __init__.py              # LuantiServer class
│   │   │   ├── luanti_deploy.yml        # Ansible playbook for deployment
│   │   │   ├── luanti_start.yml         # Ansible playbook for starting
│   │   │   ├── luanti_stop.yml          # Ansible playbook for stopping
│   │   │   ├── luanti_cleanup.yml       # Ansible playbook for cleanup
│   │   │   └── minetest.conf.j2         # Configuration template
│   │   └── workload/
│   │       ├── __init__.py              # WalkAround class
│   │       ├── luanti_bot.py            # Bot client implementation
│   │       ├── luanti_walkaround.py     # Workload implementation
│   │       ├── walkaround_deploy.yml    # Ansible playbook for deployment
│   │       ├── walkaround_start.yml     # Ansible playbook for starting
│   │       ├── walkaround_stop.yml      # Ansible playbook for stopping
│   │       └── walkaround_cleanup.yml   # Ansible playbook for cleanup
```

## Local Testing

For local testing, you can use the provided scripts in this repository:

### Quick Setup for macOS

```bash
# Download and extract the Luanti client
mkdir -p ~/luanti
curl -L https://github.com/luanti-org/luanti/releases/download/5.11.0/luanti_5.11.0-macos11.3_x86_64_flag_O1.zip -o ~/luanti/luanti.zip
unzip ~/luanti/luanti.zip -d ~/luanti

# Set up the server directory
mkdir -p ~/luanti_server/mods/yardstick_collector
mkdir -p ~/luanti_server/worlds/yardstick_test

# Install required Python packages
pip install requests
```

### Running the Complete Benchmark Test

The complete test script will:

1. Start a Luanti server with the Minetest game mode
2. Start the Luanti GUI client
3. Start multiple bot clients that walk around in the world
4. Monitor server output for the specified duration
5. Clean up all processes when done

```bash
# Run the complete test with default settings (120 seconds, 3 bots)
./complete_test.py

# Run a shorter test with 2 bots
./complete_test.py --duration 60 --bot-count 2

# Run without the GUI client (bots only)
./complete_test.py --no-gui
```

### Running Individual Components

You can also run the individual components separately:

```bash
# Run only the server and GUI client
./luanti_local_test.py --duration 60

# Run only the bot client
./bot_client.py --count 2 --duration 30
```

## Running Benchmarks on DAS-6

To run the full benchmark on DAS-6, follow these steps:

1. Connect to DAS-6:

   ```bash
   ssh das6
   ```

2. Create and activate a Python environment:

   ```bash
   # Create a conda environment
   conda create -n yardstick python=3.9
   conda activate yardstick

   # Install dependencies
   conda install jupyter pandas seaborn
   pip install yardstick-benchmark
   ```

3. Run the example benchmark:

   ```bash
   # Run with default Minetest game mode
   python luanti_example.py

   # Run with Extra Ordinance game mode
   python luanti_example.py --game extra_ordinance

   # Customize the benchmark
   python luanti_example.py --game extra_ordinance --nodes 4 --duration 300 --bots 20
   ```

This will:

1. Reserve nodes on DAS-6
2. Deploy the monitoring tools (Telegraf)
3. Deploy the Luanti server on one node with the specified game mode
4. Deploy the workload (bots that walk around) on other nodes
5. Run the benchmark for the specified duration
6. Collect and save the results

## Advanced Configuration

The `luanti_example.py` script includes default parameters for the benchmark. You can modify these parameters to explore different scenarios:

- Change the game mode: Use the `--game` argument
- Change the number of nodes: Use the `--nodes` argument
- Change the duration: Use the `--duration` argument
- Change the number of bots: Use the `--bots` argument
- Use a custom game: `--game custom --custom-game-url URL`

## Understanding the Results

After running the benchmark, results will be saved to `/var/scratch/<username>/yardstick/<timestamp>/`. This directory will contain:

- CSV files with performance metrics
- Log files from the server and workload
- Metadata about the benchmark configuration

You can analyze these results using Jupyter notebooks or other data analysis tools.

## Metrics

The key metrics collected during benchmarking are:

- `luanti_tick_duration_seconds`: How long each server tick takes (lower is better)
- `luanti_player_count`: Number of connected players
- `luanti_packet_in_total`: Number of packets received by the server
- `luanti_packet_out_total`: Number of packets sent by the server

## Different Game Mode Considerations

When benchmarking different game modes, keep in mind:

### Minetest

- Focuses on mining and crafting
- Performance affected by terrain generation and block updates

### Extra Ordinance

- Intensive shooter with destructible terrain
- Higher CPU requirements due to combat mechanics and physics
- More network traffic due to projectiles and explosions

### Custom Games

- Behavior depends on the specific game
- May require custom workloads for realistic testing
