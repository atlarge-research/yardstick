#!/usr/bin/env python3
"""
Simple Extra Ordinance Benchmark Runner

This script sets up a local Extra Ordinance benchmark by creating a symlink
to avoid permission issues with the Luanti.app directory.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

def setup_extra_ordinance_symlink():
    """Create a symlink to make Extra Ordinance available without copying to Luanti.app"""
    
    # Check if Extra Ordinance is downloaded
    source_game = Path("./luanti_server/mods/extra_ordinance")
    if not source_game.exists():
        print("❌ Extra Ordinance not found!")
        print("Please run: curl -L -o extra_ordinance.zip 'https://content.luanti.org/packages/Sumianvoice/extra_ordinance/download/'")
        print("Then: unzip -q extra_ordinance.zip -d temp_mod && mv temp_mod/extra_ordinance luanti_server/mods/")
        return False
    
    # Create games directory in our project
    games_dir = Path("./luanti_games")
    games_dir.mkdir(exist_ok=True)
    
    # Create symlink
    symlink_path = games_dir / "extra_ordinance"
    if symlink_path.exists():
        if symlink_path.is_symlink():
            print("✓ Extra Ordinance symlink already exists")
            return True
        else:
            print("⚠️ Removing existing non-symlink Extra Ordinance directory")
            import shutil
            shutil.rmtree(symlink_path)
    
    try:
        symlink_path.symlink_to(source_game.absolute())
        print(f"✅ Created Extra Ordinance symlink: {symlink_path} -> {source_game}")
        return True
    except Exception as e:
        print(f"❌ Failed to create symlink: {e}")
        return False

def run_extra_ordinance_benchmark(args):
    """Run benchmark with Extra Ordinance using custom games directory"""
    
    if not setup_extra_ordinance_symlink():
        return False
    
    # Build the command
    cmd = [
        "python3", "local_luanti_benchmark.py",
        "--mod-config", "vanilla",  # Use vanilla but we'll override the game
        "--duration", str(args.duration),
        "--bots", str(args.bots),
        "--port", str(args.port),
        "--movement-mode", args.movement_mode
    ]
    
    print("🚀 Starting Extra Ordinance benchmark...")
    print(f"Command: {' '.join(cmd)}")
    
    # Set environment variable to point to our games directory
    env = os.environ.copy()
    env['MINETEST_GAME_PATH'] = str(Path("./luanti_games").absolute())
    
    # Run the benchmark
    try:
        result = subprocess.run(cmd, env=env)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Run Luanti benchmark with Extra Ordinance game",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument("--duration", type=int, default=180,
                       help="Benchmark duration in seconds")
    parser.add_argument("--bots", type=int, default=20,
                       help="Number of bots to spawn")
    parser.add_argument("--port", type=int, default=30003,
                       help="Luanti server port")
    parser.add_argument("--movement-mode", type=str, default="circular",
                       choices=["random", "circular", "straight", "static"],
                       help="Bot movement pattern")
    
    args = parser.parse_args()
    
    print("🎮 Extra Ordinance Benchmark Setup")
    print("=" * 50)
    
    success = run_extra_ordinance_benchmark(args)
    if success:
        print("✅ Benchmark completed successfully!")
    else:
        print("❌ Benchmark failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 