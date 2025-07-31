# Luanti Server Management

This project provides tools for starting and managing Luanti servers, a custom UDP-based protocol used by certain game servers.

## Core Components

1. **Basic Server Starter** (`run_basic_server.py`) - A simple script to launch a Luanti server with minimal configuration.
2. **Server Management** (`run_server.py`) - Simple script to start a Luanti server.
3. **Experiment Runner** (`run_all_experiments.py`) - Tool for running benchmark experiments.

## Quick Start Guide

### Running a Basic Server

```bash
# Start a Luanti server on the default port (30123)
python run_basic_server.py --server-path /path/to/Luanti.app/Contents/MacOS/luanti
```

### Running the Server

```bash
# Start a simple Luanti server
python run_server.py --server-path /path/to/Luanti.app/Contents/MacOS/luanti
```

### Packet Analysis

```bash
# Capture and analyze packets (useful for debugging)
python packet_sniffer.py --port 30123
```

### Running Experiments

```bash
# Run all experiments using your Rust bots
python run_all_experiments.py

# Run a specific experiment
python run_all_experiments.py --experiment player_scalability
```

## Server Configuration

The basic server (`run_basic_server.py`) is configured with these default settings:

- Creative mode enabled
- Damage disabled
- Anticheat disabled
- Default spawn point at (0,20,0)
- Flat world generation

## Technical Details

### Server Management Options

The `run_server.py` script accepts these options:

```
--server-path       Path to Luanti executable (required)
--server-dir        Directory for server files (default: ./basic_server)
--server-port       Port for server (default: auto-select)
--debug             Enable verbose logging
```

### Experiment Runner

The `run_all_experiments.py` script can be used for automated testing:

```bash
# Run all experiments
python run_all_experiments.py

# Run a specific experiment (using your Rust bots)
python run_all_experiments.py --experiment player_scalability
```

Available experiment types:

- player_scalability
- mod_impact
- network_resilience
- player_behavior
- environment_modification

## Using with External Bots

To use the server with externally developed bots:

1. Start the server using `run_server.py`
2. Note the port number provided in the output
3. Connect your external bots to the server port

## Repository Structure

- **Scripts**: Core Python scripts for server management and testing

  - `run_basic_server.py` - Minimal server launch script
  - `run_server.py` - Enhanced server management script
  - `run_all_experiments.py` - Experiment runner

- **Configuration**:

  - `experiments/` - YAML configuration files for different experiment types
  - `basic_server/` - Server configuration and world data
  - `yardstick_benchmark/` - Benchmark implementation files

- **Documentation**:
  - `docs/` - Protocol documentation and setup guides

## Development Notes

These server tools provide a clean environment for testing Luanti protocol implementations. For traffic analysis, you can use the `packet_sniffer.py` tool to capture and analyze network communications between server and clients.
