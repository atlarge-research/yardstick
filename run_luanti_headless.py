#!/usr/bin/env python3
"""
Deploy and run Luanti headless server on DAS5.
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run a command and handle errors."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=check, 
                               capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Return code: {e.returncode}")
        print(f"Error output: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def deploy_luanti_headless():
    """Deploy Luanti headless server using Ansible."""
    
    # Working directory for the server
    wd = "/var/scratch/aco237/luanti_headless"
    
    # Path to the deployment playbook
    playbook_path = "yardstick_benchmark/games/luanti/server/luanti_deploy.yml"
    
    print("🚀 Starting Luanti headless server deployment...")
    
    # Check if playbook exists
    if not Path(playbook_path).exists():
        print(f"❌ Playbook not found: {playbook_path}")
        return False
    
    # Prepare Ansible variables
    extra_vars = {
        "wd": wd,
        "game_mode": "minetest_game",
        "ansible_user": "aco237",
        "collector_mod": "yardstick_benchmark/games/luanti/mods/yardstick_collector.lua",
        "luanti_template": "yardstick_benchmark/games/luanti/server/luanti.conf.j2"
    }
    
    # Convert extra_vars to command line format
    extra_vars_str = " ".join([f"{k}='{v}'" for k, v in extra_vars.items()])
    
    # Run Ansible playbook
    ansible_cmd = f"ansible-playbook -i inventory.ini {playbook_path} --extra-vars \"{extra_vars_str}\" -v"
    
    print("📦 Deploying Luanti headless server...")
    result = run_command(ansible_cmd, check=False)
    
    if result.returncode != 0:
        print("❌ Deployment failed!")
        return False
    
    print("✅ Deployment completed successfully!")
    
    # Check if the server binary was created
    server_binary = Path(wd) / "luantiserver"
    if server_binary.exists():
        print(f"✅ Server binary found at: {server_binary}")
    else:
        print(f"❌ Server binary not found at: {server_binary}")
        return False
    
    return True

def start_luanti_server():
    """Start the Luanti headless server."""
    
    wd = "/var/scratch/aco237/luanti_headless"
    server_binary = Path(wd) / "luantiserver"
    
    if not server_binary.exists():
        print(f"❌ Server binary not found: {server_binary}")
        return False
    
    print("🎮 Starting Luanti headless server...")
    
    # Change to working directory and start server
    start_cmd = f"cd {wd} && ./luantiserver --world worlds/benchmark --config luanti.conf --terminal"
    
    print(f"Starting server with command: {start_cmd}")
    print("To connect to the server, use: luanti --go --address 127.0.0.1 --port 30000")
    print("To stop the server, press Ctrl+C")
    
    try:
        # Run server in foreground
        subprocess.run(start_cmd, shell=True, cwd=wd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        return False
    
    return True

def main():
    """Main function."""
    
    if len(sys.argv) > 1 and sys.argv[1] == "start-only":
        # Only start the server (assume it's already deployed)
        success = start_luanti_server()
    else:
        # Deploy and start
        print("🔧 Deploying Luanti headless server...")
        success = deploy_luanti_headless()
        
        if success:
            print("\n" + "="*50)
            input("Press Enter to start the server...")
            success = start_luanti_server()
    
    if success:
        print("✅ All done!")
    else:
        print("❌ Failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
