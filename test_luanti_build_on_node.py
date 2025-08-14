#!/usr/bin/env python3
"""
Quick test deployment using the build_luanti_headless.py script on a compute node.
This is a simpler alternative that uses your existing build script.
"""

import subprocess
import sys
import tempfile
import time
import os

def create_simple_slurm_script():
    """Create a SLURM script that uses the build_luanti_headless.py script."""
    script_content = f"""#!/bin/bash
#SBATCH --job-name=luanti-build-test
#SBATCH --output=/var/scratch/aco237/luanti_build_test_%j.out
#SBATCH --error=/var/scratch/aco237/luanti_build_test_%j.out
#SBATCH --time=00:30:00
#SBATCH --partition=defq
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=4G

echo "=== SLURM Job Information ==="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "=========================="

# Change to a temporary directory
cd /tmp

# Run the build script
echo "🏗️ Building Luanti headless server..."
python3 /var/scratch/aco237/luantick/build_luanti_headless.py

# If build was successful, try to run a quick test
if [ -d "/tmp/luanti_build/test_server" ]; then
    echo "✅ Build successful! Testing server startup..."
    cd /tmp/luanti_build/test_server
    
    # Modify the config to disable IPv6
    cat > minetest.conf << 'EOF'
# Minimal server configuration for testing
server_name = Test Luanti Server
motd = Welcome to the test server!
max_users = 10
port = 30000
default_game = minetest_game
creative_mode = true
enable_damage = false

# Network settings - IPv4 only
bind_address = 0.0.0.0
enable_ipv6 = false
ipv6_server = false
EOF
    
    echo "🎮 Starting server test (will run for 2 minutes)..."
    echo "Node: $SLURM_NODELIST"
    echo "Port: 30000"
    
    # Start server in background
    timeout 120 ./luantiserver --world "testworld" --config "minetest.conf" --logfile "server.log" &
    SERVER_PID=$!
    
    # Wait a bit for startup
    sleep 5
    
    if ps -p $SERVER_PID > /dev/null; then
        echo "✅ Server started successfully!"
        echo "🌐 Connection Info:"
        echo "  Host: $SLURM_NODELIST"
        echo "  Port: 30000"
        echo "  SSH tunnel: ssh -L 30000:$SLURM_NODELIST:30000 aco237@fs0.das5.cs.vu.nl"
        
        # Let it run for a bit
        echo "⏳ Letting server run for 2 minutes..."
        wait $SERVER_PID
        
        echo "📊 Server log:"
        cat server.log || echo "No log file found"
    else
        echo "❌ Server failed to start"
        echo "📊 Server log:"
        cat server.log || echo "No log file found"
    fi
else
    echo "❌ Build failed - no test server directory found"
fi

echo "🏁 Test completed"
"""
    return script_content

def submit_simple_test():
    """Submit a simple test job."""
    print("🧪 Quick Luanti Build & Test on DAS5")
    print("=" * 40)
    
    # Create script
    script_content = create_simple_slurm_script()
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.slurm', delete=False) as f:
        f.write(script_content)
        script_path = f.name
    
    try:
        # Submit job
        result = subprocess.run(
            f"sbatch {script_path}", 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # Extract job ID
        job_output = result.stdout.strip()
        job_id = job_output.split()[-1] if "Submitted batch job" in job_output else "unknown"
        output_file = f"/var/scratch/aco237/luanti_build_test_{job_id}.out"
        
        print(f"✅ Test job submitted!")
        print(f"Job ID: {job_id}")
        print(f"Output: {output_file}")
        
        print(f"\\n📊 Monitor with:")
        print(f"  squeue -j {job_id}")
        print(f"  tail -f {output_file}")
        
        # Quick status check
        time.sleep(1)
        subprocess.run(f"squeue -j {job_id}", shell=True)
        
        return job_id, output_file
        
    finally:
        os.unlink(script_path)

if __name__ == "__main__":
    try:
        job_id, output_file = submit_simple_test()
        
        print(f"\\n⏳ Job will build and test Luanti on a compute node.")
        print(f"   This takes about 10-15 minutes for the build.")
        
        response = input("\\nMonitor output? (Y/n): ").lower()
        if response != 'n':
            print(f"\\nMonitoring {output_file} (Ctrl+C to stop monitoring)...")
            try:
                subprocess.run(f"tail -f {output_file}", shell=True)
            except KeyboardInterrupt:
                print("\\nStopped monitoring. Job continues running.")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)
