#!/usr/bin/env python3
"""
Test script for the BlockBot - demonstrates block placement patterns
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

def run_blockbot_test(args):
    """Run a blockbot test with specified parameters."""
    print(f"🏗️  Starting BlockBot test with pattern: {args.pattern}")
    print(f"   Server: {args.server}")
    print(f"   Duration: {args.duration}s")
    print(f"   Max blocks: {args.max_blocks}")
    print(f"   Building at: ({args.x}, {args.y}, {args.z})")
    
    # Build the blockbot first
    bot_dir = Path("bot_components/texmodbot")
    build_cmd = ["cargo", "build", "--release"]
    
    print("🔨 Building blockbot...")
    result = subprocess.run(build_cmd, cwd=bot_dir, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ Failed to build blockbot:")
        print(result.stderr)
        return 1
    
    # Run the blockbot
    blockbot_bin = bot_dir / "target" / "release" / "blockbot"
    
    cmd = [
        str(blockbot_bin),
        args.server,
        "--username", args.username,
        "--password", args.password,
        "--quit-after-seconds", str(args.duration),
        "--pattern", args.pattern,
        "--speed", str(args.speed),
        "--max-blocks", str(args.max_blocks),
        "--start-x", str(args.x),
        "--start-y", str(args.y),
        "--start-z", str(args.z),
        "--auto-register",
    ]
    
    if args.destructive:
        cmd.append("--destructive")
    
    print(f"🤖 Running: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        # Run the blockbot and show output in real-time
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        return_code = process.poll()
        print("=" * 60)
        print(f"✅ BlockBot finished with return code: {return_code}")
        return return_code
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        process.terminate()
        return 130

def main():
    parser = argparse.ArgumentParser(
        description="Test the BlockBot with different building patterns",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument("server", help="Server address (e.g., 127.0.0.1:30000)")
    parser.add_argument("--username", default="testbot", help="Bot username")
    parser.add_argument("--password", default="testpass", help="Bot password")
    parser.add_argument("--pattern", default="tower", 
                       choices=["tower", "wall", "platform", "random", "spiral", "house"],
                       help="Building pattern")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--speed", type=float, default=1.0, help="Block placement speed (seconds between blocks)")
    parser.add_argument("--max-blocks", type=int, default=50, help="Maximum blocks to place")
    parser.add_argument("--x", type=float, default=0.0, help="Starting X coordinate")
    parser.add_argument("--y", type=float, default=9.0, help="Starting Y coordinate (near spawn)")
    parser.add_argument("--z", type=float, default=123.0, help="Starting Z coordinate (near spawn)")
    parser.add_argument("--destructive", action="store_true", help="Also dig blocks occasionally")
    
    args = parser.parse_args()
    
    print("🚀 BlockBot Test Script")
    print("=" * 60)
    
    return run_blockbot_test(args)

if __name__ == "__main__":
    sys.exit(main()) 