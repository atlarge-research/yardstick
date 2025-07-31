#!/usr/bin/env python3
"""
Live Deployment Monitor

This script helps monitor a running Luanti deployment by checking
logs, system status, and providing real-time feedback.
"""

import os
import time
import subprocess
from pathlib import Path
from datetime import datetime

class DeploymentMonitor:
    def __init__(self):
        self.start_time = datetime.now()
        self.user = os.getlogin()
        self.results_base = Path(f"/var/scratch/{self.user}/yardstick")
        
    def print_header(self):
        print("🔍 LUANTI DEPLOYMENT MONITOR")
        print("=" * 40)
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"User: {self.user}")
        print(f"Results Path: {self.results_base}")
        print("=" * 40)
        
    def check_results_directory(self):
        """Check for active result directories."""
        if not self.results_base.exists():
            print("⚠️  No results directory found - deployment may not be running")
            return []
            
        # Look for recent directories
        recent_dirs = []
        for item in self.results_base.iterdir():
            if item.is_dir():
                # Check if created recently (within last hour)
                stat = item.stat()
                age_minutes = (time.time() - stat.st_mtime) / 60
                if age_minutes < 60:
                    recent_dirs.append((item, age_minutes))
                    
        if recent_dirs:
            print(f"✅ Found {len(recent_dirs)} recent result directories:")
            for dir_path, age in sorted(recent_dirs, key=lambda x: x[1]):
                print(f"   📁 {dir_path.name} (created {age:.1f} minutes ago)")
        else:
            print("⚠️  No recent result directories found")
            
        return recent_dirs
        
    def check_running_processes(self):
        """Check for running Luanti and bot processes."""
        print("\n🔍 Checking for running processes...")
        
        # Check for Luanti server
        try:
            luanti_result = subprocess.run(
                ["pgrep", "-f", "luanti"],
                capture_output=True, text=True
            )
            if luanti_result.returncode == 0:
                pids = luanti_result.stdout.strip().split('\n')
                print(f"✅ Found {len(pids)} Luanti server process(es)")
                for pid in pids:
                    if pid:
                        print(f"   🎮 PID: {pid}")
            else:
                print("⚠️  No Luanti server processes found")
        except Exception as e:
            print(f"❌ Error checking Luanti processes: {e}")
            
        # Check for bot processes
        try:
            bot_result = subprocess.run(
                ["pgrep", "-f", "multi_walkbot"],
                capture_output=True, text=True
            )
            if bot_result.returncode == 0:
                pids = bot_result.stdout.strip().split('\n')
                print(f"✅ Found {len(pids)} bot process(es)")
                for pid in pids:
                    if pid:
                        print(f"   🤖 PID: {pid}")
            else:
                print("⚠️  No bot processes found")
        except Exception as e:
            print(f"❌ Error checking bot processes: {e}")
            
    def check_network_connections(self):
        """Check for active network connections on Luanti port."""
        print("\n🌐 Checking network connections...")
        
        try:
            # Check if port 30000 is listening
            netstat_result = subprocess.run(
                ["netstat", "-ln"], 
                capture_output=True, text=True
            )
            if ":30000" in netstat_result.stdout:
                print("✅ Luanti server port (30000) is active")
            else:
                print("⚠️  Luanti server port (30000) not found")
                
            # Check for established connections
            established_result = subprocess.run(
                ["netstat", "-n", "|", "grep", ":30000.*ESTABLISHED"],
                shell=True, capture_output=True, text=True
            )
            if established_result.stdout.strip():
                connections = established_result.stdout.strip().split('\n')
                print(f"✅ Found {len(connections)} active connections to server")
            else:
                print("⚠️  No active connections to Luanti server")
                
        except Exception as e:
            print(f"❌ Error checking network connections: {e}")
            
    def show_recent_logs(self, results_dirs):
        """Show recent log entries if available."""
        print("\n📝 Recent log activity...")
        
        if not results_dirs:
            print("⚠️  No recent results directories to check for logs")
            return
            
        # Look for log files in the most recent directory
        most_recent = sorted(results_dirs, key=lambda x: x[1])[0][0]
        log_files = list(most_recent.glob("**/*.log"))
        
        if log_files:
            print(f"📄 Found {len(log_files)} log files in {most_recent.name}")
            for log_file in log_files[:3]:  # Show first 3 log files
                try:
                    # Show last 5 lines of each log
                    tail_result = subprocess.run(
                        ["tail", "-n", "5", str(log_file)],
                        capture_output=True, text=True
                    )
                    if tail_result.returncode == 0 and tail_result.stdout.strip():
                        print(f"\n📄 {log_file.name} (last 5 lines):")
                        for line in tail_result.stdout.strip().split('\n'):
                            print(f"   {line}")
                except Exception as e:
                    print(f"❌ Error reading {log_file.name}: {e}")
        else:
            print("⚠️  No log files found in results directory")
            
    def show_system_resources(self):
        """Show basic system resource usage."""
        print("\n💻 System resources...")
        
        try:
            # CPU usage
            cpu_result = subprocess.run(
                ["top", "-bn1", "|", "grep", "Cpu", "|", "head", "-1"],
                shell=True, capture_output=True, text=True
            )
            if cpu_result.stdout:
                print(f"🔥 {cpu_result.stdout.strip()}")
                
            # Memory usage
            mem_result = subprocess.run(
                ["free", "-h"], capture_output=True, text=True
            )
            if mem_result.returncode == 0:
                lines = mem_result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    print(f"💾 {lines[1]}")  # Memory line
                    
        except Exception as e:
            print(f"❌ Error checking system resources: {e}")
            
    def run_continuous_monitor(self, interval=30):
        """Run continuous monitoring with updates."""
        self.print_header()
        
        try:
            while True:
                print(f"\n🕐 Update at {datetime.now().strftime('%H:%M:%S')}")
                print("-" * 40)
                
                results_dirs = self.check_results_directory()
                self.check_running_processes()
                self.check_network_connections()
                self.show_system_resources()
                
                if results_dirs:
                    self.show_recent_logs(results_dirs)
                
                print(f"\n⏱️  Next update in {interval} seconds (Ctrl+C to stop)")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped by user")
            
    def run_single_check(self):
        """Run a single monitoring check."""
        self.print_header()
        
        results_dirs = self.check_results_directory()
        self.check_running_processes()
        self.check_network_connections()
        self.show_system_resources()
        
        if results_dirs:
            self.show_recent_logs(results_dirs)
            
        print(f"\n📊 Monitoring complete at {datetime.now().strftime('%H:%M:%S')}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor Luanti deployment")
    parser.add_argument(
        "--continuous", "-c", 
        action="store_true",
        help="Run continuous monitoring (default: single check)"
    )
    parser.add_argument(
        "--interval", "-i",
        type=int, default=30,
        help="Update interval in seconds for continuous mode (default: 30)"
    )
    
    args = parser.parse_args()
    
    monitor = DeploymentMonitor()
    
    if args.continuous:
        monitor.run_continuous_monitor(args.interval)
    else:
        monitor.run_single_check()

if __name__ == "__main__":
    main()
