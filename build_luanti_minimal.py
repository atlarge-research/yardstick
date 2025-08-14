#!/usr/bin/env python3
"""
Minimal Luanti headless server builder for DAS5
This version tries to build with minimal dependencies and falls back gracefully.
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

def check_build_tools():
    """Check if basic build tools are available."""
    print("Checking build tools...")
    
    tools = {
        'gcc': '/opt/ohpc/pub/compiler/gcc/12.4.0/bin/gcc',
        'g++': '/opt/ohpc/pub/compiler/gcc/12.4.0/bin/g++', 
        'cmake': '/usr/bin/cmake',
        'git': '/usr/bin/git',
        'make': '/usr/bin/make'
    }
    
    missing = []
    for tool, path in tools.items():
        if Path(path).exists():
            print(f"✓ {tool}: {path}")
        else:
            missing.append(tool)
            print(f"✗ {tool}: not found")
    
    if missing:
        print(f"Missing tools: {missing}")
        return False
    return True

def try_simple_build():
    """Try building Luanti with whatever is available."""
    print("\n" + "="*50)
    print("ATTEMPTING SIMPLE BUILD")
    print("="*50)
    
    work_dir = Path("/tmp/luanti_simple_build")
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir()
    os.chdir(work_dir)
    
    # First, let's just try to get the source and see what cmake says
    print("Cloning Luanti source...")
    result = run_command("git clone -b stable-5 --depth 1 https://github.com/luanti-org/luanti.git")
    if not result:
        print("Failed to clone Luanti")
        return False
    
    os.chdir("luanti")
    
    # Try to configure with cmake to see what's missing
    print("Trying cmake configuration...")
    build_dir = Path("build")
    build_dir.mkdir()
    os.chdir("build")
    
    # Try with system paths and available libraries
    cmake_cmd = """cmake .. \
        -DBUILD_CLIENT=0 \
        -DBUILD_SERVER=1 \
        -DRUN_IN_PLACE=1 \
        -DBUILD_UNITTESTS=0 \
        -DCMAKE_BUILD_TYPE=Release \
        -DENABLE_CURL=ON \
        -DENABLE_LEVELDB=OFF \
        -DENABLE_POSTGRESQL=OFF \
        -DENABLE_REDIS=OFF \
        -DENABLE_PROMETHEUS=OFF"""
    
    result = run_command(cmake_cmd, check=False, capture_output=True)
    
    if result and result.returncode == 0:
        print("✓ CMake configuration successful!")
        
        # Try to build
        print("Attempting build...")
        build_result = run_command("make -j$(nproc)", check=False, capture_output=True)
        
        if build_result and build_result.returncode == 0:
            print("✓ Build successful!")
            
            # Check if binary exists
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
                print("Build errors:")
                print(build_result.stderr[-1000:])  # Last 1000 chars
            return False
    else:
        print("✗ CMake configuration failed")
        if result:
            print("CMake errors:")
            print(result.stderr)
        
        # Check what dependencies are missing
        if result and "Could NOT find" in result.stderr:
            missing_deps = []
            for line in result.stderr.split('\n'):
                if "Could NOT find" in line:
                    missing_deps.append(line.strip())
            
            print("\nMissing dependencies:")
            for dep in missing_deps:
                print(f"  {dep}")
        
        return False

def create_mock_server():
    """Create a simple mock server for testing purposes."""
    print("\n" + "="*50)
    print("CREATING MOCK SERVER")
    print("="*50)
    
    mock_dir = Path("/tmp/mock_luanti_server")
    if mock_dir.exists():
        shutil.rmtree(mock_dir)
    mock_dir.mkdir()
    
    # Create a simple Python-based mock server for testing
    mock_server_code = '''#!/usr/bin/env python3
"""
Mock Luanti Server for testing network protocols
This simulates a basic Luanti server for testing bot connections.
"""

import socket
import threading
import time
import struct

class MockLuantiServer:
    def __init__(self, host="0.0.0.0", port=30000):
        self.host = host
        self.port = port
        self.running = False
        self.clients = []
        
    def start(self):
        """Start the mock server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.running = True
        
        print(f"Mock Luanti server started on {self.host}:{self.port}")
        print("Press Ctrl+C to stop")
        
        try:
            while self.running:
                try:
                    data, addr = self.socket.recvfrom(1024)
                    print(f"Received {len(data)} bytes from {addr}")
                    
                    # Send a basic response (mock protocol)
                    response = b"MOCK_LUANTI_RESPONSE"
                    self.socket.sendto(response, addr)
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error: {e}")
                    
        except KeyboardInterrupt:
            print("\\nServer stopped by user")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up server resources."""
        self.running = False
        if hasattr(self, 'socket'):
            self.socket.close()

if __name__ == "__main__":
    server = MockLuantiServer()
    server.start()
'''
    
    mock_server_file = mock_dir / "mock_server.py"
    with open(mock_server_file, "w") as f:
        f.write(mock_server_code)
    mock_server_file.chmod(0o755)
    
    # Create a start script
    start_script = mock_dir / "start_mock_server.sh"
    with open(start_script, "w") as f:
        f.write("#!/bin/bash\npython3 mock_server.py\n")
    start_script.chmod(0o755)
    
    print(f"✓ Mock server created in: {mock_dir}")
    return mock_dir

def test_network_connectivity():
    """Test basic network connectivity for server functionality."""
    print("\n" + "="*50)
    print("TESTING NETWORK CONNECTIVITY")
    print("="*50)
    
    # Test if we can bind to the Luanti port
    import socket
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        test_socket.bind(("0.0.0.0", 30000))
        test_socket.close()
        print("✓ Can bind to port 30000")
        return True
    except Exception as e:
        print(f"✗ Cannot bind to port 30000: {e}")
        return False

def main():
    """Main function."""
    print("Minimal Luanti Server Setup for DAS5")
    print("="*50)
    
    # Step 1: Check build tools
    if not check_build_tools():
        print("Missing essential build tools. Cannot proceed with compilation.")
        print("Falling back to mock server for testing...")
        mock_dir = create_mock_server()
        test_network_connectivity()
        print(f"\nMock server available at: {mock_dir}")
        print("Run: cd {mock_dir} && ./start_mock_server.sh")
        return
    
    # Step 2: Try simple build
    print("Build tools available. Attempting to build from source...")
    binary_path = try_simple_build()
    
    if binary_path:
        print("\n" + "="*50)
        print("BUILD SUCCESSFUL!")
        print("="*50)
        print(f"Luanti server binary: {binary_path}")
        print("\nYou can now run the server with:")
        print(f"  {binary_path} --help")
    else:
        print("\n" + "="*50)
        print("BUILD FAILED - CREATING MOCK SERVER")
        print("="*50)
        print("Creating mock server for testing purposes...")
        mock_dir = create_mock_server()
        test_network_connectivity()
        print(f"Mock server available at: {mock_dir}")
        print("Run: cd {mock_dir} && ./start_mock_server.sh")

if __name__ == "__main__":
    main()
