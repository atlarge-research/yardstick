#!/usr/bin/env python3
"""
Build Luanti headless server from source on DAS5 (Rocky Linux)
This script checks dependencies and builds a minimal headless server.
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
            sys.exit(1)
        return result
    else:
        result = subprocess.run(cmd, shell=True)
        if check and result.returncode != 0:
            print(f"Command failed with exit code {result.returncode}")
            sys.exit(1)
        return result

def check_command_exists(cmd):
    """Check if a command exists on the system."""
    result = subprocess.run(f"which {cmd}", shell=True, capture_output=True)
    return result.returncode == 0

def check_package_installed(package):
    """Check if a package is installed on Rocky Linux."""
    result = subprocess.run(f"rpm -q {package}", shell=True, capture_output=True)
    return result.returncode == 0

def install_dependencies():
    """Check for required dependencies on DAS5 - skip installation if not available."""
    print("Checking for required dependencies on DAS5...")
    
    # Essential build tools - these should be available via modules on DAS5
    essential_commands = {
        "g++": "gcc-c++",
        "cmake": "cmake", 
        "make": "make",
        "git": "git"
    }
    
    # Check for essential commands
    missing_commands = []
    for cmd, pkg in essential_commands.items():
        if check_command_exists(cmd):
            print(f"✓ {cmd} is available")
        else:
            print(f"❌ {cmd} not found")
            missing_commands.append(cmd)
    
    # Check for development headers by looking for key files
    dev_checks = {
        "sqlite3": ["/usr/include/sqlite3.h", "/usr/local/include/sqlite3.h"],
        "curl": ["/usr/include/curl/curl.h", "/usr/local/include/curl/curl.h"],
        "zlib": ["/usr/include/zlib.h", "/usr/local/include/zlib.h"],
        "gmp": ["/usr/include/gmp.h", "/usr/local/include/gmp.h"],
        "jsoncpp": ["/usr/include/jsoncpp/json/json.h", "/usr/local/include/jsoncpp/json/json.h"],
        "ncurses": ["/usr/include/ncurses.h", "/usr/local/include/ncurses.h"]
    }
    
    missing_dev = []
    for lib, paths in dev_checks.items():
        found = False
        for path in paths:
            if Path(path).exists():
                print(f"✓ {lib} development headers found at {path}")
                found = True
                break
        if not found:
            print(f"⚠️  {lib} development headers not found")
            missing_dev.append(lib)
    
    # Check if ninja is available
    ninja_available = check_command_exists("ninja")
    if not ninja_available:
        print("⚠️  ninja not available, will use make instead")
    else:
        print("✓ ninja is available")
    
    # On DAS5, don't try to install packages - just warn and continue
    if missing_commands or missing_dev:
        print(f"\n⚠️  Some dependencies may be missing:")
        if missing_commands:
            print(f"   Commands: {', '.join(missing_commands)}")
        if missing_dev:
            print(f"   Dev libraries: {', '.join(missing_dev)}")
        
        print("\nOn DAS5, you may need to load modules. Try:")
        print("   module load cmake")
        print("   module load gcc")
        print("   module avail  # to see available modules")
        print("\nContinuing anyway - CMake will report specific missing dependencies...")
        
        # Don't exit - let CMake handle the detailed dependency checking
    else:
        print("✓ All essential dependencies appear to be available")
    
    return ninja_available

def build_luajit():
    """Build LuaJIT from source."""
    print("\n" + "="*50)
    print("BUILDING LUAJIT")
    print("="*50)
    
    luajit_dir = Path("luajit")
    
    if luajit_dir.exists():
        print("LuaJIT directory already exists, cleaning...")
        shutil.rmtree(luajit_dir)
    
    # Clone LuaJIT
    run_command("git clone https://github.com/LuaJIT/LuaJIT luajit")
    
    # Build LuaJIT
    os.chdir("luajit")
    run_command("make amalg")
    os.chdir("..")
    
    print("✓ LuaJIT built successfully")

def build_luanti(use_ninja=True):
    """Build Luanti from source."""
    print("\n" + "="*50)
    print("BUILDING LUANTI")
    print("="*50)
    
    luanti_dir = Path("luanti")
    
    if luanti_dir.exists():
        print("Luanti directory already exists, cleaning...")
        shutil.rmtree(luanti_dir)
    
    # Clone Luanti (stable version)
    run_command("git clone -b stable-5 --depth 1 https://github.com/luanti-org/luanti.git")
    
    os.chdir("luanti")
    
    # Create build directory
    build_dir = Path("build")
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    
    os.chdir("build")
    
    # Configure with cmake
    generator = "-G Ninja" if use_ninja else ""
    build_command = "ninja" if use_ninja else "make -j$(nproc)"
    
    cmake_cmd = f"""cmake .. {generator} \
        -DBUILD_CLIENT=0 \
        -DBUILD_SERVER=1 \
        -DRUN_IN_PLACE=1 \
        -DBUILD_UNITTESTS=0 \
        -DLUA_INCLUDE_DIR=../../luajit/src/ \
        -DLUA_LIBRARY=../../luajit/src/libluajit.a"""
    
    run_command(cmake_cmd)
    
    # Build
    run_command(build_command)
    
    os.chdir("../..")
    
    print("✓ Luanti built successfully")
    
    # Check if binary was created
    binary_path = Path("luanti/build/bin/luantiserver")
    if binary_path.exists():
        print(f"✓ Server binary created: {binary_path}")
        # Make it executable
        binary_path.chmod(0o755)
        return binary_path
    else:
        print("✗ Server binary not found!")
        sys.exit(1)

def setup_test_server(binary_path):
    """Set up a minimal test server configuration."""
    print("\n" + "="*50)
    print("SETTING UP TEST SERVER")
    print("="*50)
    
    server_dir = Path("test_server")
    if server_dir.exists():
        shutil.rmtree(server_dir)
    server_dir.mkdir()
    
    # Copy necessary files
    shutil.copytree("luanti/builtin", server_dir / "builtin")
    shutil.copy(binary_path, server_dir / "luantiserver")
    
    # Create a minimal minetest.conf
    conf_content = """
# Minimal server configuration for testing
server_name = Test Luanti Server
motd = Welcome to the test server!
max_users = 10
port = 30000
default_game = minetest_game
creative_mode = true
enable_damage = false
"""
    
    with open(server_dir / "minetest.conf", "w") as f:
        f.write(conf_content.strip())
    
    # Create worlds directory
    (server_dir / "worlds").mkdir()
    
    # Create games directory and check if minetest_game exists
    games_dir = server_dir / "games"
    games_dir.mkdir()
    
    luanti_games_dir = Path("luanti/games")
    if luanti_games_dir.exists():
        # Copy available games
        for game_dir in luanti_games_dir.iterdir():
            if game_dir.is_dir():
                shutil.copytree(game_dir, games_dir / game_dir.name)
                print(f"✓ Copied game: {game_dir.name}")
    
    # Create a simple start script
    start_script = server_dir / "start_server.sh"
    with open(start_script, "w") as f:
        f.write("""#!/bin/bash
echo "Starting Luanti headless server..."
./luantiserver --world "testworld" --config "minetest.conf" --logfile "server.log" --terminal
""")
    start_script.chmod(0o755)
    
    print(f"✓ Test server set up in: {server_dir}")
    return server_dir

def test_server(server_dir):
    """Test that the server can start."""
    print("\n" + "="*50)
    print("TESTING SERVER")
    print("="*50)
    
    os.chdir(server_dir)
    
    print("Testing server startup (will run for 10 seconds)...")
    
    # Test server startup
    try:
        # Run server in background for a few seconds to test startup
        import signal
        import time
        
        # Start server process
        proc = subprocess.Popen(
            ["./luantiserver", "--world", "testworld", "--config", "minetest.conf", 
             "--logfile", "server.log"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a bit for startup
        time.sleep(5)
        
        # Check if process is still running (good sign)
        if proc.poll() is None:
            print("✓ Server started successfully!")
            
            # Terminate gracefully
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            
            print("✓ Server stopped cleanly")
            
            # Check if log file was created
            if Path("server.log").exists():
                print("✓ Server log file created")
                # Show first few lines of log
                with open("server.log", "r") as f:
                    lines = f.readlines()[:10]
                    if lines:
                        print("Server log preview:")
                        for line in lines:
                            print(f"  {line.strip()}")
            
            return True
            
        else:
            print("✗ Server process exited immediately")
            stdout, stderr = proc.communicate()
            if stdout:
                print(f"STDOUT: {stdout.decode()}")
            if stderr:
                print(f"STDERR: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing server: {e}")
        return False
    finally:
        os.chdir("..")

def main():
    """Main build and test process."""
    print("Luanti Headless Server Builder for DAS5")
    print("="*50)
    
    # Check basic requirements
    if not check_command_exists("git"):
        print("✗ git is required but not found")
        sys.exit(1)
    
    work_dir = Path("/tmp/luanti_build")
    if work_dir.exists():
        print(f"Cleaning previous build directory: {work_dir}")
        shutil.rmtree(work_dir)
    
    work_dir.mkdir(parents=True)
    os.chdir(work_dir)
    print(f"Working in: {work_dir}")
    
    try:
        # Step 1: Install dependencies
        use_ninja = install_dependencies()
        
        # Step 2: Build LuaJIT
        build_luajit()
        
        # Step 3: Build Luanti
        binary_path = build_luanti(use_ninja)
        
        # Step 4: Set up test server
        server_dir = setup_test_server(binary_path)
        
        # Step 5: Test server
        success = test_server(server_dir)
        
        if success:
            print("\n" + "="*50)
            print("BUILD SUCCESSFUL!")
            print("="*50)
            print(f"Server directory: {work_dir / server_dir}")
            print("To run the server:")
            print(f"  cd {work_dir / server_dir}")
            print("  ./start_server.sh")
            print("\nYou can copy this directory to your desired location.")
        else:
            print("\n" + "="*50)
            print("BUILD COMPLETED BUT SERVER TEST FAILED")
            print("="*50)
            print("The binary was built but may have runtime issues.")
            print(f"Check the server directory: {work_dir / server_dir}")
    
    except KeyboardInterrupt:
        print("\nBuild interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nBuild failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
