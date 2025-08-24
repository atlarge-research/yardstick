#!/usr/bin/env python3
"""
This script allows you to run either Luanti or PaperMC benchmarks
based on command line arguments.

Usage:
    python mve_benchmark.py luanti [options]
    python mve_benchmark.py papermc [options]
    python mve_benchmark.py --help
"""

import argparse
import sys
import os
import logging
from pathlib import Path
from typing import Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def run_luanti_benchmark(
    num_nodes: int = 2,
    bots_per_node: int = 50,
    duration: int = 90,
    bot_type: str = "walkbot",
    movement_mode: str = "random",
    game_mode: str = "extra_ordinance"
) -> bool:
    """Run the Luanti benchmark with specified parameters."""
    try:
        logger.info("Starting Luanti benchmark...")
        logger.info(f"Configuration: {num_nodes} nodes, {bots_per_node} bots/node, {duration}s duration")
        logger.info(f"Bot type: {bot_type}, Movement: {movement_mode}, Game: {game_mode}")
        
        # Import and configure luanti benchmark modules
        from yardstick_benchmark.provisioning import Das
        from yardstick_benchmark.monitoring import Telegraf
        from yardstick_benchmark.games.luanti.server import LuantiServer
        from yardstick_benchmark.games.luanti.workload import RustWalkAround, RustBlockBot
        import yardstick_benchmark
        from datetime import datetime, timedelta
        from time import sleep
        
        # Provision nodes
        logger.info(f"Provisioning {num_nodes} nodes on DAS cluster...")
        das = Das()
        nodes = das.provision(num=num_nodes, time_s=3600)  # 1 hour reservation
        
        try:
            # Clean any previous data
            yardstick_benchmark.clean(nodes)
            
            # Setup monitoring
            telegraf = Telegraf(nodes)
            telegraf.add_input_luanti_metrics(nodes[0])  # Server node
            telegraf.deploy()
            telegraf.start()
            
            # Setup Luanti server
            luanti_server = LuantiServer(
                nodes[:1], 
                game_mode=game_mode,
                use_source_build=False,
                enable_luajit=False,
                ipv4_only=True
            )
            
            luanti_server.deploy()
            luanti_server.start()
            
            # Give server time to initialize
            sleep(10)
            
            # Setup and run workload
            if bot_type == "walkbot":
                workload = RustWalkAround(
                    nodes[1:] if len(nodes) > 1 else nodes[:1],
                    server_host=nodes[0].host,
                    server_port=30000,
                    bots_per_node=bots_per_node,
                    duration=timedelta(seconds=duration),
                    movement_mode=movement_mode,
                    movement_speed=2.0,
                    spawn_radius=0
                )
            elif bot_type == "blockbot":
                workload = RustBlockBot(
                    nodes[1:] if len(nodes) > 1 else nodes[:1],
                    server_host=nodes[0].host,
                    server_port=30000,
                    bots_per_node=bots_per_node,
                    duration=timedelta(seconds=duration),
                    building_pattern="tower",
                    building_speed=2.0,
                    max_blocks=-1,
                    destructive_mode=False,
                    start_x=10.0,
                    start_y=8.0,
                    start_z=130.0,
                    spawn_radius=0
                )
            else:
                raise ValueError(f"Unknown bot type: {bot_type}")
            
            logger.info(f"Deploying {bot_type} workload...")
            workload.deploy()
            
            logger.info(f"Starting {bot_type} workload...")
            workload.start()
            
            logger.info(f"Running benchmark for {duration + 10} seconds...")
            sleep(duration + 10)
            
            # Stop services
            luanti_server.stop()
            telegraf.stop()
            
            # Fetch results
            username = os.getlogin()
            dest = Path(f"/var/scratch/{username}/yardstick/luanti_output")
            dest.mkdir(parents=True, exist_ok=True)
            yardstick_benchmark.fetch(dest, nodes)
            
            logger.info("Luanti benchmark completed successfully!")
            logger.info(f"Results saved to: {dest}")
            return True
            
        finally:
            # Clean up
            try:
                yardstick_benchmark.clean(nodes)
                das.release(nodes)
                logger.info("Cleanup completed")
            except Exception as e:
                logger.warning(f"Cleanup warning: {e}")
                
    except Exception as e:
        logger.error(f"Luanti benchmark failed: {e}")
        return False

def run_papermc_benchmark(
    num_nodes: int = 2,
    bots_per_node: int = 10,
    duration: int = 60
) -> bool:
    """Run the PaperMC benchmark with specified parameters."""
    try:
        logger.info("Starting PaperMC benchmark...")
        logger.info(f"Configuration: {num_nodes} nodes, {bots_per_node} bots/node, {duration}s duration")
        
        # Import PaperMC benchmark modules
        from yardstick_benchmark.provisioning import Das
        from yardstick_benchmark.monitoring import Telegraf
        from yardstick_benchmark.games.minecraft.server import PaperMC
        from yardstick_benchmark.games.minecraft.workload import WalkAround
        import yardstick_benchmark
        from datetime import datetime
        from time import sleep
        
        # Provision nodes
        logger.info(f"Provisioning {num_nodes} nodes on DAS cluster...")
        das = Das()
        nodes = das.provision(num=num_nodes, time_s=3600)  # 1 hour reservation
        
        try:
            # Clean any previous data
            yardstick_benchmark.clean(nodes)
            
            # Setup monitoring
            telegraf = Telegraf(nodes)
            telegraf.add_input_jolokia_agent(nodes[0])
            telegraf.add_input_execd_minecraft_ticks(nodes[0])
            telegraf.deploy()
            telegraf.start()
            
            # Setup PaperMC server
            papermc = PaperMC(nodes[:1])
            papermc.deploy()
            papermc.start()
            
            # Setup and run workload
            workload = WalkAround(nodes[1:], nodes[0].host, bots_per_node=bots_per_node)
            workload.deploy()
            workload.start()
            
            logger.info(f"Running benchmark for {duration} seconds...")
            sleep(duration)
            
            # Stop services
            papermc.stop()
            papermc.cleanup()
            
            # Fetch results
            username = os.getlogin()
            timestamp = (
                datetime.now()
                .isoformat(timespec="minutes")
                .replace("-", "")
                .replace(":", "")
            )
            dest = Path(f"/var/scratch/{username}/yardstick/papermc_{timestamp}")
            yardstick_benchmark.fetch(dest, nodes)
            
            logger.info("PaperMC benchmark completed successfully!")
            logger.info(f"Results saved to: {dest}")
            return True
            
        finally:
            # Clean up
            try:
                yardstick_benchmark.clean(nodes)
                das.release(nodes)
                logger.info("Cleanup completed")
            except Exception as e:
                logger.warning(f"Cleanup warning: {e}")
                
    except Exception as e:
        logger.error(f"PaperMC benchmark failed: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are available."""
    logger.info("Checking dependencies...")
    
    try:
        import yardstick_benchmark
        logger.info("yardstick_benchmark module available")
    except ImportError as e:
        logger.error(f"yardstick_benchmark module not found: {e}")
        return False
    
    # Check bot components for Luanti
    bot_dir = Path("bot_components/texmodbot")
    if bot_dir.exists():
        logger.info(f"Rust bot components found: {bot_dir}")
    else:
        logger.warning(f"ust bot components not found: {bot_dir} (needed for Luanti)")
    
    return True

def main():
    """Main entry point for the MVE benchmark runner."""
    parser = argparse.ArgumentParser(
        description="MVE Benchmark Runner - Run Luanti or PaperMC benchmarks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python mve_benchmark.py luanti --bots-per-node 50 --duration 120
    python mve_benchmark.py papermc --nodes 3 --bots-per-node 15
    python mve_benchmark.py luanti --bot-type blockbot --movement-mode tower
        """
    )
    
    parser.add_argument(
        "game",
        nargs="?",
        choices=["luanti", "papermc"],
        help="Game to benchmark (luanti or papermc)"
    )
    
    parser.add_argument(
        "--nodes", "-n",
        type=int,
        default=2,
        help="Number of nodes to provision (default: 2)"
    )
    
    parser.add_argument(
        "--bots-per-node", "-b",
        type=int,
        help="Number of bots per node (default: 50 for Luanti, 10 for PaperMC)"
    )
    
    parser.add_argument(
        "--duration", "-d",
        type=int,
        help="Benchmark duration in seconds (default: 90 for Luanti, 60 for PaperMC)"
    )
    
    # Luanti-specific options
    parser.add_argument(
        "--bot-type",
        choices=["walkbot", "blockbot"],
        default="walkbot",
        help="Bot type for Luanti (default: walkbot)"
    )
    
    parser.add_argument(
        "--movement-mode",
        default="random",
        help="Movement mode for Luanti bots (default: random)"
    )
    
    parser.add_argument(
        "--game-mode",
        default="extra_ordinance",
        help="Game mode for Luanti (default: extra_ordinance)"
    )
    
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check dependencies and exit"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check dependencies if requested
    if args.check_deps:
        success = check_dependencies()
        sys.exit(0 if success else 1)
    
    # Ensure game is specified for benchmarking
    if args.game is None:
        parser.error("Game argument is required unless using --check-deps")
    
    # Validate dependencies
    if not check_dependencies():
        logger.error("Dependency check failed. Use --check-deps for details.")
        sys.exit(1)
    
    # Set game-specific defaults
    if args.game == "luanti":
        bots_per_node = args.bots_per_node or 50
        duration = args.duration or 90
    else:  # papermc
        bots_per_node = args.bots_per_node or 10
        duration = args.duration or 60
    
    logger.info("Starting MVE Benchmark Runner")
    logger.info(f"Game: {args.game}")
    logger.info(f"Nodes: {args.nodes}")
    logger.info(f"Bots per node: {bots_per_node}")
    logger.info(f"Duration: {duration}s")
    
    # Run the appropriate benchmark
    if args.game == "luanti":
        success = run_luanti_benchmark(
            num_nodes=args.nodes,
            bots_per_node=bots_per_node,
            duration=duration,
            bot_type=args.bot_type,
            movement_mode=args.movement_mode,
            game_mode=args.game_mode
        )
    else:  # papermc
        success = run_papermc_benchmark(
            num_nodes=args.nodes,
            bots_per_node=bots_per_node,
            duration=duration
        )
    
    if success:
        logger.info("Benchmark completed successfully!")
        sys.exit(0)
    else:
        logger.error("Benchmark failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
