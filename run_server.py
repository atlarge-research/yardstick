#!/usr/bin/env python3
"""
Simple script to run a Luanti server
"""

import argparse
import subprocess
import time
import os
import signal
import sys
import socket
import logging

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

# Middleware function has been removed

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
    parser = argparse.ArgumentParser(description="Run a basic Luanti server")
    parser.add_argument("--server-path", required=True, 
                        help="Path to the Luanti server executable")
    parser.add_argument("--server-dir", default="./basic_server", 
                        help="Base directory for server files")
    parser.add_argument("--server-port", type=int, default=0,
                        help="Port for the server (0 for auto)")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Find available port if not specified
    server_port = args.server_port if args.server_port != 0 else find_available_port(30000)
    if not server_port:
        logger.error("Could not find an available port for the server")
        return 1
    
    logger.info(f"Using server port: {server_port}")
    
    # Start the server
    server_process = run_server(args.server_path, args.server_dir, server_port)
    
    # Wait for server to initialize
    logger.info("Waiting for server to initialize...")
    time.sleep(2)
    
    # Print connection info
    logger.info("\nLuanti server is now running!")
    logger.info(f"  - Server is running on port {server_port}")
    logger.info(f"  - Connect your client to 127.0.0.1:{server_port}")
    
    logger.info("\nPress Ctrl+C to stop all processes.")
    
    try:
        # Keep the script running until Ctrl+C
        while True:
            time.sleep(1)
            
            # Check if server exited unexpectedly
            if server_process.poll() is not None:
                logger.error(f"Server process exited unexpectedly with code: {server_process.returncode}")
                break
                
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    finally:
        # Ensure server process is terminated
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
