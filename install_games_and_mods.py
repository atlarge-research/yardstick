#!/usr/bin/env python3
"""
Download and Install Games for Luanti Server
This script downloads minetest_game and extra_ordinance and sets up a complete server.
"""

import subprocess
import sys
import os
import shutil
import zipfile
import tempfile
from pathlib import Path
import urllib.request

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

def download_file(url, filename):
    """Download a file from URL."""
    print(f"Downloading {filename} from {url}")
    try:
        urllib.request.urlretrieve(url, filename)
        print(f"✓ Downloaded {filename}")
        return True
    except Exception as e:
        print(f"✗ Failed to download {filename}: {e}")
        return False

def extract_zip(zip_path, extract_to):
    """Extract a zip file."""
    print(f"Extracting {zip_path} to {extract_to}")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"✓ Extracted {zip_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to extract {zip_path}: {e}")
        return False

def setup_server_directory():
    """Set up or find the server directory."""
    # First check if we already have a server directory
    existing_dirs = [
        Path("/var/scratch/aco237/luantick/luanti_server_headless"),
        Path("/var/scratch/aco237/luantick/luanti_server"),
        Path("/tmp/luanti_server_complete")
    ]
    
    server_dir = None
    for dir_path in existing_dirs:
        if dir_path.exists() and (dir_path / "luantiserver").exists():
            server_dir = dir_path
            print(f"✓ Found existing server at: {server_dir}")
            break
    
    if not server_dir:
        # Create new server directory
        server_dir = Path("/var/scratch/aco237/luantick/luanti_server_complete")
        print(f"Creating new server directory: {server_dir}")
        server_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy server binary if available
        binary_source = Path("/tmp/luanti_simple_build/luanti/bin/luantiserver")
        builtin_source = Path("/tmp/luanti_simple_build/luanti/builtin")
        
        if binary_source.exists():
            binary_dest = server_dir / "luantiserver"
            shutil.copy2(binary_source, binary_dest)
            binary_dest.chmod(0o755)
            print(f"✓ Copied server binary to {binary_dest}")
            
            if builtin_source.exists():
                builtin_dest = server_dir / "builtin"
                if builtin_dest.exists():
                    shutil.rmtree(builtin_dest)
                shutil.copytree(builtin_source, builtin_dest)
                print(f"✓ Copied builtin directory to {builtin_dest}")
        else:
            print("⚠️  No server binary found. Please build Luanti first:")
            print("   python3 build_luanti_minimal.py")
    
    # Create subdirectories
    for subdir in ["games", "mods", "worlds", "logs"]:
        (server_dir / subdir).mkdir(exist_ok=True)
    
    return server_dir

def download_and_install_games(server_dir):
    """Download and install minetest_game and extra_ordinance."""
    games_dir = server_dir / "games"
    mods_dir = server_dir / "mods"
    
    # URLs for downloads
    downloads = {
        "minetest_game": {
            "url": "https://content.luanti.org/packages/Luanti/minetest_game/releases/31762/download/",
            "filename": "minetest_game.zip",
            "type": "game",
            "install_dir": games_dir
        },
        "extra_ordinance": {
            "url": "https://content.luanti.org/packages/Sumianvoice/extra_ordinance/releases/28707/download/",
            "filename": "extra_ordinance.zip", 
            "type": "mod",
            "install_dir": mods_dir
        }
    }
    
    temp_dir = Path(tempfile.mkdtemp())
    print(f"Using temporary directory: {temp_dir}")
    
    try:
        for name, info in downloads.items():
            print(f"\n{'='*50}")
            print(f"INSTALLING {name.upper()}")
            print(f"{'='*50}")
            
            # Check if already installed
            install_path = info["install_dir"] / name
            if install_path.exists():
                print(f"✓ {name} already installed at {install_path}")
                continue
            
            # Download
            zip_path = temp_dir / info["filename"]
            if not download_file(info["url"], zip_path):
                continue
            
            # Extract to temporary location
            extract_temp = temp_dir / f"{name}_extract"
            extract_temp.mkdir()
            if not extract_zip(zip_path, extract_temp):
                continue
            
            # Find the actual content directory
            extracted_items = list(extract_temp.iterdir())
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                # Single directory, use it
                content_dir = extracted_items[0]
            else:
                # Multiple items, use the extract directory itself
                content_dir = extract_temp
            
            # Install to the correct location
            if install_path.exists():
                shutil.rmtree(install_path)
            
            shutil.copytree(content_dir, install_path)
            print(f"✓ Installed {name} to {install_path}")
            
            # For games, check if it has the required files
            if info["type"] == "game":
                game_conf = install_path / "game.conf"
                if game_conf.exists():
                    print(f"✓ Game configuration found: {game_conf}")
                    with open(game_conf, 'r') as f:
                        content = f.read()[:200]
                        print(f"  Game config preview: {content}...")
                else:
                    print(f"⚠️  No game.conf found in {install_path}")
                    # List contents to see what we have
                    contents = list(install_path.iterdir())[:10]
                    print(f"  Contents: {[p.name for p in contents]}")
    
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        print(f"✓ Cleaned up temporary directory")
    
    return True

def create_server_config(server_dir):
    """Create server configuration files."""
    config_content = """# Luanti Server Configuration
# Basic server settings
server_name = DAS5 Luanti Server with Extra Ordinance
server_description = Luanti server running on DAS5 cluster with extra_ordinance mod
motd = Welcome to the DAS5 Luanti Server! Extra Ordinance enabled.

# Network settings
port = 30000
bind_address = 0.0.0.0
max_users = 20

# Game settings
default_game = minetest_game
creative_mode = false
enable_damage = true
enable_pvp = true

# Mod settings - enable extra_ordinance
load_mod_extra_ordinance = true

# World settings
enable_rollback_recording = true
max_clearobjects_extra_loaded_blocks = 4096

# Performance settings
max_block_send_distance = 10
max_block_generate_distance = 8
active_block_range = 3

# Security settings
enable_client_modding = false
csm_restriction_flags = 62
csm_restriction_noderange = 0

# Logging
debug_log_level = info
"""
    
    config_file = server_dir / "minetest.conf"
    with open(config_file, 'w') as f:
        f.write(config_content)
    print(f"✓ Created server configuration: {config_file}")

def create_startup_scripts(server_dir):
    """Create startup and management scripts."""
    
    # Simple start script
    start_script_content = f"""#!/bin/bash
cd {server_dir}
echo "Starting Luanti server with extra_ordinance..."
echo "Server directory: {server_dir}"
echo "Game: minetest_game"
echo "Mod: extra_ordinance"
echo "Press Ctrl+C to stop"
echo "========================"
./luantiserver --world "world" --config "minetest.conf" --logfile "logs/server.log" --terminal
"""
    
    start_script = server_dir / "start_server.sh"
    with open(start_script, 'w') as f:
        f.write(start_script_content)
    start_script.chmod(0o755)
    print(f"✓ Created start script: {start_script}")
    
    # Background start script
    start_bg_script_content = f"""#!/bin/bash
cd {server_dir}
echo "Starting Luanti server in background..."
nohup ./luantiserver --world "world" --config "minetest.conf" --logfile "logs/server.log" > logs/console.log 2>&1 &
echo $! > server.pid
echo "Server started with PID $(cat server.pid)"
echo "Log: tail -f {server_dir}/logs/server.log"
echo "Console: tail -f {server_dir}/logs/console.log"
echo "Stop: {server_dir}/stop_server.sh"
"""
    
    start_bg_script = server_dir / "start_server_background.sh"
    with open(start_bg_script, 'w') as f:
        f.write(start_bg_script_content)
    start_bg_script.chmod(0o755)
    print(f"✓ Created background start script: {start_bg_script}")
    
    # Stop script
    stop_script_content = f"""#!/bin/bash
cd {server_dir}
if [ -f server.pid ]; then
    PID=$(cat server.pid)
    echo "Stopping server with PID $PID..."
    kill $PID
    rm server.pid
    echo "Server stopped"
else
    echo "No server.pid file found"
    echo "Trying to kill any luantiserver processes..."
    pkill luantiserver
fi
"""
    
    stop_script = server_dir / "stop_server.sh"
    with open(stop_script, 'w') as f:
        f.write(stop_script_content)
    stop_script.chmod(0o755)
    print(f"✓ Created stop script: {stop_script}")

def verify_installation(server_dir):
    """Verify that everything is installed correctly."""
    print(f"\n{'='*50}")
    print("VERIFYING INSTALLATION")
    print(f"{'='*50}")
    
    # Check server binary
    binary = server_dir / "luantiserver"
    if binary.exists():
        print(f"✓ Server binary: {binary}")
    else:
        print(f"✗ Server binary missing: {binary}")
        return False
    
    # Check builtin
    builtin = server_dir / "builtin"
    if builtin.exists():
        print(f"✓ Builtin directory: {builtin}")
    else:
        print(f"✗ Builtin directory missing: {builtin}")
        return False
    
    # Check game
    game_dir = server_dir / "games" / "minetest_game"
    if game_dir.exists():
        print(f"✓ Game installed: {game_dir}")
        game_conf = game_dir / "game.conf"
        if game_conf.exists():
            print(f"✓ Game configuration: {game_conf}")
        else:
            print(f"⚠️  Game configuration missing: {game_conf}")
    else:
        print(f"✗ Game missing: {game_dir}")
    
    # Check mod
    mod_dir = server_dir / "mods" / "extra_ordinance"
    if mod_dir.exists():
        print(f"✓ Mod installed: {mod_dir}")
        mod_conf = mod_dir / "mod.conf"
        if mod_conf.exists():
            print(f"✓ Mod configuration: {mod_conf}")
        else:
            print(f"⚠️  Mod configuration missing: {mod_conf}")
    else:
        print(f"✗ Mod missing: {mod_dir}")
    
    # Check configuration
    config = server_dir / "minetest.conf"
    if config.exists():
        print(f"✓ Server configuration: {config}")
    else:
        print(f"✗ Server configuration missing: {config}")
    
    return True

def main():
    """Main setup function."""
    print("Luanti Server Game and Mod Installation")
    print("="*60)
    
    # Step 1: Set up directory structure
    server_dir = setup_server_directory()
    
    # Step 2: Download and install games/mods
    download_and_install_games(server_dir)
    
    # Step 3: Create configuration
    create_server_config(server_dir)
    
    # Step 4: Create startup scripts
    create_startup_scripts(server_dir)
    
    # Step 5: Verify installation
    verify_installation(server_dir)
    
    print(f"\n{'='*60}")
    print("INSTALLATION COMPLETE!")
    print("="*60)
    print(f"Luanti server with games and mods ready at: {server_dir}")
    print("\nContents:")
    print(f"  • Server binary: luantiserver")
    print(f"  • Game: minetest_game")
    print(f"  • Mod: extra_ordinance")
    print(f"  • Configuration: minetest.conf")
    print("\nTo start the server:")
    print(f"  cd {server_dir}")
    print("  ./start_server.sh")
    print("\nTo start in background:")
    print("  ./start_server_background.sh")
    print("\nTo stop:")
    print("  ./stop_server.sh")

if __name__ == "__main__":
    main()
