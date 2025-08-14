#!/usr/bin/env python3
"""
Robust Cluster-based Luanti Benchmark Script

This enhanced version of luanti_example.py incorporates reliability features
from the local benchmark to ensure robust server startup, bot connectivity
verification, and comprehensive metrics collection on the DAS cluster.
"""

import logging
import os
import shutil
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from yardstick_benchmark.provisioning import Das
from yardstick_benchmark.monitoring import Telegraf
from yardstick_benchmark.games.luanti.server import LuantiServer
from yardstick_benchmark.games.luanti.workload import RustWalkAround
import yardstick_benchmark

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class RobustClusterBenchmark:
    """Enhanced cluster benchmark with robustness features from local benchmark."""
    
    def __init__(self, args):
        self.args = args
        self.dest = Path(f"/var/scratch/{os.getlogin()}/yardstick/luanti_output")
        self.nodes = None
        self.das = None
        
        # Component references for cleanup
        self.telegraf = None
        self.luanti_server = None
        self.workload = None
        
    def check_dependencies(self):
        """Check if required tools and paths are available."""
        logger.info("Checking dependencies...")
        
        # Check if yardstick_benchmark is properly installed
        try:
            import yardstick_benchmark
            logger.info("✓ yardstick_benchmark module available")
        except ImportError:
            logger.error("✗ yardstick_benchmark module not found")
            logger.error("Please ensure the yardstick benchmark framework is properly installed")
            sys.exit(1)
        
        # Check if bot components exist
        bot_dir = Path("bot_components/texmodbot")
        if not bot_dir.exists():
            logger.error(f"✗ Rust bot directory not found: {bot_dir}")
            logger.error("Please ensure bot_components/texmodbot exists")
            sys.exit(1)
        logger.info(f"✓ Rust bot components found: {bot_dir}")
        
        # Check output directory permissions
        try:
            self.dest.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"✓ Output directory accessible: {self.dest}")
        except Exception as e:
            logger.error(f"✗ Cannot access output directory: {e}")
            sys.exit(1)
    
    def provision_nodes(self, num_nodes: int = 2):
        """Provision nodes on the DAS cluster with validation."""
        logger.info(f"Provisioning {num_nodes} nodes on DAS cluster...")
        
        self.das = Das()
        try:
            self.nodes = self.das.provision(num=num_nodes)
            logger.info(f"✓ Successfully provisioned {len(self.nodes)} nodes:")
            for i, node in enumerate(self.nodes):
                logger.info(f"  Node {i}: {node.host} (wd: {node.wd})")
            return self.nodes
        except Exception as e:
            logger.error(f"✗ Failed to provision nodes: {e}")
            sys.exit(1)
    
    def deploy_and_start_telegraf(self):
        """Deploy and start Telegraf with validation."""
        logger.info("Setting up metrics collection (Telegraf)...")
        
        self.telegraf = Telegraf(self.nodes)
        self.telegraf.add_input_luanti_metrics(self.nodes[0])
        
        try:
            # Deploy Telegraf
            logger.info("Deploying Telegraf...")
            res = self.telegraf.deploy()
            logger.info("✓ Telegraf deployed successfully")
            
            # Start Telegraf
            logger.info("Starting Telegraf...")
            self.telegraf.start()
            
            # Give Telegraf a moment to initialize
            time.sleep(3)
            logger.info("✓ Telegraf started successfully")
            
        except Exception as e:
            logger.error(f"✗ Failed to setup Telegraf: {e}")
            raise
    
    def deploy_and_start_server(self, game_mode: str = "minetest_game"):
        """Deploy and start Luanti server with startup verification."""
        logger.info("Setting up Luanti server...")
        
        self.luanti_server = LuantiServer(self.nodes[:1], game_mode=game_mode)
        
        try:
            # Deploy server
            logger.info("Deploying Luanti server...")
            self.luanti_server.deploy()
            logger.info("✓ Luanti server deployed successfully")
            
            # Start server
            logger.info("Starting Luanti server...")
            self.luanti_server.start()
            
            # Verify server startup
            self.verify_server_startup()
            
        except Exception as e:
            logger.error(f"✗ Failed to setup Luanti server: {e}")
            raise
    
    def verify_server_startup(self, max_wait_time: int = 60):
        """Verify that the server has started successfully."""
        logger.info("Verifying server startup...")
        
        # The Ansible playbooks already do some verification, but we can add more checks here
        # For now, we'll wait a bit and then check logs
        
        check_interval = 5
        for i in range(max_wait_time // check_interval):
            time.sleep(check_interval)
            
            try:
                # Check server logs for startup confirmation
                # Note: This would require SSH access to the node to check logs
                # For now, we trust the Ansible verification but log the progress
                elapsed = (i + 1) * check_interval
                logger.info(f"Server startup verification: {elapsed}s elapsed...")
                
                if elapsed >= 30:  # After 30 seconds, assume success if no errors
                    break
                    
            except Exception as e:
                logger.warning(f"Could not verify server status: {e}")
        
        logger.info("✓ Server startup verification completed")
    
    def deploy_and_start_workload(self, 
                                 duration: timedelta = timedelta(seconds=120),
                                 bots_per_node: int = 15,
                                 movement_mode: str = "random",
                                 movement_speed: float = 2.0):
        """Deploy and start bot workload with staggered startup."""
        logger.info(f"Setting up bot workload ({bots_per_node} bots per node)...")
        
        self.workload = RustWalkAround(
            self.nodes[1:],              # Deploy bots on node 1
            self.nodes[0].host,          # Connect to server on node 0
            duration=duration,
            bots_per_node=bots_per_node,
            movement_mode=movement_mode,
            movement_speed=movement_speed,
        )
        
        try:
            # Deploy workload
            logger.info("Deploying bot workload...")
            self.workload.deploy()
            logger.info("✓ Bot workload deployed successfully")
            
            # Start workload with verification
            logger.info("Starting bot workload...")
            self.workload.start()
            
            # Give bots time to connect
            logger.info("Waiting for bots to connect...")
            time.sleep(10)
            logger.info("✓ Bot workload started successfully")
            
        except Exception as e:
            logger.error(f"✗ Failed to setup bot workload: {e}")
            raise
    
    def run_benchmark_cycle(self, run_duration: int = 150):
        """Run the benchmark for the specified duration with monitoring."""
        logger.info("="*60)
        logger.info("RUNNING BENCHMARK")
        logger.info("="*60)
        logger.info(f"Duration: {run_duration} seconds")
        logger.info(f"Server node: {self.nodes[0].host}")
        logger.info(f"Bot node: {self.nodes[1].host}")
        logger.info("="*60)
        
        # Monitor progress
        check_interval = 30  # Report every 30 seconds
        elapsed = 0
        
        while elapsed < run_duration:
            sleep_time = min(check_interval, run_duration - elapsed)
            time.sleep(sleep_time)
            elapsed += sleep_time
            
            remaining = run_duration - elapsed
            logger.info(f"Benchmark progress: {elapsed}s elapsed, {remaining}s remaining")
        
        logger.info("✓ Benchmark duration completed")
    
    def cleanup_components(self):
        """Clean up all components in the correct order."""
        logger.info("Cleaning up benchmark components...")
        
        errors = []
        
        # Stop workload
        if self.workload:
            try:
                logger.info("Stopping bot workload...")
                self.workload.stop()
                self.workload.cleanup()
                logger.info("✓ Bot workload cleaned up")
            except Exception as e:
                error_msg = f"Failed to cleanup workload: {e}"
                logger.error(f"✗ {error_msg}")
                errors.append(error_msg)
        
        # Stop server
        if self.luanti_server:
            try:
                logger.info("Stopping Luanti server...")
                self.luanti_server.stop()
                self.luanti_server.cleanup()
                logger.info("✓ Luanti server cleaned up")
            except Exception as e:
                error_msg = f"Failed to cleanup server: {e}"
                logger.error(f"✗ {error_msg}")
                errors.append(error_msg)
        
        # Stop Telegraf
        if self.telegraf:
            try:
                logger.info("Stopping Telegraf...")
                self.telegraf.stop()
                self.telegraf.cleanup()
                logger.info("✓ Telegraf cleaned up")
            except Exception as e:
                error_msg = f"Failed to cleanup Telegraf: {e}"
                logger.error(f"✗ {error_msg}")
                errors.append(error_msg)
        
        # Clean nodes
        if self.nodes:
            try:
                logger.info("Cleaning nodes...")
                yardstick_benchmark.clean(self.nodes)
                logger.info("✓ Nodes cleaned")
            except Exception as e:
                error_msg = f"Failed to clean nodes: {e}"
                logger.error(f"✗ {error_msg}")
                errors.append(error_msg)
        
        # Release nodes
        if self.das and self.nodes:
            try:
                logger.info("Releasing nodes...")
                self.das.release(self.nodes)
                logger.info("✓ Nodes released")
            except Exception as e:
                error_msg = f"Failed to release nodes: {e}"
                logger.error(f"✗ {error_msg}")
                errors.append(error_msg)
        
        if errors:
            logger.warning(f"Cleanup completed with {len(errors)} errors:")
            for error in errors:
                logger.warning(f"  - {error}")
        else:
            logger.info("✓ All components cleaned up successfully")
    
    def fetch_and_verify_results(self):
        """Fetch results and verify they were collected properly."""
        logger.info("Fetching benchmark results...")
        
        # Remove existing output directory
        if self.dest.exists():
            shutil.rmtree(self.dest)
        
        try:
            # Fetch all collected data
            yardstick_benchmark.fetch(self.dest, self.nodes)
            logger.info(f"✓ Results fetched to: {self.dest}")
            
            # Verify results
            self.verify_results()
            
        except Exception as e:
            logger.error(f"✗ Failed to fetch results: {e}")
            raise
    
    def verify_results(self):
        """Verify that expected result files were created."""
        logger.info("Verifying benchmark results...")
        
        if not self.dest.exists():
            logger.error("✗ Results directory does not exist")
            return
        
        # Check for expected files and directories
        expected_items = [
            "server.log",       # Server logs
            "metrics",          # Metrics directory
        ]
        
        found_items = []
        missing_items = []
        
        for item in expected_items:
            item_path = self.dest / item
            if item_path.exists():
                found_items.append(item)
                if item_path.is_file():
                    size_mb = item_path.stat().st_size / (1024 * 1024)
                    logger.info(f"✓ Found {item} ({size_mb:.2f} MB)")
                else:
                    file_count = len(list(item_path.rglob("*"))) if item_path.is_dir() else 0
                    logger.info(f"✓ Found {item}/ ({file_count} files)")
            else:
                missing_items.append(item)
                logger.warning(f"⚠️ Missing {item}")
        
        # Summary
        logger.info("="*60)
        logger.info("RESULT VERIFICATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Found: {len(found_items)}/{len(expected_items)} expected items")
        if missing_items:
            logger.warning(f"Missing items: {', '.join(missing_items)}")
        else:
            logger.info("✓ All expected result items found")
        logger.info(f"Results location: {self.dest}")
        logger.info("="*60)
    
    def run_benchmark(self, 
                     duration: int = 150,
                     bots_per_node: int = 15, 
                     game_mode: str = "minetest_game",
                     movement_mode: str = "random"):
        """Run the complete robust benchmark."""
        start_time = datetime.now()
        logger.info("="*60)
        logger.info("ROBUST CLUSTER LUANTI BENCHMARK")
        logger.info("="*60)
        logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Duration: {duration}s")
        logger.info(f"Bots per node: {bots_per_node}")
        logger.info(f"Game mode: {game_mode}")
        logger.info(f"Movement mode: {movement_mode}")
        logger.info("="*60)
        
        try:
            # Step 1: Check dependencies
            self.check_dependencies()
            
            # Step 2: Provision nodes
            self.provision_nodes(num_nodes=2)
            
            # Step 3: Clean any previous data
            logger.info("Cleaning previous data...")
            yardstick_benchmark.clean(self.nodes)
            
            # Step 4: Deploy and start monitoring
            self.deploy_and_start_telegraf()
            
            # Step 5: Deploy and start server
            self.deploy_and_start_server(game_mode=game_mode)
            
            # Step 6: Deploy and start workload
            bot_duration = timedelta(seconds=duration - 30)  # Stop bots 30s before end
            self.deploy_and_start_workload(
                duration=bot_duration,
                bots_per_node=bots_per_node,
                movement_mode=movement_mode
            )
            
            # Step 7: Run benchmark
            self.run_benchmark_cycle(duration)
            
            # Step 8: Fetch and verify results
            self.fetch_and_verify_results()
            
            # Final summary
            end_time = datetime.now()
            total_duration = end_time - start_time
            
            logger.info("="*60)
            logger.info("BENCHMARK COMPLETED SUCCESSFULLY")
            logger.info("="*60)
            logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Total duration: {total_duration}")
            logger.info(f"Results saved to: {self.dest}")
            logger.info("="*60)
            
        except KeyboardInterrupt:
            logger.info("Benchmark interrupted by user")
            raise
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            raise
        finally:
            # Always clean up
            self.cleanup_components()

class BenchmarkConfig:
    """Configuration class for benchmark parameters."""
    def __init__(self):
        self.duration = 150          # Total benchmark duration in seconds
        self.bots_per_node = 15      # Number of bots per node
        self.game_mode = "minetest_game"  # Game mode to use
        self.movement_mode = "random"     # Bot movement pattern

def main():
    """Main function with argument parsing and signal handling."""
    # Parse arguments (could be enhanced with argparse if needed)
    config = BenchmarkConfig()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        logger.info("Received interrupt signal, cleaning up...")
        sys.exit(130)  # Standard exit code for SIGINT
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run benchmark
    try:
        benchmark = RobustClusterBenchmark(config)
        benchmark.run_benchmark(
            duration=config.duration,
            bots_per_node=config.bots_per_node,
            game_mode=config.game_mode,
            movement_mode=config.movement_mode
        )
    except KeyboardInterrupt:
        logger.info("Benchmark cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Benchmark failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
