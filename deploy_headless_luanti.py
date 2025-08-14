#!/usr/bin/env python3
"""
Deploy and run Luanti headless server on DAS5 using the official build method.
This script follows the official Luanti headless server documentation.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description, cwd=None):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        print(f"✅ {description} completed successfully")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        return None

def deploy_headless_server():
    """Deploy Luanti headless server using Ansible."""
    
    # Set up working directory
    wd = f"/var/scratch/{os.environ.get('USER', 'user')}/luanti_headless"
    
    # Define paths
    script_dir = Path(__file__).parent
    playbook_path = script_dir / "yardstick_benchmark/games/luanti/server/luanti_deploy.yml"
    luanti_template = script_dir / "yardstick_benchmark/games/luanti/server/luanti.conf.j2"
    collector_mod = script_dir / "yardstick_benchmark/games/luanti/server/collector.lua"
    
    print(f"🚀 Deploying Luanti headless server to: {wd}")
    print(f"📝 Using playbook: {playbook_path}")
    
    if not playbook_path.exists():
        print(f"❌ Playbook not found: {playbook_path}")
        return False
    
    # Build ansible-playbook command
    ansible_cmd = f"""
    ansible-playbook {playbook_path} \\
        -i inventory.ini \\
        --extra-vars "wd={wd}" \\
        --extra-vars "luanti_template={luanti_template}" \\
        --extra-vars "collector_mod={collector_mod}" \\
        --extra-vars "game_mode=minetest_game" \\
        --verbose
    """
    
    result = run_command(ansible_cmd, "Deploying Luanti headless server", cwd=script_dir)
    
    if result is None:
        print("❌ Deployment failed")
        return False
    
    print("✅ Luanti headless server deployed successfully!")
    return wd

def start_headless_server(wd):
    """Start the Luanti headless server."""
    print(f"🎮 Starting Luanti headless server from {wd}")
    
    # Change to working directory
    server_cmd = f"""
    cd {wd} && \\
    ./luantiserver \\
        --world worlds/benchmark \\
        --config luanti.conf \\
        --port 30000 \\
        --terminal \\
        --verbose
    """
    
    print("Server command:")
    print(server_cmd)
    print("\n🎯 To connect to the server:")
    print("   Host: localhost")
    print("   Port: 30000")
    print("\n⚠️  Server will run in interactive mode. Use Ctrl+C to stop.")
    print("=" * 60)
    
    try:
        # Run the server in foreground (interactive mode)
        subprocess.run(server_cmd, shell=True, cwd=wd)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")

def main():
    """Main deployment function."""
    print("🏗️  Luanti Headless Server Deployment (DAS5/Rocky Linux)")
    print("=" * 60)
    
    # Check if we're on a DAS5 node
    hostname = subprocess.run("hostname", shell=True, capture_output=True, text=True).stdout.strip()
    if not any(das in hostname for das in ['das5', 'das-5', 'fs0', 'fs1', 'fs2', 'fs3', 'fs4']):
        print(f"⚠️  Warning: Hostname '{hostname}' doesn't appear to be a DAS5 node")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Deployment cancelled")
            return
    
    # Deploy the server
    wd = deploy_headless_server()
    if not wd:
        sys.exit(1)
    
    # Ask if user wants to start the server immediately
    response = input("\n🎮 Start the server now? (y/N): ")
    if response.lower() == 'y':
        start_headless_server(wd)
    else:
        print(f"\n📍 Server deployed to: {wd}")
        print("To start manually:")
        print(f"  cd {wd}")
        print("  ./luantiserver --world worlds/benchmark --config luanti.conf --port 30000 --terminal")

if __name__ == "__main__":
    main()
