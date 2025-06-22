#!/usr/bin/env python3
"""
Simple script to download and setup Extra Ordinance mod for Luanti benchmarking
"""

import subprocess
import sys
from pathlib import Path
import shutil

def setup_extra_ordinance_mod():
    """Download and setup Extra Ordinance mod using git clone method"""
    
    print("🚀 Setting up Extra Ordinance mod for Luanti benchmarking...")
    
    # Check if git is available
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
        print("✓ Git is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Git is not available. Please install git first.")
        print("   macOS: brew install git")
        print("   Or download from: https://git-scm.com/")
        return False
    
    # Create mods directory in our benchmark setup
    benchmark_mods_dir = Path("./luanti_server/mods")
    benchmark_mods_dir.mkdir(parents=True, exist_ok=True)
    
    extra_ordinance_dir = benchmark_mods_dir / "extra_ordinance"
    
    # Remove existing directory if it exists
    if extra_ordinance_dir.exists():
        print(f"🔄 Removing existing Extra Ordinance mod at {extra_ordinance_dir}")
        shutil.rmtree(extra_ordinance_dir)
    
    # Clone the mod from ContentDB source
    print("📥 Downloading Extra Ordinance mod...")
    try:
        subprocess.run([
            'git', 'clone', 
            'https://codeberg.org/Sumianvoice/extra_ordinance.git',
            str(extra_ordinance_dir)
        ], check=True)
        print(f"✅ Extra Ordinance mod downloaded to {extra_ordinance_dir}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to download mod: {e}")
        return False
    
    # Check if mod files exist
    if (extra_ordinance_dir / "init.lua").exists():
        print("✓ Mod files verified")
    else:
        print("⚠️ Warning: init.lua not found in mod directory")
    
    print("\n🎯 Extra Ordinance mod is ready!")
    print(f"   Installed at: {extra_ordinance_dir}")
    print("\nNow you can run benchmarks with:")
    print("   python3 local_luanti_benchmark.py --mod-config extra_ordinance --duration 180 --bots 20")
    
    return True

if __name__ == "__main__":
    success = setup_extra_ordinance_mod()
    if not success:
        sys.exit(1) 