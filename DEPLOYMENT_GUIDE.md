# Luanti Deployment Guide

## Overview

This guide documents the complete Luanti benchmark deployment system using the yardstick framework on the DAS cluster. The system deploys Luanti game servers with Rust-based bot workloads for performance evaluation.

## System Architecture

### Components

1. **Luanti Server**: The game server running on dedicated nodes
2. **Rust Bots**: Multi-threaded bot clients using the texmodbot framework
3. **Metrics Collection**: Telegraf monitoring for performance data
4. **Deployment Scripts**: Ansible-based automation for cluster deployment

### File Structure

```
luantick/
├── luanti_example.py          # Main deployment script for DAS cluster
├── luanti_example.ipynb       # Jupyter notebook for analysis
├── test_deployment.py         # Configuration validation script
├── bot_components/
│   ├── texmodbot/             # Rust bot implementation
│   ├── mt_net/                # Minetest network library
│   ├── mt_rudp/               # RUDP protocol implementation
│   └── mt_auth/               # Authentication library
└── yardstick_benchmark/
    └── games/luanti/
        ├── server/            # Server deployment playbooks
        └── workload/          # Bot deployment playbooks
```

## Deployment Configuration

### Server Deployment (Ansible Playbooks)

1. **luanti_deploy.yml**: Downloads and configures Luanti server

   - Installs dependencies (wget, tar, sqlite3, build-essential)
   - Downloads Luanti binary from multiple sources
   - Sets up world directory and configuration
   - Installs yardstick collector mod

2. **luanti_start.yml**: Starts the game server

   - Detects server binary location
   - Launches server with proper configuration
   - Verifies port availability and startup logs

3. **luanti_stop.yml**: Gracefully stops the server

   - Sends TERM signal for graceful shutdown
   - Falls back to KILL if needed
   - Collects server logs

4. **luanti_cleanup.yml**: Cleans up deployment
   - Removes server files and directories
   - Kills any remaining processes

### Rust Bot Deployment (Ansible Playbooks)

1. **rust_walkaround_deploy.yml**: Sets up Rust environment

   - Installs Rust nightly toolchain
   - Copies texmodbot source code to remote nodes
   - Builds project dependencies

2. **rust_walkaround_start.yml**: Launches bot workload

   - Compiles and runs multi_walkbot binary
   - Configures bots with specified parameters
   - Supports multiple bots per node

3. **rust_walkaround_stop.yml**: Stops bot processes

   - Gracefully terminates bot processes
   - Collects bot logs and metrics

4. **rust_walkaround_cleanup.yml**: Cleans up bot deployment
   - Removes bot files and processes
   - Frees system resources

## Configuration Parameters

### Server Configuration

- **Game Mode**: `minetest_game` (default Luanti game)
- **Port**: 30000 (default Luanti port)
- **World**: Auto-generated benchmark world
- **Mods**: yardstick_collector for metrics

### Bot Configuration

- **Bots per Node**: 15 (configurable for load testing)
- **Movement Mode**: "random" (random walk pattern)
- **Movement Speed**: 2.0 seconds (direction change interval)
- **Duration**: 120 seconds (experiment runtime)
- **Connection**: Connects to server on port 30000

### System Requirements

- **Rust**: Nightly toolchain (automatically installed)
- **OS**: Ubuntu (with apt package manager)
- **Memory**: Sufficient for multiple bot processes
- **Network**: Low-latency connection between nodes

## Usage Instructions

### 1. Validate Configuration

```bash
cd /Users/alx/Documents/Thesis/code/luantick
python test_deployment.py
```

This script validates:

- All Ansible playbooks exist
- Texmodbot source code is available
- Required binaries are configured
- Deployment script syntax is correct

### 2. Run Deployment

```bash
python luanti_example.py
```

This script:

- Provisions 2 DAS nodes (1 server, 1 bots)
- Deploys Telegraf for metrics collection
- Deploys and starts Luanti server
- Deploys and runs Rust bot workload
- Collects performance data
- Cleans up and releases nodes

### 3. Analyze Results

Results are saved to `/var/scratch/{username}/yardstick/luanti_output/`

Use the Jupyter notebook for analysis:

```bash
jupyter lab luanti_example.ipynb
```

## Performance Characteristics

### Load Testing Configuration

- **15 bots per node**: High-load scenario for stress testing
- **2-minute duration**: Sufficient for performance evaluation
- **Random movement**: Realistic player behavior simulation
- **Multi-threaded bots**: Efficient resource utilization

### Metrics Collected

- **Server Performance**: CPU usage, memory consumption, network I/O
- **Bot Performance**: Connection times, movement latency, error rates
- **Network Metrics**: Packet loss, bandwidth utilization, latency
- **System Metrics**: Overall node resource usage

## Troubleshooting

### Common Issues

1. **Server Binary Not Found**

   - Check download URLs in luanti_deploy.yml
   - Verify binary detection logic in luanti_start.yml

2. **Rust Compilation Errors**

   - Ensure nightly toolchain is installed
   - Check texmodbot source code synchronization

3. **Connection Failures**

   - Verify server startup and port availability
   - Check firewall settings and network connectivity

4. **Performance Issues**
   - Monitor node resource usage
   - Adjust bot count and timing parameters

### Debugging

- **Server logs**: Collected in `{wd}/server.log`
- **Bot logs**: Available in `/tmp/walkbot_{hostname}.log`
- **Ansible output**: Detailed execution logs
- **System metrics**: Telegraf data collection

## Development Notes

### Recent Improvements

1. **Robust Binary Detection**: Enhanced server binary discovery
2. **Multi-source Downloads**: Fallback URLs for reliability
3. **Rust Nightly Support**: Automatic toolchain installation
4. **Error Handling**: Comprehensive error recovery
5. **Path Resolution**: Corrected texmodbot source paths

### Future Enhancements

1. **Dynamic Scaling**: Automatic bot count adjustment
2. **Real-time Monitoring**: Live performance dashboards
3. **Multiple Game Modes**: Support for different Luanti game types
4. **Advanced Bot Behaviors**: More sophisticated movement patterns
5. **Fault Tolerance**: Automatic recovery from failures

## References

- [Luanti Official Documentation](https://www.luanti.org/)
- [DAS Cluster Documentation](https://www.das6.science.uva.nl/)
- [Yardstick Benchmark Framework](https://github.com/atlarge-research/yardstick)
- [Rust Minetest Libraries](https://github.com/minetest-rust/)
