# Luanti Benchmarking with Yardstick on DAS-6

This document explains the updates made to the Yardstick integration code for running Luanti benchmarks on the DAS-6 cluster.

## Overview

The integration code has been updated to use Luanti version 5.11.0, which matches our local testing environment. The bot implementation has also been improved with better protocol handling and more realistic workload behavior.

## Key Changes

1. **Updated Server Deployment**

   - Updated download URL to use Luanti 5.11.0
   - Updated path references to match the new version
   - Enhanced the Yardstick collector mod to match our local implementation

2. **Improved Bot Implementation**

   - Rewrote the bot client with a more reliable protocol implementation
   - Implemented better random walk behavior with appropriate timing
   - Added more realistic chat and keepalive behavior

3. **Enhanced WalkAround Workload**
   - Updated to use the new bot implementation
   - Improved movement patterns to better simulate player behavior
   - Fixed connection and error handling

## Running Benchmarks on DAS-6

To run the benchmarks on DAS-6, follow these steps:

1. Connect to DAS-6:

   ```bash
   ssh das6
   ```

2. Set up a Python environment:

   ```bash
   conda create -n yardstick python=3.9
   conda activate yardstick
   pip install yardstick-benchmark
   ```

3. Run a benchmark:
   ```bash
   python luanti_example.py --game minetest --nodes 4 --duration 300 --bots 20
   ```

## Benchmark Parameters

The `luanti_example.py` script supports the following parameters:

- `--game`: Game mode to benchmark (`minetest`, `extra_ordinance`, or `custom`)
- `--nodes`: Number of DAS-6 nodes to provision (default: 2)
- `--duration`: Duration of the benchmark in seconds (default: 120)
- `--bots`: Number of bots per node (default: 10)
- `--custom-game-url`: URL to custom game repository (if game=custom)

## Metrics Collection

The benchmark collects the following metrics:

- `luanti_tick_duration_seconds`: How long each server tick takes (lower is better)
- `luanti_player_count`: Number of connected players
- `luanti_packet_in_total`: Number of packets received by the server
- `luanti_packet_out_total`: Number of packets sent by the server

These metrics are exposed via HTTP endpoint on the server and collected by Telegraf.

## Troubleshooting

If you encounter issues with the benchmark:

1. Check the server logs for errors:

   ```
   /var/scratch/<username>/yardstick/<timestamp>/luanti-5.11.0/server.log
   ```

2. Check the bot logs for connection issues:

   ```
   /var/scratch/<username>/yardstick/<timestamp>/walkaround-<hostname>.log
   ```

3. Verify that the Luanti server is running:

   ```
   ps aux | grep luanti
   ```

4. Ensure the Yardstick collector mod is properly loaded:
   ```
   grep "Yardstick collector mod initialized" /var/scratch/<username>/yardstick/<timestamp>/luanti-5.11.0/server.log
   ```
