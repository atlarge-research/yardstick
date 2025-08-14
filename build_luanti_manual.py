#!/usr/bin/env python3
"""
Try to build Luanti with minimal dependencies by specifying library paths manually
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

def run_command(cmd, check=True, capture_output=False):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    if capture_output:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if check and result.returncode != 0:
            print(f"Command failed: {result.stderr}")
            return None
        return result
    else:
        result = subprocess.run(cmd, shell=True)
        if check and result.returncode != 0:
            print(f"Command failed with exit code {result.returncode}")
            return None
        return result

def find_system_libraries():
    """Find what libraries are available on the system."""
    print("Scanning system libraries...")
    
    lib_paths = ["/usr/lib64", "/usr/lib", "/lib64", "/lib"]
    include_paths = ["/usr/include"]
    
    found_libs = {}
    found_includes = {}
    
    # Check for key libraries
    key_libs = ["sqlite3", "curl", "z", "gmp", "ncurses"]
    
    for lib_name in key_libs:
        for lib_path in lib_paths:
            lib_file = Path(lib_path) / f"lib{lib_name}.so"
            if lib_file.exists() or Path(f"{lib_file}.0").exists():
                found_libs[lib_name] = lib_path
                print(f"✓ Found lib{lib_name} in {lib_path}")
                break
        else:
            print(f"✗ lib{lib_name} not found")
    
    # Check for includes (likely missing, but let's see)
    key_includes = ["sqlite3.h", "curl.h", "zlib.h", "gmp.h", "ncurses.h"]
    
    for inc_name in key_includes:
        for inc_path in include_paths:
            inc_file = Path(inc_path) / inc_name
            if inc_file.exists():
                found_includes[inc_name] = inc_path
                print(f"✓ Found {inc_name} in {inc_path}")
                break
        else:
            # Check subdirectories
            found = False
            for inc_path in include_paths:
                for subdir in Path(inc_path).glob("*/"):
                    inc_file = subdir / inc_name
                    if inc_file.exists():
                        found_includes[inc_name] = str(subdir)
                        print(f"✓ Found {inc_name} in {subdir}")
                        found = True
                        break
                if found:
                    break
            if not found:
                print(f"✗ {inc_name} not found")
    
    return found_libs, found_includes

def try_cmake_with_manual_paths():
    """Try cmake with manually specified library paths."""
    print("\n" + "="*50)
    print("TRYING CMAKE WITH MANUAL LIBRARY PATHS")
    print("="*50)
    
    work_dir = Path("/tmp/luanti_manual_build")
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir()
    os.chdir(work_dir)
    
    # Clone source
    print("Cloning Luanti source...")
    result = run_command("git clone -b stable-5 --depth 1 https://github.com/luanti-org/luanti.git")
    if not result:
        return False
    
    os.chdir("luanti")
    
    # Find libraries
    found_libs, found_includes = find_system_libraries()
    
    # Create build directory
    build_dir = Path("build")
    build_dir.mkdir()
    os.chdir("build")
    
    # Try to specify library paths manually
    cmake_args = [
        "-DBUILD_CLIENT=0",
        "-DBUILD_SERVER=1", 
        "-DRUN_IN_PLACE=1",
        "-DBUILD_UNITTESTS=0"
    ]
    
    # Add library paths if found
    if "sqlite3" in found_libs:
        # Try to help cmake find sqlite3
        cmake_args.extend([
            f"-DSQLITE3_LIBRARY={found_libs['sqlite3']}/libsqlite3.so",
            "-DSQLITE3_INCLUDE_DIR=/usr/include"  # Guess, may not work
        ])
    
    # Try with bundled libraries to reduce dependencies
    cmake_args.extend([
        "-DENABLE_BUNDLED_JSONCPP=ON",
        "-DENABLE_BUNDLED_GMP=ON"
    ])
    
    cmake_cmd = f"cmake .. {' '.join(cmake_args)}"
    
    result = run_command(cmake_cmd, check=False, capture_output=True)
    
    if result and result.returncode == 0:
        print("✓ CMake configuration successful with manual paths!")
        
        # Try to build
        print("Attempting build...")
        build_result = run_command("make -j$(nproc)", check=False, capture_output=True)
        
        if build_result and build_result.returncode == 0:
            print("✓ Build successful!")
            
            binary_path = Path("bin/luantiserver")
            if binary_path.exists():
                print(f"✓ Server binary created: {binary_path.absolute()}")
                return binary_path.absolute()
            else:
                print("✗ Binary not found after build")
                return False
        else:
            print("✗ Build failed")
            if build_result:
                print("Build errors (last 500 chars):")
                print(build_result.stderr[-500:])
            return False
    else:
        print("✗ CMake configuration still failed")
        if result:
            print("CMake errors:")
            print(result.stderr)
        return False

def create_simple_test_server():
    """Create a very simple test server in Python to verify networking."""
    print("\n" + "="*50)
    print("CREATING SIMPLE TEST SERVER")
    print("="*50)
    
    test_dir = Path("/var/scratch/aco237/luantick/simple_test_server")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    # Create a simple UDP server that mimics basic Luanti protocol
    server_code = '''#!/usr/bin/env python3
"""
Simple test server for Luanti protocol testing
This creates a UDP server on port 30000 that can receive connections from bots.
"""

import socket
import threading
import time
import sys

class SimpleTestServer:
    def __init__(self, host="0.0.0.0", port=30000):
        self.host = host
        self.port = port
        self.running = False
        self.clients = {}
        self.stats = {"connections": 0, "packets": 0}
        
    def start(self):
        """Start the test server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((self.host, self.port))
            self.socket.settimeout(1.0)  # 1 second timeout for recv
            self.running = True
            
            print(f"Simple test server started on {self.host}:{self.port}")
            print("This server accepts UDP packets and responds with basic acknowledgments")
            print("Press Ctrl+C to stop")
            print("-" * 50)
            
            while self.running:
                try:
                    data, addr = self.socket.recvfrom(1024)
                    self.handle_packet(data, addr)
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Error handling packet: {e}")
                        
        except KeyboardInterrupt:
            print("\\nServer stopped by user")
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.cleanup()
    
    def handle_packet(self, data, addr):
        """Handle incoming packet."""
        self.stats["packets"] += 1
        
        # Track new clients
        if addr not in self.clients:
            self.clients[addr] = {"first_seen": time.time(), "packet_count": 0}
            self.stats["connections"] += 1
            print(f"New client: {addr[0]}:{addr[1]}")
        
        self.clients[addr]["packet_count"] += 1
        
        # Log packet info
        packet_info = f"Packet from {addr[0]}:{addr[1]} - {len(data)} bytes"
        if len(data) > 0:
            # Show first few bytes as hex
            hex_data = " ".join(f"{b:02x}" for b in data[:min(16, len(data))])
            packet_info += f" - Data: {hex_data}"
            if len(data) > 16:
                packet_info += "..."
        
        print(packet_info)
        
        # Send a simple response
        response = b"ACK" + data[:4]  # Echo first 4 bytes
        try:
            self.socket.sendto(response, addr)
        except Exception as e:
            print(f"Failed to send response to {addr}: {e}")
        
        # Print stats every 10 packets
        if self.stats["packets"] % 10 == 0:
            self.print_stats()
    
    def print_stats(self):
        """Print current statistics."""
        print(f"Stats: {self.stats['connections']} clients, {self.stats['packets']} packets")
    
    def cleanup(self):
        """Clean up server resources."""
        self.running = False
        if hasattr(self, 'socket'):
            self.socket.close()
        
        print("\\nFinal Statistics:")
        print(f"  Total clients: {self.stats['connections']}")
        print(f"  Total packets: {self.stats['packets']}")
        
        if self.clients:
            print("\\nClient details:")
            for addr, info in self.clients.items():
                duration = time.time() - info['first_seen']
                print(f"  {addr[0]}:{addr[1]} - {info['packet_count']} packets over {duration:.1f}s")

if __name__ == "__main__":
    server = SimpleTestServer()
    server.start()
'''
    
    server_file = test_dir / "simple_server.py"
    with open(server_file, "w") as f:
        f.write(server_code)
    server_file.chmod(0o755)
    
    # Create start script
    start_script = test_dir / "start_server.sh"
    with open(start_script, "w") as f:
        f.write("#!/bin/bash\\necho 'Starting simple test server...'\\npython3 simple_server.py\\n")
    start_script.chmod(0o755)
    
    # Create test script
    test_script = test_dir / "test_connection.py" 
    test_code = '''#!/usr/bin/env python3
"""Test connection to the simple server"""

import socket
import time

def test_connection(host="localhost", port=30000):
    """Test UDP connection to server."""
    print(f"Testing connection to {host}:{port}")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        # Send test packet
        test_data = b"HELLO_FROM_TEST_CLIENT"
        sock.sendto(test_data, (host, port))
        print(f"Sent: {test_data}")
        
        # Wait for response
        sock.settimeout(5.0)
        response, addr = sock.recvfrom(1024)
        print(f"Received: {response} from {addr}")
        
        return True
        
    except socket.timeout:
        print("No response received (timeout)")
        return False
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False
    finally:
        sock.close()

if __name__ == "__main__":
    success = test_connection()
    print("Connection test:", "PASSED" if success else "FAILED")
'''
    
    with open(test_script, "w") as f:
        f.write(test_code)
    test_script.chmod(0o755)
    
    print(f"✓ Simple test server created in: {test_dir}")
    print("Files created:")
    print(f"  {test_dir}/simple_server.py - Main server")
    print(f"  {test_dir}/start_server.sh - Start script")
    print(f"  {test_dir}/test_connection.py - Connection test")
    
    return test_dir

def main():
    """Main function."""
    print("Manual Luanti Build Attempt for DAS5")
    print("="*50)
    
    # Try building with manual library paths
    binary_path = try_cmake_with_manual_paths()
    
    if binary_path:
        print("\\n" + "="*50)
        print("BUILD SUCCESSFUL!")
        print("="*50)
        print(f"Luanti server binary: {binary_path}")
        print("\\nYou can now test the server.")
    else:
        print("\\n" + "="*50)
        print("BUILD FAILED - CREATING SIMPLE TEST SERVER")
        print("="*50)
        print("Since Luanti build failed due to missing development headers,")
        print("creating a simple test server for protocol testing...")
        
        test_dir = create_simple_test_server()
        
        print("\\n" + "="*50)
        print("NEXT STEPS")
        print("="*50)
        print("1. You can use the simple test server for basic protocol testing:")
        print(f"   cd {test_dir}")
        print("   ./start_server.sh")
        print("")
        print("2. To get a real Luanti server, you would need to install development packages:")
        print("   Ask your system administrator to install: sqlite-devel")
        print("   (This requires root access)")
        print("")
        print("3. Alternatively, you could:")
        print("   - Use a container/Docker with the pre-built binary")
        print("   - Build on a different system and copy the binary")
        print("   - Use the simple test server for basic networking tests")

if __name__ == "__main__":
    main()
