#!/usr/bin/env python3
"""
All-in-one script to run Luanti server, middleware, and bots
"""

import argparse
import subprocess
import time
import os
import signal
import sys
import socket
import logging
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def find_available_port(start_port=30000, max_attempts=100):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            # Create a socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # 2 second timeout
            
            # Attempt to bind to the port
            result = sock.connect_ex(('127.0.0.1', port))
            
            # If result is 0, the port is in use
            is_available = (result != 0)
            
            # Close the socket
            sock.close()
            
            if is_available:
                return port
        except Exception:
            pass
    return None

def run_server(server_path, server_dir, port):
    """Run the basic server in a separate process"""
    cmd = [
        sys.executable, 
        "run_basic_server.py", 
        "--server-path", server_path,
        "--dir", server_dir,
        "--port", str(port)
    ]
    
    logger.info(f"Starting server with command: {' '.join(cmd)}")
    server_process = subprocess.Popen(cmd)
    return server_process

# def run_middleware(listen_port, server_port, debug=False):
#     """Run the protocol middleware in a separate process"""
#     cmd = [
#         sys.executable,
#         "enhanced_middleware.py",
#         "--listen-port", str(listen_port),
#         "--server-port", str(server_port)
#     ]
    
#     if debug:
#         cmd.append("--debug")
    
#     logger.info(f"Starting middleware with command: {' '.join(cmd)}")
#     middleware_process = subprocess.Popen(cmd)
#     return middleware_process

# def run_bots(middleware_port, num_bots, bot_prefix, log_packets=False):
#     """Run the bots in a separate process"""
#     cmd = [
#         sys.executable,
#         "luanti_bot.py",
#         "--server-host", "127.0.0.1",
#         "--server-port", str(middleware_port),
#         "--num-bots", str(num_bots),
#         "--bot-prefix", bot_prefix
#     ]
    
#     if log_packets:
#         cmd.append("--log-packets")
    
#     logger.info(f"Starting bots with command: {' '.join(cmd)}")
#     bots_process = subprocess.Popen(cmd)
#     return bots_process

def wait_for_port_availability(host, port, timeout=10, interval=0.5):
    """Wait for a port to become available (server to start listening)"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        try:
            sock.connect((host, port))
            sock.close()
            return True  # Port is open and accepting connections
        except:
            sock.close()
            time.sleep(interval)
    
    return False  # Timed out waiting for port

def main():
    parser = argparse.ArgumentParser(description="Run Luanti server, middleware, and bots")
    parser.add_argument("--server-path", required=True, 
                        help="Path to the Luanti server executable")
    parser.add_argument("--server-dir", default="./basic_server", 
                        help="Base directory for server files")
    parser.add_argument("--server-port", type=int, default=0,
                        help="Port for the server (0 for auto)")
    # parser.add_argument("--middleware-port", type=int, default=0,
    #                     help="Port for the middleware (0 for auto)")
    # parser.add_argument("--num-bots", type=int, default=1,
    #                     help="Number of bots to create (default: 1)")
    # parser.add_argument("--bot-prefix", default="LuantiBot",
    #                     help="Prefix for bot names (default: LuantiBot)")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    # parser.add_argument("--log-packets", action="store_true",
    #                     help="Log packet data")
    parser.add_argument("--no-middleware", action="store_true",
                        help="Skip starting middleware (connect directly)")
    # parser.add_argument("--no-bots", action="store_true",
    #                     help="Skip starting bots (manual connection)")
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Find available ports if not specified
    server_port = args.server_port if args.server_port != 0 else find_available_port(30000)
    if not server_port:
        logger.error("Could not find an available port for the server")
        return 1
    
    middleware_port = None
    if not args.no_middleware:
        middleware_port = args.middleware_port if args.middleware_port != 0 else find_available_port(server_port + 1)
        if not middleware_port:
            logger.error("Could not find an available port for the middleware")
            return 1
    
    logger.info(f"Using server port: {server_port}")
    if middleware_port:
        logger.info(f"Using middleware port: {middleware_port}")
    
    # Start the server
    server_process = run_server(args.server_path, args.server_dir, server_port)
    
    # Wait for server to initialize
    logger.info("Waiting for server to initialize...")
    time.sleep(2)
    
    middleware_process = None
    if not args.no_middleware:
        # Start the middleware
        middleware_process = run_middleware(middleware_port, server_port, args.debug)
        
        # Wait for middleware to initialize
        logger.info("Waiting for middleware to initialize...")
        time.sleep(2)
    
    # bots_process = None
    # if not args.no_bots:
    #     # Start the bots
    #     target_port = middleware_port if middleware_port else server_port
    #     bots_process = run_bots(
    #         target_port, 
    #         args.num_bots, 
    #         args.bot_prefix,
    #         args.log_packets
    #     )
    
    # Print connection info
    logger.info("\nLuanti is now running!")
    logger.info(f"  - Server is running on port {server_port}")
    
    if middleware_process:
        logger.info(f"  - Middleware is listening on port {middleware_port}")
        logger.info(f"  - Connect your client to 127.0.0.1:{middleware_port}")
    else:
        logger.info(f"  - Connect your client directly to 127.0.0.1:{server_port}")
    
    # if bots_process:
    #     logger.info(f"  - {args.num_bots} bots have been started")
    
    logger.info("\nPress Ctrl+C to stop all processes.")
    
    try:
        # Keep the script running until Ctrl+C
        while True:
            time.sleep(1)
            
            # Check if any process exited unexpectedly
            if server_process.poll() is not None:
                logger.error(f"Server process exited unexpectedly with code: {server_process.returncode}")
                break
                
            if middleware_process and middleware_process.poll() is not None:
                logger.error(f"Middleware process exited unexpectedly with code: {middleware_process.returncode}")
                break
                
            # if bots_process and bots_process.poll() is not None:
            #     logger.error(f"Bots process exited unexpectedly with code: {bots_process.returncode}")
            #     break
                
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    finally:
        # Ensure all processes are terminated in reverse order
        # if bots_process and bots_process.poll() is None:
        #     logger.info("Terminating bots...")
        #     bots_process.terminate()
        #     try:
        #         bots_process.wait(timeout=5)
        #     except subprocess.TimeoutExpired:
        #         logger.warning("Bots didn't terminate, killing process...")
        #         bots_process.kill()
        
        if middleware_process and middleware_process.poll() is None:
            logger.info("Terminating middleware...")
            middleware_process.terminate()
            try:
                middleware_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Middleware didn't terminate, killing process...")
                middleware_process.kill()
        
        if server_process.poll() is None:
            logger.info("Terminating server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Server didn't terminate, killing process...")
                server_process.kill()
    
    logger.info("All processes terminated. Exiting.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 