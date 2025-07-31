#!/usr/bin/env python3
"""
Most basic script to start a Luanti server without any extra features
"""

import os
import subprocess
import time
import logging
import signal
import argparse
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def setup_server_files(base_dir, port=30000):
    """Set up minimal server files"""
    # Create base directory
    os.makedirs(base_dir, exist_ok=True)
    
    # Create world directory
    world_dir = os.path.join(base_dir, "worlds", "yardstick_flat_test")
    os.makedirs(world_dir, exist_ok=True)
    
    # Create world.mt file
    with open(os.path.join(world_dir, "world.mt"), 'w') as f:
        f.write("""
gameid = minetest_game
backend = sqlite3
creative_mode = true
disable_anticheat = true
enable_damage = false
""")
    
    # Create config file
    config_file = os.path.join(base_dir, "minetest.conf")
    with open(config_file, 'w') as f:
        f.write(f"""
# Basic server settings
server_name = Basic Luanti Server
server_description = A simple Luanti server for testing
server_address = 127.0.0.1
port = {port}
disable_anticheat = true
creative_mode = true
enable_damage = false
default_privs = interact, shout, build, give, use, kick, ban, op, privs, server, admin, owner
max_users = 10
motd = Welcome to the basic Luanti server!

# Game mechanics settings
creative_mode = true
enable_damage = false

# Performance settings
max_block_send_distance = 10
max_simultaneous_block_sends_per_client = 40
max_simultaneous_block_sends_server_total = 250
time_speed = 0

# World generation settings
fixed_map_seed = grass
mg_name = v7
mg_flags = trees, caves, dungeons, decorations
water_level = 1
static_spawn_point = 0,20,0

# Debug settings
debug_log_level = verbose
html.enable = true
enable_debug_log = true
html.debug = true
html.debug_log_level = verbose


# End of parameters
""")
    
    # Create empty mods directory (for clean startup)
    mods_dir = os.path.join(base_dir, "mods")
    os.makedirs(mods_dir, exist_ok=True)
    
    return config_file, world_dir

def run_server(server_path, config_file, world_dir, debug=False):
    """Run the server with minimal configuration"""
    logger.info(f"Starting server with executable: {server_path}")
    logger.info(f"Using config file: {config_file}")
    logger.info(f"Using world directory: {world_dir}")
    
    # Simply run the server with minimal arguments
    cmd = [
        server_path,
        "--config", config_file,
        "--world", world_dir,
        "--gameid", "minetest_game",
        "--server"
    ]
    
    if debug:
        cmd.append("--verbose")
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    # Start the process
    process = subprocess.Popen(cmd)
    logger.info(f"Server started with PID {process.pid}")
    
    return process

def main():
    parser = argparse.ArgumentParser(description="Run a basic Luanti server")
    parser.add_argument("--server-path", default="/Users/alx/luanti_server/Luanti.app/Contents/MacOS/luanti", 
                        help="Path to the Luanti server executable (default: /Users/alx/luanti_server/Luanti.app/Contents/MacOS/luanti)")
    parser.add_argument("--dir", default="./basic_server", 
                        help="Base directory for server files")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug mode for more verbose logging")
    parser.add_argument("--port", type=int, default=30000,
                        help="Port for server to listen on (default: 30000)")
    
    args = parser.parse_args()
    
    # Set up server files
    base_dir = os.path.abspath(args.dir)
    config_file, world_dir = setup_server_files(base_dir, args.port)
    
    # Start the server
    server_process = run_server(args.server_path, config_file, world_dir, args.debug)
    
    try:
        logger.info("Server running. Press Ctrl+C to stop...")
        
        # Wait for the server to start
        time.sleep(2)
        
        # Monitor the server process
        while server_process.poll() is None:
            time.sleep(1)
        
        # If we got here, the server exited on its own
        exit_code = server_process.returncode
        logger.info(f"Server exited with code {exit_code}")
        
    except KeyboardInterrupt:
        logger.info("Stopping server...")
    finally:
        # Ensure the server is terminated
        if server_process.poll() is None:
            logger.info("Terminating server process...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Server didn't terminate, killing process...")
                server_process.kill()
        
        logger.info("Server stopped")

if __name__ == "__main__":
    main() 