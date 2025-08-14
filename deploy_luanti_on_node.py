#!/usr/bin/env python3
"""
Deploy and run Luanti headless server on a DAS5 compute node.
This script:
1. Reserves a compute node using SLURM
2. Deploys the headless server with IPv4-only configuration
3. Starts the server and provides connection information
"""

import subprocess
import sys
import os
import time
import json
import tempfile
from pathlib import Path

def run_command(cmd, description, cwd=None, check=True):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=check, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        if result.stdout.strip():
            print(f"✅ {description} completed")
            return result
        else:
            print(f"✅ {description} completed (no output)")
            return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Command: {cmd}")
        print(f"Error: {e.stderr}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if check:
            sys.exit(1)
        return None

def check_slurm_available():
    """Check if SLURM is available."""
    result = subprocess.run("which srun", shell=True, capture_output=True)
    return result.returncode == 0

def get_available_nodes():
    """Get list of available compute nodes."""
    try:
        result = subprocess.run(
            "sinfo -h -t idle -o '%n'", 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=True
        )
        nodes = [node.strip() for node in result.stdout.strip().split('\n') if node.strip()]
        return nodes
    except:
        return []

def create_slurm_script(job_name, working_dir, output_file):
    """Create a SLURM batch script for running the server."""
    script_content = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --output={output_file}
#SBATCH --error={output_file}
#SBATCH --time=01:00:00
#SBATCH --partition=defq
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=4G

echo "=== SLURM Job Information ==="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Working directory: {working_dir}"
echo "=========================="

# Change to working directory
cd {working_dir}

# Deploy the server using Ansible (non-interactive)
echo "🚀 Deploying Luanti headless server..."
ansible-playbook /var/scratch/aco237/luantick/yardstick_benchmark/games/luanti/server/luanti_deploy.yml \\
    -i /var/scratch/aco237/luantick/inventory.ini \\
    --extra-vars "wd={working_dir}" \\
    --extra-vars "luanti_template=/var/scratch/aco237/luantick/yardstick_benchmark/games/luanti/server/luanti.conf.j2" \\
    --extra-vars "collector_mod=/var/scratch/aco237/luantick/yardstick_benchmark/games/luanti/server/collector.lua" \\
    --extra-vars "game_mode=minetest_game" \\
    --verbose

if [ $? -ne 0 ]; then
    echo "❌ Deployment failed"
    exit 1
fi

echo "✅ Deployment successful"

# Update the Luanti configuration to disable IPv6 and set IPv4-only
echo "🔧 Configuring server for IPv4-only..."
cat > luanti.conf << 'EOF'
# Luanti Server Configuration (IPv4-only)
server_name = Luanti Headless Test Server
motd = Welcome to the Luanti headless server!
max_users = 20
port = 30000

# Network settings - IPv4 only
bind_address = 0.0.0.0
ipv6_server = false
enable_ipv6 = false

# Game settings
default_game = minetest_game
creative_mode = true
enable_damage = false
enable_pvp = false

# Performance settings
dedicated_server_step = 0.1
time_speed = 0
server_map_save_interval = 5.3

# Logging
debug_log_level = action
logfile = logs/server.log

# Disable unnecessary features for headless
enable_client_modding = false
EOF

# Create logs directory
mkdir -p logs

# Start the server
echo "🎮 Starting Luanti headless server..."
echo "Server node: $SLURM_NODELIST"
echo "Server port: 30000"
echo "=========================="

# Start server in background and capture PID
./luantiserver \\
    --world worlds/benchmark \\
    --config luanti.conf \\
    --port 30000 \\
    --logfile logs/server.log \\
    --verbose &

SERVER_PID=$!
echo $SERVER_PID > luanti.pid

echo "Server started with PID: $SERVER_PID"
echo "Server node: $SLURM_NODELIST"

# Wait for server to initialize
echo "⏳ Waiting for server to initialize..."
sleep 10

# Check if server is still running
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Server is running successfully!"
    
    # Get the node hostname for connection info
    NODE_HOST=$SLURM_NODELIST
    echo ""
    echo "🌐 CONNECTION INFORMATION:"
    echo "Host: $NODE_HOST"
    echo "Port: 30000"
    echo "Game: minetest_game"
    echo ""
    echo "To connect from your local machine:"
    echo "  ssh -L 30000:$NODE_HOST:30000 aco237@fs0.das5.cs.vu.nl"
    echo "  Then connect to localhost:30000 in Luanti client"
    echo ""
    
    # Monitor server for a while
    echo "📊 Monitoring server (will run for 50 minutes)..."
    
    # Keep the job alive and monitor
    for i in {{1..50}}; do
        if ps -p $SERVER_PID > /dev/null; then
            echo "[$i/50] Server running (PID: $SERVER_PID)"
            
            # Show some log output every 10 minutes
            if [ $((i % 10)) -eq 0 ] && [ -f logs/server.log ]; then
                echo "--- Recent server log ---"
                tail -5 logs/server.log
                echo "------------------------"
            fi
        else
            echo "❌ Server process died!"
            break
        fi
        sleep 60  # Sleep for 1 minute
    done
    
    # Cleanup
    if ps -p $SERVER_PID > /dev/null; then
        echo "🛑 Stopping server..."
        kill $SERVER_PID
        sleep 5
        
        # Force kill if still running
        if ps -p $SERVER_PID > /dev/null; then
            kill -9 $SERVER_PID
        fi
    fi
    
    echo "✅ Server stopped"
    
else
    echo "❌ Server failed to start!"
    echo "--- Server log ---"
    cat logs/server.log 2>/dev/null || echo "No log file found"
    exit 1
fi
"""
    return script_content

def submit_server_job():
    """Submit the server job to SLURM."""
    print("🚀 Deploying Luanti headless server on DAS5 compute node")
    print("=" * 60)
    
    # Check if SLURM is available
    if not check_slurm_available():
        print("❌ SLURM not available. This script requires a SLURM-enabled system.")
        sys.exit(1)
    
    # Check available nodes
    available_nodes = get_available_nodes()
    if not available_nodes:
        print("⚠️  No idle nodes available. Job will be queued.")
    else:
        print(f"✅ {len(available_nodes)} idle nodes available: {', '.join(available_nodes[:5])}{'...' if len(available_nodes) > 5 else ''}")
    
    # Set up working directory
    timestamp = int(time.time())
    job_name = f"luanti-server-{timestamp}"
    working_dir = f"/var/scratch/aco237/luanti_headless_{timestamp}"
    output_file = f"/var/scratch/aco237/luanti_server_{timestamp}.out"
    
    print(f"📁 Working directory: {working_dir}")
    print(f"📝 Output file: {output_file}")
    
    # Create SLURM script
    script_content = create_slurm_script(job_name, working_dir, output_file)
    
    # Write script to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.slurm', delete=False) as f:
        f.write(script_content)
        script_path = f.name
    
    try:
        # Submit job
        print(f"📋 Submitting SLURM job: {job_name}")
        result = run_command(f"sbatch {script_path}", "Submitting SLURM job")
        
        # Extract job ID
        job_output = result.stdout.strip()
        job_id = job_output.split()[-1] if "Submitted batch job" in job_output else "unknown"
        
        print(f"✅ Job submitted successfully!")
        print(f"Job ID: {job_id}")
        print(f"Working directory: {working_dir}")
        print(f"Output file: {output_file}")
        
        print(f"\\n📊 Monitor your job with:")
        print(f"  squeue -j {job_id}")
        print(f"  tail -f {output_file}")
        
        print(f"\\n🔍 Check job status:")
        time.sleep(2)
        run_command(f"squeue -j {job_id}", "Checking job status", check=False)
        
        print(f"\\n⏳ Your server will start automatically once a compute node is allocated.")
        print(f"   The job will run for up to 1 hour.")
        print(f"   Connection information will be shown in: {output_file}")
        
        return job_id, output_file
        
    finally:
        # Clean up script file
        os.unlink(script_path)

def monitor_job_output(output_file, timeout=300):
    """Monitor job output file for connection information."""
    print(f"\\n👀 Monitoring job output for connection info...")
    print(f"Output file: {output_file}")
    
    start_time = time.time()
    connection_info_found = False
    
    while time.time() - start_time < timeout:
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r') as f:
                    content = f.read()
                    
                if "CONNECTION INFORMATION:" in content:
                    # Extract and display connection info
                    lines = content.split('\\n')
                    in_connection_section = False
                    
                    print("\\n" + "=" * 50)
                    print("🌐 SERVER CONNECTION INFORMATION")
                    print("=" * 50)
                    
                    for line in lines:
                        if "CONNECTION INFORMATION:" in line:
                            in_connection_section = True
                            continue
                        elif in_connection_section and line.strip():
                            if line.startswith("To connect") or line.startswith("  ssh") or line.startswith("  Then"):
                                print(line)
                            elif "Host:" in line or "Port:" in line or "Game:" in line:
                                print(line)
                            elif not line.startswith(" ") and line.strip():
                                break  # End of connection section
                    
                    connection_info_found = True
                    break
                    
                elif "❌" in content and ("failed" in content.lower() or "error" in content.lower()):
                    print("\\n❌ Job appears to have failed. Check the output file:")
                    print(f"  cat {output_file}")
                    break
                    
            except Exception as e:
                pass  # File might be being written to
        
        time.sleep(5)
    
    if not connection_info_found:
        print(f"\\n⏳ Job still initializing. Monitor manually:")
        print(f"  tail -f {output_file}")

def main():
    """Main function."""
    print("Luanti Headless Server Deployment (DAS5)")
    print("=" * 50)
    
    # Submit the job
    try:
        job_id, output_file = submit_server_job()
        
        # Ask if user wants to monitor
        print(f"\\n🤔 Would you like to monitor the job output for connection info?")
        response = input("Monitor job output? (Y/n): ").lower()
        
        if response != 'n':
            monitor_job_output(output_file)
        
        print(f"\\n📋 Job management commands:")
        print(f"  Monitor: tail -f {output_file}")
        print(f"  Cancel:  scancel {job_id}")
        print(f"  Status:  squeue -j {job_id}")
        
    except KeyboardInterrupt:
        print("\\n⚠️  Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\\n❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
