#!/usr/bin/env python3
"""
Mod Impact Assessment Experiment for Luanti

This script runs systematic performance tests comparing different mod configurations
to measure their impact on server performance.

Usage:
    python mod_impact_assessment.py --config config.yml
    python mod_impact_assessment.py --list-configs  # Show available mod configurations
    python mod_impact_assessment.py --quick-test    # Run a quick test with 2 configs
"""

import argparse
import asyncio
import csv
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

import yaml

from yardstick_benchmark.model import Node
from yardstick_benchmark.games.luanti.server.mod_impact_server import (
    LuantiModImpactServer, 
    get_mod_configuration, 
    list_mod_configurations,
    MOD_CONFIGURATIONS
)
from yardstick_benchmark.games.luanti.workload import RustWalkAround
from yardstick_benchmark.monitoring import collect_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModImpactExperiment:
    """Manages the mod impact assessment experiment"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results = []
        self.start_time = datetime.now()
        
        # Parse node configuration
        self.nodes = [Node(n["host"], n["user"], n["keyfile"]) for n in config["nodes"]]
        
        # Experiment parameters
        self.test_duration = timedelta(seconds=config.get("test_duration_seconds", 120))
        self.bot_count = config.get("bot_count", 10)
        self.warmup_time = timedelta(seconds=config.get("warmup_seconds", 30))
        self.cooldown_time = timedelta(seconds=config.get("cooldown_seconds", 30))
        
        # Mod configurations to test
        self.mod_configs_to_test = config.get("mod_configurations", ["vanilla", "extra_ordinance_only"])
        
        # Output settings
        self.output_dir = Path(config.get("output_dir", "mod_impact_results"))
        self.output_dir.mkdir(exist_ok=True)
        
    async def run_single_test(self, mod_config_name: str) -> Dict[str, Any]:
        """Run a single test with a specific mod configuration"""
        
        logger.info(f"Starting test with mod configuration: {mod_config_name}")
        
        # Get mod configuration
        mod_config = get_mod_configuration(mod_config_name)
        
        # Create server instance
        server = LuantiModImpactServer(self.nodes, mod_config)
        
        # Create workload (bots)
        workload = RustWalkAround(
            nodes=self.nodes,
            server_host=self.nodes[0].host,  # Assume server runs on first node
            duration=self.test_duration,
            bots_per_node=self.bot_count,
            movement_mode="random",
            movement_speed=2.0,
        )
        
        test_start = datetime.now()
        
        try:
            # Deploy server
            logger.info(f"Deploying server with {mod_config_name} configuration...")
            server.deploy()
            
            # Start server
            logger.info("Starting server...")
            server.start()
            
            # Wait for server to stabilize
            logger.info(f"Waiting {self.warmup_time.total_seconds()}s for server warmup...")
            await asyncio.sleep(self.warmup_time.total_seconds())
            
            # Deploy workload
            logger.info(f"Deploying workload with {self.bot_count} bots...")
            workload.deploy()
            
            # Start workload
            logger.info("Starting bots...")
            workload.start()
            
            # Wait a bit for bots to connect
            await asyncio.sleep(10)
            
            # Collect baseline metrics
            logger.info("Collecting performance metrics...")
            metrics_start = datetime.now()
            
            # Collect metrics during the test
            metrics = await self.collect_performance_metrics(
                duration=self.test_duration,
                interval_seconds=5
            )
            
            metrics_end = datetime.now()
            
            # Stop workload
            logger.info("Stopping bots...")
            workload.stop()
            workload.cleanup()
            
            # Stop server
            logger.info("Stopping server...")
            server.stop()
            
            # Wait for cooldown
            await asyncio.sleep(self.cooldown_time.total_seconds())
            
            # Cleanup server
            server.cleanup()
            
            test_end = datetime.now()
            
            # Compile results
            result = {
                "mod_config_name": mod_config_name,
                "mod_config_description": mod_config.description,
                "test_start": test_start.isoformat(),
                "test_end": test_end.isoformat(),
                "metrics_start": metrics_start.isoformat(),
                "metrics_end": metrics_end.isoformat(),
                "test_duration_seconds": (test_end - test_start).total_seconds(),
                "bot_count": self.bot_count,
                "metrics": metrics,
                "success": True,
                "error": None
            }
            
            logger.info(f"Test completed successfully for {mod_config_name}")
            return result
            
        except Exception as e:
            logger.error(f"Test failed for {mod_config_name}: {e}")
            
            # Try to cleanup
            try:
                workload.stop()
                workload.cleanup()
                server.stop()
                server.cleanup()
            except:
                pass
            
            return {
                "mod_config_name": mod_config_name,
                "mod_config_description": mod_config.description,
                "test_start": test_start.isoformat(),
                "test_end": datetime.now().isoformat(),
                "success": False,
                "error": str(e),
                "metrics": {}
            }

    async def collect_performance_metrics(self, duration: timedelta, interval_seconds: int = 5) -> Dict[str, Any]:
        """Collect performance metrics during the test"""
        
        metrics = {
            "tick_rates": [],
            "timestamps": [],
            "cpu_usage": [],
            "memory_usage": [],
            "network_io": [],
            "disk_io": []
        }
        
        end_time = datetime.now() + duration
        
        while datetime.now() < end_time:
            timestamp = datetime.now()
            
            try:
                # Collect metrics from all nodes
                for node in self.nodes:
                    # This is a simplified version - you'd need to implement actual metric collection
                    # based on your existing monitoring infrastructure
                    
                    # Placeholder for actual metric collection
                    # In practice, you'd use your existing monitoring tools
                    tick_rate = await self.get_tick_rate(node)
                    cpu_usage = await self.get_cpu_usage(node)
                    memory_usage = await self.get_memory_usage(node)
                    
                    metrics["tick_rates"].append(tick_rate)
                    metrics["timestamps"].append(timestamp.isoformat())
                    metrics["cpu_usage"].append(cpu_usage)
                    metrics["memory_usage"].append(memory_usage)
                    
            except Exception as e:
                logger.warning(f"Failed to collect metrics: {e}")
                
            await asyncio.sleep(interval_seconds)
        
        return metrics

    async def get_tick_rate(self, node: Node) -> float:
        """Get server tick rate - placeholder implementation"""
        # This should integrate with your existing tick rate monitoring
        # For now, return a placeholder value
        return 20.0

    async def get_cpu_usage(self, node: Node) -> float:
        """Get CPU usage - placeholder implementation"""
        # This should integrate with your existing system monitoring
        return 50.0

    async def get_memory_usage(self, node: Node) -> float:
        """Get memory usage - placeholder implementation"""
        # This should integrate with your existing system monitoring
        return 1024.0

    async def run_all_tests(self):
        """Run all configured tests"""
        
        logger.info(f"Starting mod impact assessment with {len(self.mod_configs_to_test)} configurations")
        logger.info(f"Configurations to test: {self.mod_configs_to_test}")
        
        for mod_config_name in self.mod_configs_to_test:
            logger.info(f"Running test {len(self.results) + 1}/{len(self.mod_configs_to_test)}")
            
            result = await self.run_single_test(mod_config_name)
            self.results.append(result)
            
            # Save intermediate results
            self.save_results()
            
            logger.info(f"Completed test for {mod_config_name}")
            
        logger.info("All tests completed!")

    def save_results(self):
        """Save results to files"""
        
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        
        # Save detailed JSON results
        json_file = self.output_dir / f"mod_impact_detailed_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump({
                "experiment_start": self.start_time.isoformat(),
                "experiment_end": datetime.now().isoformat(),
                "config": self.config,
                "results": self.results
            }, f, indent=2)
        
        # Save CSV summary
        csv_file = self.output_dir / f"mod_impact_summary_{timestamp}.csv"
        with open(csv_file, 'w', newline='') as f:
            if self.results:
                writer = csv.DictWriter(f, fieldnames=[
                    'mod_config_name', 'mod_config_description', 'success',
                    'test_duration_seconds', 'bot_count', 'avg_tick_rate',
                    'avg_cpu_usage', 'avg_memory_usage', 'error'
                ])
                writer.writeheader()
                
                for result in self.results:
                    # Calculate averages
                    metrics = result.get("metrics", {})
                    avg_tick_rate = sum(metrics.get("tick_rates", [0])) / max(len(metrics.get("tick_rates", [1])), 1)
                    avg_cpu = sum(metrics.get("cpu_usage", [0])) / max(len(metrics.get("cpu_usage", [1])), 1)
                    avg_memory = sum(metrics.get("memory_usage", [0])) / max(len(metrics.get("memory_usage", [1])), 1)
                    
                    writer.writerow({
                        'mod_config_name': result['mod_config_name'],
                        'mod_config_description': result['mod_config_description'],
                        'success': result['success'],
                        'test_duration_seconds': result.get('test_duration_seconds', 0),
                        'bot_count': result.get('bot_count', 0),
                        'avg_tick_rate': avg_tick_rate,
                        'avg_cpu_usage': avg_cpu,
                        'avg_memory_usage': avg_memory,
                        'error': result.get('error', '')
                    })
        
        logger.info(f"Results saved to {json_file} and {csv_file}")

    def generate_report(self):
        """Generate a markdown report of the results"""
        
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"mod_impact_report_{timestamp}.md"
        
        with open(report_file, 'w') as f:
            f.write("# Luanti Mod Impact Assessment Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Experiment Duration:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} to {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Test Configuration\n\n")
            f.write(f"- **Bot Count:** {self.bot_count}\n")
            f.write(f"- **Test Duration:** {self.test_duration.total_seconds()} seconds\n")
            f.write(f"- **Warmup Time:** {self.warmup_time.total_seconds()} seconds\n")
            f.write(f"- **Cooldown Time:** {self.cooldown_time.total_seconds()} seconds\n\n")
            
            f.write("## Results Summary\n\n")
            f.write("| Mod Configuration | Description | Success | Avg Tick Rate | Avg CPU % | Avg Memory MB |\n")
            f.write("|-------------------|-------------|---------|---------------|-----------|---------------|\n")
            
            for result in self.results:
                metrics = result.get("metrics", {})
                avg_tick_rate = sum(metrics.get("tick_rates", [0])) / max(len(metrics.get("tick_rates", [1])), 1)
                avg_cpu = sum(metrics.get("cpu_usage", [0])) / max(len(metrics.get("cpu_usage", [1])), 1)
                avg_memory = sum(metrics.get("memory_usage", [0])) / max(len(metrics.get("memory_usage", [1])), 1)
                
                f.write(f"| {result['mod_config_name']} | {result['mod_config_description']} | ")
                f.write(f"{'✅' if result['success'] else '❌'} | {avg_tick_rate:.1f} | ")
                f.write(f"{avg_cpu:.1f} | {avg_memory:.1f} |\n")
            
            f.write("\n## Detailed Analysis\n\n")
            
            # Performance comparison
            successful_results = [r for r in self.results if r['success']]
            if len(successful_results) > 1:
                # Find baseline (vanilla)
                baseline = next((r for r in successful_results if r['mod_config_name'] == 'vanilla'), successful_results[0])
                baseline_metrics = baseline.get("metrics", {})
                baseline_tick_rate = sum(baseline_metrics.get("tick_rates", [20])) / max(len(baseline_metrics.get("tick_rates", [20])), 1)
                
                f.write(f"**Baseline Performance (({baseline['mod_config_name']})):** {baseline_tick_rate:.1f} TPS\n\n")
                
                for result in successful_results:
                    if result['mod_config_name'] == baseline['mod_config_name']:
                        continue
                        
                    metrics = result.get("metrics", {})
                    tick_rate = sum(metrics.get("tick_rates", [0])) / max(len(metrics.get("tick_rates", [1])), 1)
                    impact = ((baseline_tick_rate - tick_rate) / baseline_tick_rate) * 100
                    
                    f.write(f"**{result['mod_config_name']}:** {tick_rate:.1f} TPS ")
                    if impact > 0:
                        f.write(f"({impact:.1f}% performance decrease)\n")
                    else:
                        f.write(f"({abs(impact):.1f}% performance increase)\n")
            
            f.write("\n## Errors\n\n")
            failed_results = [r for r in self.results if not r['success']]
            if failed_results:
                for result in failed_results:
                    f.write(f"**{result['mod_config_name']}:** {result.get('error', 'Unknown error')}\n")
            else:
                f.write("No errors occurred during testing.\n")
        
        logger.info(f"Report saved to {report_file}")


def load_config(config_file: Path) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def create_default_config() -> Dict[str, Any]:
    """Create a default configuration for testing"""
    return {
        "nodes": [
            {
                "host": "localhost",
                "user": "testuser",
                "keyfile": "~/.ssh/id_rsa"
            }
        ],
        "test_duration_seconds": 120,
        "bot_count": 10,
        "warmup_seconds": 30,
        "cooldown_seconds": 30,
        "mod_configurations": ["vanilla", "extra_ordinance_only", "weather_only"],
        "output_dir": "mod_impact_results"
    }


async def main():
    parser = argparse.ArgumentParser(description="Luanti Mod Impact Assessment")
    parser.add_argument("--config", type=Path, help="Configuration file path")
    parser.add_argument("--list-configs", action="store_true", help="List available mod configurations")
    parser.add_argument("--quick-test", action="store_true", help="Run a quick test with 2 configurations")
    parser.add_argument("--create-default-config", type=Path, help="Create a default configuration file")
    
    args = parser.parse_args()
    
    if args.list_configs:
        print("Available mod configurations:")
        for name, description in list_mod_configurations().items():
            print(f"  {name}: {description}")
        return
    
    if args.create_default_config:
        config = create_default_config()
        with open(args.create_default_config, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        print(f"Default configuration created at {args.create_default_config}")
        return
    
    # Load configuration
    if args.config:
        config = load_config(args.config)
    elif args.quick_test:
        config = create_default_config()
        config["mod_configurations"] = ["vanilla", "extra_ordinance_only"]
        config["test_duration_seconds"] = 60
        print("Running quick test with vanilla and extra_ordinance_only configurations...")
    else:
        print("Please provide --config, --quick-test, or --list-configs")
        return
    
    # Run experiment
    experiment = ModImpactExperiment(config)
    await experiment.run_all_tests()
    experiment.generate_report()
    
    print(f"\nMod Impact Assessment completed!")
    print(f"Results saved to: {experiment.output_dir}")


if __name__ == "__main__":
    asyncio.run(main()) 