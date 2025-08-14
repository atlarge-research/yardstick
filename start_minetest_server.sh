#!/bin/bash
#SBATCH --job-name=luanti_minetest_server
#SBATCH --time=01:00:00
#SBATCH --mem=4G
#SBATCH --cpus-per-task=4
#SBATCH --output=/var/scratch/aco237/luanti_minetest_server_%j.out
#SBATCH --error=/var/scratch/aco237/luanti_minetest_server_%j.err

echo "🚀 Starting Luanti server with minetest game on DAS5"
echo "Node: $(hostname)"
echo "Date: $(date)"
echo "Job ID: $SLURM_JOB_ID"

# Set up working directory
WORK_DIR="/var/scratch/aco237/luanti_server_$(date +%s)"
echo "📁 Working directory: $WORK_DIR"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# Use Ansible to deploy the server
echo "🔧 Deploying Luanti server using Ansible..."
ansible-playbook /var/scratch/aco237/luantick/yardstick_benchmark/games/luanti/server/luanti_deploy.yml \
    -i /var/scratch/aco237/luantick/inventory.ini \
    --extra-vars "wd=$WORK_DIR" \
    --extra-vars "luanti_template=/var/scratch/aco237/luantick/yardstick_benchmark/games/luanti/server/luanti.conf.j2" \
    --extra-vars "collector_mod=/var/scratch/aco237/luantick/yardstick_benchmark/games/luanti/server/collector.lua" \
    --extra-vars "game_mode=minetest_game" \
    --verbose

if [ $? -ne 0 ]; then
    echo "❌ Deployment failed"
    exit 1
fi

echo "✅ Deployment successful"

# Fix the IPv6 issue by updating the configuration
echo "🔧 Configuring server for IPv4-only minetest game..."
cat > luanti.conf << 'EOF'
# Luanti Server Configuration for minetest game
server_name = Luanti Minetest Game Server
motd = Welcome to the Luanti server running minetest game!
max_users = 20
port = 30000

# Network settings - IPv4 only
server_address = 127.0.0.1
bind_address = 127.0.0.1
enable_ipv6 = false
ipv6_server = false

# Game settings
default_game = minetest
creative_mode = true
enable_damage = false
enable_pvp = false

# Performance settings
dedicated_server_step = 0.1
time_speed = 0
server_map_save_interval = 5.3

# World generation
mg_name = v7
mg_flags = trees, caves, dungeons, decorations
water_level = 1
static_spawnpoint = 0, 80, 0

# Logging
debug_log_level = action
logfile = logs/server.log

# Disable unnecessary features for headless
enable_client_modding = false
EOF

# Create logs directory
mkdir -p logs

# Update the world.mt file to use correct minetest game ID
if [ -f "worlds/benchmark/world.mt" ]; then
    echo "🔧 Updating world configuration..."
    cat > worlds/benchmark/world.mt << 'EOF'
enable_damage = false
creative_mode = true
gameid = minetest
world_name = benchmark
backend = sqlite3
load_mod_yardstick_collector = true
EOF
fi

echo "🎮 Starting Luanti server with minetest game..."
echo "Server details:"
echo "  Node: $(hostname)"
echo "  Port: 30000"
echo "  Game: minetest"
echo "  Working directory: $WORK_DIR"
echo "=========================="

# Start server in background and capture PID
./luantiserver \
    --world worlds/benchmark \
    --config luanti.conf \
    --port 30000 \
    --logfile logs/server.log \
    --verbose &

SERVER_PID=$!
echo $SERVER_PID > luanti.pid

echo "Server started with PID: $SERVER_PID"

# Wait for server to initialize
echo "⏳ Waiting for server to initialize..."
sleep 15

# Check if server is still running
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Server is running successfully!"
    
    # Get the node hostname for connection info
    NODE_HOST=$(hostname)
    echo ""
    echo "🌐 CONNECTION INFORMATION:"
    echo "Host: $NODE_HOST"
    echo "Port: 30000"
    echo "Game: minetest"
    echo ""
    echo "To connect from your local machine:"
    echo "  1. Set up SSH tunnel:"
    echo "     ssh -L 30000:$NODE_HOST:30000 aco237@fs0.das5.cs.vu.nl"
    echo "  2. Connect Luanti client to: localhost:30000"
    echo ""
    
    # Show initial log output
    if [ -f logs/server.log ]; then
        echo "📊 Initial server log:"
        head -20 logs/server.log
        echo "------------------------"
    fi
    
    # Monitor server for 50 minutes
    echo "📊 Monitoring server (will run for 50 minutes)..."
    
    for i in {1..50}; do
        if ps -p $SERVER_PID > /dev/null; then
            echo "[$i/50] Server running (PID: $SERVER_PID) - $(date)"
            
            # Show some log output every 10 minutes
            if [ $((i % 10)) -eq 0 ] && [ -f logs/server.log ]; then
                echo "--- Recent server activity ---"
                tail -5 logs/server.log
                echo "-----------------------------"
            fi
        else
            echo "❌ Server process died at minute $i!"
            echo "--- Final server log ---"
            tail -20 logs/server.log 2>/dev/null || echo "No log file found"
            break
        fi
        sleep 60  # Sleep for 1 minute
    done
    
    # Cleanup
    if ps -p $SERVER_PID > /dev/null; then
        echo "🛑 Stopping server gracefully..."
        kill $SERVER_PID
        sleep 5
        
        # Force kill if still running
        if ps -p $SERVER_PID > /dev/null; then
            echo "🛑 Force stopping server..."
            kill -9 $SERVER_PID
        fi
    fi
    
    echo "✅ Server stopped"
    echo "📁 Server files available at: $WORK_DIR"
    
else
    echo "❌ Server failed to start!"
    echo "--- Server log ---"
    cat logs/server.log 2>/dev/null || echo "No log file found"
    
    # Check if binary exists and is executable
    if [ -f ./luantiserver ]; then
        echo "Binary exists and permissions:"
        ls -la ./luantiserver
    else
        echo "❌ Server binary not found!"
    fi
    
    # Check if world exists
    if [ -d worlds/benchmark ]; then
        echo "World directory exists:"
        ls -la worlds/benchmark/
    else
        echo "❌ World directory not found!"
    fi
    
    exit 1
fi
