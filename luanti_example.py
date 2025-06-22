#!/usr/bin/env python3
"""
Luanti Server Benchmark Script for DAS5

This script runs a comprehensive benchmark of a Luanti game server using the Yardstick framework.
It provisions nodes, deploys the server and bot workload, collects metrics, and saves results.
"""

import argparse
import logging
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep

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

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run Luanti server benchmark on DAS5",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Basic configuration
    parser.add_argument("--nodes", type=int, default=2,
                       help="Number of nodes to reserve (minimum 2)")
    parser.add_argument("--duration", type=int, default=120,
                       help="Benchmark duration in seconds")
    parser.add_argument("--bots-per-node", type=int, default=15,
                       help="Number of bots per workload node")
    parser.add_argument("--game-mode", default="minetest_game",
                       choices=["minetest_game", "devtest"],
                       help="Game mode to use")
    
    # Movement configuration
    parser.add_argument("--movement-mode", default="random",
                       choices=["random", "circular", "linear"],
                       help="Bot movement pattern")
    parser.add_argument("--movement-speed", type=float, default=2.0,
                       help="Bot movement speed (direction changes per second)")
    
    # Output configuration
    parser.add_argument("--output-dir", 
                       default=f"/var/scratch/{os.getlogin()}/yardstick",
                       help="Base output directory")
    parser.add_argument("--keep-old-results", action="store_true",
                       help="Don't delete previous results")
    
    # DAS configuration
    parser.add_argument("--reservation-time", type=int, default=900,
                       help="Node reservation time in seconds")
    
    return parser.parse_args()

def setup_output_directory(base_dir: str, keep_old: bool = False) -> Path:
    """Set up output directory with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = Path(base_dir) / f"luanti_benchmark_{timestamp}"
    
    if not keep_old and dest.parent.exists():
        # Clean up old benchmark results (keep last 5)
        old_dirs = sorted([d for d in dest.parent.iterdir() 
                          if d.is_dir() and d.name.startswith("luanti_benchmark_")])
        for old_dir in old_dirs[:-4]:  # Keep last 4, will add 1 new
            logger.info(f"Removing old benchmark directory: {old_dir}")
            shutil.rmtree(old_dir, ignore_errors=True)
    
    return dest

def validate_configuration(args):
    """Validate the benchmark configuration."""
    if args.nodes < 2:
        raise ValueError("At least 2 nodes required (1 server + 1 workload)")
    
    if args.duration < 30:
        raise ValueError("Duration must be at least 30 seconds")
    
    if args.bots_per_node < 1:
        raise ValueError("At least 1 bot per node required")
    
    if args.bots_per_node > 50:
        logger.warning("High bot count may cause performance issues")

def main():
    """Main benchmark execution function."""
    args = parse_arguments()
    
    try:
        validate_configuration(args)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Setup output directory
    dest = setup_output_directory(args.output_dir, args.keep_old_results)
    
    logger.info("="*60)
    logger.info("LUANTI SERVER BENCHMARK")
    logger.info("="*60)
    logger.info(f"Nodes: {args.nodes}")
    logger.info(f"Duration: {args.duration}s")
    logger.info(f"Bots per node: {args.bots_per_node}")
    logger.info(f"Game mode: {args.game_mode}")
    logger.info(f"Movement: {args.movement_mode} @ {args.movement_speed}/s")
    logger.info(f"Output: {dest}")
    logger.info("="*60)

    # Calculate total bots
    workload_nodes = args.nodes - 1  # All nodes except server
    total_bots = workload_nodes * args.bots_per_node
    logger.info(f"Total bots: {total_bots} across {workload_nodes} nodes")

    ### DEPLOYMENT ENVIRONMENT ###
    
    logger.info("Provisioning DAS5 nodes...")
    das = Das()
    nodes = das.provision(num=args.nodes)
    
    try:
        # Clean any previous data
        logger.info("Cleaning previous data from nodes...")
        yardstick_benchmark.clean(nodes)

        ### METRICS ###
        
        logger.info("Setting up metrics collection...")
        telegraf = Telegraf(nodes)
        telegraf.add_input_luanti_metrics(nodes[0])  # Server metrics
        
        logger.info("Deploying Telegraf...")
        telegraf.deploy()
        telegraf.start()

        ### LUANTI SERVER ###
        
        logger.info(f"Deploying Luanti server on {nodes[0].host}...")
        luanti_server = LuantiServer(nodes[:1], game_mode=args.game_mode)
        luanti_server.deploy()
        
        logger.info("Starting Luanti server...")
        luanti_server.start()

        ### WORKLOAD ###
        
        if len(nodes) > 1:
            logger.info(f"Deploying bot workload on {len(nodes[1:])} nodes...")
            wl = RustWalkAround(
                nodes[1:],              # Deploy bots on all nodes except first
                nodes[0].host,          # Connect to server on node 0
                duration=timedelta(seconds=args.duration),
                bots_per_node=args.bots_per_node,
                movement_mode=args.movement_mode,
                movement_speed=args.movement_speed,
            )
            wl.deploy()
            
            logger.info("Starting bot workload...")
            wl.start()

            # Let the experiment run
            sleep_time = args.duration + 30  # Extra time for cleanup
            logger.info(f"Running benchmark for {sleep_time} seconds...")
            logger.info(f"Server: {nodes[0].host}")
            logger.info(f"Bots: {[n.host for n in nodes[1:]]}")
            
            sleep(sleep_time)

            # Stop workload
            logger.info("Stopping bot workload...")
            wl.stop()
            wl.cleanup()
        else:
            logger.warning("Only one node available, running server-only benchmark")
            sleep(args.duration)

        # Stop server and monitoring
        logger.info("Stopping Luanti server...")
        luanti_server.stop()
        luanti_server.cleanup()

        logger.info("Stopping metrics collection...")
        telegraf.stop()
        telegraf.cleanup()

        # Fetch results
        logger.info("Collecting benchmark results...")
        yardstick_benchmark.fetch(dest, nodes)
        
        logger.info("="*60)
        logger.info("BENCHMARK COMPLETED SUCCESSFULLY")
        logger.info(f"Results saved to: {dest}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise
    finally:
        # Always clean up and release nodes
        logger.info("Cleaning up and releasing nodes...")
        yardstick_benchmark.clean(nodes)
        das.release(nodes)

if __name__ == "__main__":
    main()
