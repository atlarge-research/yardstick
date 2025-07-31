#!/usr/bin/env python3
"""
Script to run all Luanti benchmark experiments
"""

import argparse
import subprocess
import os
import time
from pathlib import Path

# Experiment configurations
EXPERIMENTS = [
    "player_scalability",
    "mod_impact",
    "network_resilience",
    "player_behavior",
    "environment_modification"
]

def run_experiment(experiment_name, args):
    """Run a specific experiment with the given arguments"""
    print(f"\n{'='*80}")
    print(f"Running experiment: {experiment_name}")
    print(f"{'='*80}\n")
    
    # Load the experiment configuration
    config_file = Path("experiments") / f"{experiment_name}.yml"
    if not config_file.exists():
        print(f"Error: Experiment configuration {config_file} not found!")
        return False
    
    # Build the command
    cmd = [
        "python", "luanti_example.py",
        "--experiment", str(config_file),
        "--nodes", str(args.nodes),
        "--duration", str(args.duration)
    ]
    
    # Run the experiment
    try:
        subprocess.run(cmd, check=True)
        print(f"\nExperiment {experiment_name} completed successfully.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError running experiment {experiment_name}: {e}\n")
        return False

def main():
    """Run all experiments or a specific one"""
    parser = argparse.ArgumentParser(description="Run Luanti benchmark experiments")
    parser.add_argument("--experiment", choices=EXPERIMENTS,
                       help="Run a specific experiment (default: run all)")
    parser.add_argument("--nodes", type=int, default=5,
                       help="Number of DAS nodes to provision (default: 5)")
    parser.add_argument("--duration", type=int, default=300,
                       help="Duration of each experiment in seconds (default: 300)")
    
    args = parser.parse_args()
    
    # Create results directory
    results_dir = Path("results") / f"run_{int(time.time())}"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Run experiments
    if args.experiment:
        # Run a specific experiment
        success = run_experiment(args.experiment, args)
    else:
        # Run all experiments
        results = {}
        for exp in EXPERIMENTS:
            success = run_experiment(exp, args)
            results[exp] = "Success" if success else "Failed"
        
        # Print summary
        print("\n\nExperiment Run Summary:")
        print("-----------------------")
        for exp, status in results.items():
            print(f"{exp}: {status}")
    
    print(f"\nAll experiment results saved to {results_dir}")

if __name__ == "__main__":
    main() 