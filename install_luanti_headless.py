#!/usr/bin/env python3
"""
Set up Luanti headless server from the successful build
"""

import shutil
import os
from pathlib import Path

def setup_luanti_server():
    """Set up a proper Luanti server installation."""
    print("Setting up Luanti headless server...")
    
    # Source and destination paths
    build_dir = Path("/tmp/luanti_simple_build/luanti")
    server_dir = Path("/var/scratch/aco237/luantick/luanti_server_headless")
    
    # Clean up existing server directory
    if server_dir.exists():
        print(f"Removing existing server directory: {server_dir}")
        shutil.rmtree(server_dir)
    
    server_dir.mkdir(parents=True)
    
    # Copy essential files
    print("Copying server files...")
    
    # Copy the server binary
    shutil.copy2(build_dir / "bin/luantiserver", server_dir / "luantiserver")
    print("✓ Copied server binary")
    
    # Copy builtin directory (required)
    shutil.copytree(build_dir / "builtin", server_dir / "builtin")
    print("✓ Copied builtin files")
    
    # Copy games if they exist
    games_src = build_dir / "games"
    if games_src.exists():
        shutil.copytree(games_src, server_dir / "games")
        print("✓ Copied games")
    else:
        # Create empty games directory
        (server_dir / "games").mkdir()
        print("✓ Created games directory")
    
    # Create worlds directory
    (server_dir / "worlds").mkdir()
    print("✓ Created worlds directory")
    
    # Create basic server configuration
    config_content = """# Luanti Server Configuration
# Basic server settings
server_name = DAS5 Luanti Test Server
motd = Welcome to the DAS5 Luanti server!
max_users = 20
port = 30000

# World settings
default_game = minetest_game
creative_mode = true
enable_damage = false

# Performance settings
max_simultaneous_block_sends_per_client = 10
max_simultaneous_block_sends_server_total = 40

# Logging
debug_log_level = action
"""
    
    with open(server_dir / "minetest.conf", "w") as f:
        f.write(config_content)
    print("✓ Created server configuration")
    
    # Create start script
    start_script_content = """#!/bin/bash
# Luanti Server Start Script

cd "$(dirname "$0")"

echo "Starting Luanti headless server..."
echo "Server directory: $(pwd)"
echo "Configuration: minetest.conf"
echo "Press Ctrl+C to stop the server"
echo

# Start the server with terminal interface
./luantiserver \\
    --world "testworld" \\
    --config "minetest.conf" \\
    --logfile "server.log" \\
    --terminal \\
    --info
"""
    
    start_script = server_dir / "start_server.sh"
    with open(start_script, "w") as f:
        f.write(start_script_content)
    start_script.chmod(0o755)
    print("✓ Created start script")
    
    # Create background start script  
    bg_script_content = """#!/bin/bash
# Luanti Server Background Start Script

cd "$(dirname "$0")"

echo "Starting Luanti headless server in background..."

# Start the server without terminal interface
nohup ./luantiserver \\
    --world "testworld" \\
    --config "minetest.conf" \\
    --logfile "server.log" \\
    --info > server_output.log 2>&1 &

SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"
echo "$SERVER_PID" > server.pid
echo "Log file: server.log"
echo "Output file: server_output.log"
echo "To stop: kill $SERVER_PID"
"""
    
    bg_script = server_dir / "start_background.sh"
    with open(bg_script, "w") as f:
        f.write(bg_script_content)
    bg_script.chmod(0o755)
    print("✓ Created background start script")
    
    # Create stop script
    stop_script_content = """#!/bin/bash
# Stop Luanti Server

cd "$(dirname "$0")"

if [ -f server.pid ]; then
    PID=$(cat server.pid)
    echo "Stopping server with PID: $PID"
    kill $PID
    rm server.pid
    echo "Server stopped"
else
    echo "No server.pid file found"
    echo "Trying to find and stop luantiserver processes..."
    pkill -f luantiserver
fi
"""
    
    stop_script = server_dir / "stop_server.sh"
    with open(stop_script, "w") as f:
        f.write(stop_script_content)
    stop_script.chmod(0o755)
    print("✓ Created stop script")
    
    # Create README
    readme_content = """# Luanti Headless Server

Successfully built and installed Luanti headless server on DAS5.

## Files:
- `luantiserver` - The server binary
- `minetest.conf` - Server configuration
- `start_server.sh` - Start server with interactive terminal
- `start_background.sh` - Start server in background
- `stop_server.sh` - Stop background server
- `builtin/` - Required builtin files
- `games/` - Game definitions directory  
- `worlds/` - World data directory

## Quick Start:

### Interactive Mode (recommended for testing):
```bash
./start_server.sh
```

### Background Mode:
```bash
./start_background.sh
# Check logs: tail -f server.log
./stop_server.sh
```

### Manual Start:
```bash
./luantiserver --world "testworld" --config "minetest.conf" --logfile "server.log" --terminal
```

## Server Details:
- Port: 30000 (UDP)
- World: testworld (created automatically)
- Max users: 20
- Creative mode: enabled
- Damage: disabled

## Logs:
- `server.log` - Server activity log
- `server_output.log` - Background mode output

## Configuration:
Edit `minetest.conf` to customize server settings.

## Adding Games:
Place game directories in the `games/` folder.
Default game is set to `minetest_game` in the configuration.
"""
    
    with open(server_dir / "README.md", "w") as f:
        f.write(readme_content)
    print("✓ Created README")
    
    print(f"\n🎉 SUCCESS! Luanti headless server installed at: {server_dir}")
    print("\nTo start the server:")
    print(f"  cd {server_dir}")
    print("  ./start_server.sh")
    
    return server_dir

if __name__ == "__main__":
    setup_luanti_server()
