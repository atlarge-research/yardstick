# Luanti Mod Impact Assessment

This system allows you to systematically test the performance impact of different mod configurations on Luanti servers. It includes automated testing of the [Extra Ordinance mod](https://content.luanti.org/packages/Sumianvoice/extra_ordinance/), which is known to be computationally intensive.

## Overview

The Mod Impact Assessment experiment compares server performance across different mod configurations by:

1. **Deploying servers** with different mod combinations
2. **Running identical workloads** (walkbots) against each configuration
3. **Measuring performance metrics** (tick rate, CPU, memory usage)
4. **Generating comparative reports** showing mod impact

## Features

### Supported Mod Configurations

- **Vanilla**: Baseline Luanti with only monitoring mod
- **Extra Ordinance**: CPU-intensive top-down shooter mod
- **Weather**: Simple weather simulation mod
- **Performance Test**: Synthetic high-load test mod
- **Combined Configurations**: Multiple mods together

### Automated Testing

- Server deployment and cleanup
- Bot workload management
- Performance metric collection
- Statistical analysis and reporting

### Comprehensive Reporting

- CSV data files for analysis
- Markdown reports with comparisons
- JSON data for programmatic access

## Quick Start

### 1. List Available Configurations

```bash
python mod_impact_assessment.py --list-configs
```

### 2. Create Default Configuration

```bash
python mod_impact_assessment.py --create-default-config config.yml
```

### 3. Edit Configuration

Edit `config.yml` to match your infrastructure:

```yaml
nodes:
  - host: "your-server.example.com"
    user: "your-username"
    keyfile: "~/.ssh/id_rsa"

test_duration_seconds: 180
bot_count: 20
mod_configurations:
  - "vanilla"
  - "extra_ordinance_only"
```

### 4. Run Quick Test

```bash
python mod_impact_assessment.py --quick-test
```

### 5. Run Full Experiment

```bash
python mod_impact_assessment.py --config config.yml
```

## Detailed Configuration

### Node Configuration

```yaml
nodes:
  - host: "node001.example.com" # Your server hostname/IP
    user: "testuser" # SSH username
    keyfile: "~/.ssh/id_rsa" # SSH private key path
```

### Experiment Parameters

```yaml
test_duration_seconds: 180 # Test duration per configuration
bot_count: 20 # Bots per node (load level)
warmup_seconds: 45 # Server stabilization time
cooldown_seconds: 30 # Cleanup time between tests
```

### Mod Configuration Selection

```yaml
mod_configurations:
  - "vanilla" # Always include as baseline
  - "extra_ordinance_only" # High-impact mod
  - "weather_only" # Low-impact mod
  - "performance_test_only" # Synthetic load
  - "weather_and_performance" # Combined mods
  - "all_mods" # Everything except Extra Ordinance
```

## Expected Results

Based on the [Extra Ordinance reviews](https://content.luanti.org/packages/Sumianvoice/extra_ordinance/), here's what to expect:

### Performance Impact Ranking (Most to Least Impact)

1. **Extra Ordinance** - Significant CPU usage, complex graphics
2. **Performance Test** - Synthetic high-load mod
3. **Weather + Performance** - Combined overhead
4. **Weather Only** - Minimal impact
5. **Vanilla** - Baseline performance

### Key Metrics to Watch

- **Tick Rate**: Should drop significantly with Extra Ordinance
- **CPU Usage**: Expected to spike with intensive mods
- **Memory Usage**: May increase with complex mods
- **Bot Stability**: Connection issues under high load

## Understanding Results

### Output Files

- `mod_impact_detailed_YYYYMMDD_HHMMSS.json` - Complete raw data
- `mod_impact_summary_YYYYMMDD_HHMMSS.csv` - Spreadsheet-friendly summary
- `mod_impact_report_YYYYMMDD_HHMMSS.md` - Human-readable analysis

### Performance Metrics

- **Tick Rate**: Server game loop frequency (target: 20 TPS)
- **CPU Usage**: Processor utilization percentage
- **Memory Usage**: RAM consumption in MB
- **Success Rate**: Whether the test completed successfully

### Analysis Examples

```
Baseline Performance (vanilla): 20.0 TPS
extra_ordinance_only: 15.2 TPS (24% performance decrease)
weather_only: 19.8 TPS (1% performance decrease)
performance_test_only: 16.5 TPS (17.5% performance decrease)
```

## Troubleshooting

### Common Issues

#### Extra Ordinance Download Fails

The mod is downloaded from ContentDB automatically. If it fails:

- Check internet connectivity on test nodes
- Verify ContentDB is accessible
- Check disk space for mod extraction

#### High Resource Usage

Extra Ordinance is intentionally resource-intensive:

- Ensure test nodes have adequate CPU/memory
- Consider reducing bot count for initial tests
- Monitor system resources during testing

#### Bot Connection Issues

Under high server load, bots may fail to connect:

- This is expected behavior under stress
- The system will report connection success rates
- Consider this part of the performance measurement

### Performance Optimization

- **Start Small**: Begin with low bot counts (5-10)
- **Monitor Resources**: Watch CPU/memory during tests
- **Incremental Testing**: Add configurations gradually
- **Baseline First**: Always test vanilla configuration first

## Advanced Usage

### Custom Mod Configurations

You can extend the system by modifying `mod_impact_server.py`:

```python
custom_config = ModConfiguration(
    name="my_custom_test",
    description="Custom mod combination",
    game_mode="minetest_game",
    extra_ordinance_enabled=False,
    weather_enabled=True,
    performance_test_enabled=False,
)
```

### Integration with Existing Monitoring

The system provides hooks for custom metric collection:

- Override `get_tick_rate()` to use your monitoring
- Implement `get_cpu_usage()` with your preferred tools
- Extend `collect_performance_metrics()` for additional data

### Scaling to Multiple Nodes

The system supports distributed testing:

- Configure multiple nodes in `config.yml`
- Bots will be distributed across nodes
- Server runs on the first node by default

## Research Applications

This tool supports several research questions:

1. **Mod Performance Impact**: Quantify how different mods affect server performance
2. **Scalability Analysis**: Find performance limits under different mod loads
3. **Resource Utilization**: Understand CPU/memory requirements for different configurations
4. **Comparative Analysis**: Compare Luanti mod impact to other game engines

## Example Research Workflow

1. **Baseline Measurement**: Test vanilla Luanti performance
2. **Single Mod Impact**: Test each mod individually
3. **Cumulative Impact**: Test mod combinations
4. **Scaling Analysis**: Increase bot count until performance degrades
5. **Comparative Analysis**: Compare results across different configurations

## Next Steps

After running the Mod Impact Assessment, consider:

1. **Player Capacity Testing**: Find maximum player limits per configuration
2. **Behavior Impact Assessment**: Test different bot behaviors
3. **Environment Modification Testing**: Test building/destruction impact
4. **Network Resilience Testing**: Test under poor network conditions

## References

- [Extra Ordinance ContentDB Page](https://content.luanti.org/packages/Sumianvoice/extra_ordinance/)
- [Luanti Performance Documentation](https://luanti.org/docs/)
- [Yardstick Benchmark Framework](../README.md)

---

**Note**: This experiment is designed to push server performance limits. Monitor your test infrastructure and be prepared for high resource usage, especially when testing Extra Ordinance.
