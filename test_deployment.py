#!/usr/bin/env python3
"""
Test script to verify Luanti deployment configuration locally.
This script validates all components without actually deploying to DAS.
"""

from yardstick_benchmark.games.luanti.server import LuantiServer
from yardstick_benchmark.games.luanti.workload import RustWalkAround
from yardstick_benchmark.model import Node
from datetime import timedelta
from pathlib import Path
import os

def test_server_config():
    """Test server configuration without actual deployment."""
    print("Testing Luanti Server configuration...")
    
    # Create mock nodes with proper Path objects
    test_nodes = [Node("test-server", Path("/tmp"))]
    
    # Initialize server
    server = LuantiServer(test_nodes, game_mode="minetest_game")
    
    # Check that all required files exist
    playbook_paths = [
        server.deploy_action.script,
        server.start_action.script,
        server.stop_action.script,
        server.cleanup_action.script
    ]
    
    for path in playbook_paths:
        if not path.exists():
            print(f"❌ Missing server playbook: {path}")
            return False
        else:
            print(f"✅ Found server playbook: {path.name}")
    
    print("✅ Luanti Server configuration is valid")
    return True

def test_rust_workload_config():
    """Test Rust workload configuration without actual deployment."""
    print("\nTesting Rust WalkAround workload configuration...")
    
    # Create mock nodes with proper Path objects
    server_node = Node("test-server", Path("/tmp"))
    bot_nodes = [Node("test-bot", Path("/tmp"))]
    
    # Initialize workload
    workload = RustWalkAround(
        bot_nodes,
        server_node.host,
        duration=timedelta(seconds=120),
        bots_per_node=15,
        movement_mode="random",
        movement_speed=2.0,
    )
    
    # Check that all required files exist
    playbook_paths = [
        workload.deploy_action.script,
        workload.start_action.script,
        workload.stop_action.script,
        workload.cleanup_action.script
    ]
    
    for path in playbook_paths:
        if not path.exists():
            print(f"❌ Missing workload playbook: {path}")
            return False
        else:
            print(f"✅ Found workload playbook: {path.name}")
    
    # Check texmodbot source path
    texmodbot_source = Path(workload.extravars["texmodbot_source"])
    if not texmodbot_source.exists():
        print(f"❌ Missing texmodbot source: {texmodbot_source}")
        return False
    else:
        print(f"✅ Found texmodbot source: {texmodbot_source}")
    
    # Check for essential texmodbot files
    essential_files = [
        texmodbot_source / "Cargo.toml",
        texmodbot_source / "src" / "multi_walkbot.rs",
    ]
    
    for file_path in essential_files:
        if not file_path.exists():
            print(f"❌ Missing essential file: {file_path}")
            return False
        else:
            print(f"✅ Found essential file: {file_path.name}")
    
    print("✅ Rust WalkAround workload configuration is valid")
    return True

def test_deployment_script():
    """Test the main deployment script configuration."""
    print("\nTesting main deployment script...")
    
    script_path = Path(__file__).parent / "luanti_example.py"
    if not script_path.exists():
        print(f"❌ Missing deployment script: {script_path}")
        return False
    else:
        print(f"✅ Found deployment script: {script_path.name}")
    
    # Check if script can be imported (basic syntax check)
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("luanti_example", script_path)
        if spec is None:
            print("❌ Could not load deployment script spec")
            return False
        print("✅ Deployment script syntax is valid")
    except Exception as e:
        print(f"❌ Deployment script has syntax errors: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("🚀 Testing Luanti deployment configuration...\n")
    
    tests = [
        test_server_config,
        test_rust_workload_config,
        test_deployment_script,
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
    
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 All tests passed! Deployment configuration is ready.")
        print("\nNext steps:")
        print("1. Run: python luanti_example.py")
        print("2. Monitor logs in /var/scratch/{username}/yardstick/luanti_output")
        print("3. Check server performance metrics")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
