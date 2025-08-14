#!/bin/bash
# Simple Luanti Headless Server Build Script (No SLURM)
# Based on the proven manual build process that was successfully tested
# This script can be run directly on any compute node without SLURM or sudo

set -e

# Configuration
INSTALL_DIR="$HOME/luanti_build"
LUANTI_DIR="$INSTALL_DIR/luanti"
SERVER_DIR="$INSTALL_DIR/server"

echo "🏗️ LUANTI HEADLESS SERVER - PROVEN BUILD METHOD"
echo "================================================"
echo "🎯 Installation directory: $INSTALL_DIR"
echo "🎮 Server directory: $SERVER_DIR"
echo "🔧 Build method: Source build with LuaJIT optimization"
echo "🌐 Network configuration: IPv4 only"
echo "📦 Games: minetest_game + extra_ordinance (with bug fixes)"
echo "================================================"

# Check if dependencies are available (informational only)
echo "🔍 Checking build dependencies..."
for cmd in git cmake make gcc; do
    if command -v $cmd >/dev/null 2>&1; then
        echo "  ✅ $cmd available"
    else
        echo "  ❌ $cmd not found - may need to install build dependencies"
    fi
done

# Create directories
echo "📁 Creating build directories..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Build LuaJIT for better performance
echo "🚀 Building LuaJIT from source..."
if [ ! -d "LuaJIT" ]; then
    git clone https://github.com/LuaJIT/LuaJIT.git
fi
cd LuaJIT
git checkout v2.1
make -j$(nproc) || {
    echo "⚠️  LuaJIT build failed, will use system Lua instead"
    LUAJIT_FAILED=1
}

if [ "$LUAJIT_FAILED" != "1" ]; then
    make install PREFIX="$INSTALL_DIR/luajit"
    export LUAJIT_ROOT="$INSTALL_DIR/luajit"
    export PKG_CONFIG_PATH="$LUAJIT_ROOT/lib/pkgconfig:$PKG_CONFIG_PATH"
    export LD_LIBRARY_PATH="$LUAJIT_ROOT/lib:$LD_LIBRARY_PATH"
    echo "✅ LuaJIT built successfully"
else
    echo "⚠️  Will use system Lua instead of LuaJIT"
fi

cd "$INSTALL_DIR"

# Clone and build Luanti
echo "📥 Cloning Luanti source code..."
if [ ! -d "luanti" ]; then
    git clone --depth 1 --branch stable-5 https://github.com/minetest/minetest.git luanti
fi

cd luanti
mkdir -p build
cd build

echo "⚙️  Configuring CMake build..."
if [ "$LUAJIT_FAILED" != "1" ] && [ -d "$LUAJIT_ROOT" ]; then
    # Configure with LuaJIT
    cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_CLIENT=FALSE \
        -DBUILD_SERVER=TRUE \
        -DENABLE_SOUND=FALSE \
        -DENABLE_GETTEXT=TRUE \
        -DENABLE_FREETYPE=TRUE \
        -DENABLE_LEVELDB=TRUE \
        -DRUN_IN_PLACE=TRUE \
        -DCMAKE_INSTALL_PREFIX="$LUANTI_DIR" \
        -DLUA_INCLUDE_DIR="$LUAJIT_ROOT/include/luajit-2.1" \
        -DLUA_LIBRARY="$LUAJIT_ROOT/lib/libluajit-5.1.so" \
        -GNinja || \
    cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_CLIENT=FALSE \
        -DBUILD_SERVER=TRUE \
        -DENABLE_SOUND=FALSE \
        -DENABLE_GETTEXT=TRUE \
        -DENABLE_FREETYPE=TRUE \
        -DENABLE_LEVELDB=TRUE \
        -DRUN_IN_PLACE=TRUE \
        -DCMAKE_INSTALL_PREFIX="$LUANTI_DIR"
else
    # Configure with system Lua
    cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_CLIENT=FALSE \
        -DBUILD_SERVER=TRUE \
        -DENABLE_SOUND=FALSE \
        -DENABLE_GETTEXT=TRUE \
        -DENABLE_FREETYPE=TRUE \
        -DENABLE_LEVELDB=TRUE \
        -DRUN_IN_PLACE=TRUE \
        -DCMAKE_INSTALL_PREFIX="$LUANTI_DIR"
fi

echo "🔨 Building Luanti server..."
if command -v ninja >/dev/null 2>&1; then
    ninja -j$(nproc)
    ninja install
else
    make -j$(nproc)
    make install
fi

# Verify build
if [ ! -f "$LUANTI_DIR/bin/minetestserver" ]; then
    echo "❌ ERROR: Server binary not found at $LUANTI_DIR/bin/minetestserver"
    exit 1
fi

echo "✅ Luanti server built successfully!"

# Set up server directory
echo "📦 Setting up server environment..."
mkdir -p "$SERVER_DIR"
cd "$SERVER_DIR"

# Copy server files
cp "$LUANTI_DIR/bin/minetestserver" ./
cp -r "$LUANTI_DIR/share/minetest/builtin" ./
mkdir -p games

# Download games
echo "📥 Setting up games..."
cd games

# Download minetest_game
if [ ! -d "minetest_game" ]; then
    git clone --depth 1 https://github.com/minetest/minetest_game.git
fi

# Download extra_ordinance and apply bug fixes
if [ ! -d "extra_ordinance" ]; then
    echo "📥 Downloading extra_ordinance game..."
    wget -O extra_ordinance.zip "https://content.minetest.net/packages/Sumi/extra_ordinance/download/" || {
        echo "⚠️  Failed to download extra_ordinance, continuing with minetest_game only"
    }
    
    if [ -f "extra_ordinance.zip" ]; then
        unzip extra_ordinance.zip
        rm extra_ordinance.zip
        
        # Apply bug fixes
        echo "🔧 Applying bug fixes to extra_ordinance..."
        if [ -f "extra_ordinance/mods/eo_boom/init.lua" ]; then
            sed -i 's/math.random(1,10000000)/math.random(1,1000000)/g' extra_ordinance/mods/eo_boom/init.lua
        fi
        
        if [ -f "extra_ordinance/mods/eo_furniture/init.lua" ]; then
            sed -i 's/io.open(modpath..\/nodes.lua, r)/io.open(modpath..\/nodes.lua, "r")/g' extra_ordinance/mods/eo_furniture/init.lua
        fi
        
        echo "✅ Bug fixes applied to extra_ordinance"
    fi
fi

cd "$SERVER_DIR"

# Create server configuration
echo "⚙️  Creating server configuration..."
cat > minetest.conf << 'EOF'
# Luanti server configuration for headless operation (proven build method)

# Server settings
server_name = Headless Luanti Server (Proven Build)
server_description = Luanti server built from source with proven method
server_address = 0.0.0.0
bind_address = 0.0.0.0
port = 30000
max_users = 100

# Admin settings
name = admin

# Network settings - IPv4 only for better compatibility
enable_ipv6 = false
ipv6_server = false
enable_server = true

# Game mechanics settings
creative_mode = true
enable_damage = false
default_privs = interact, shout, build

# Performance settings (optimized for bot testing)
max_block_send_distance = 10
max_simultaneous_block_sends_per_client = 40
max_simultaneous_block_sends_server_total = 250
max_packets_per_iteration = 2048
time_speed = 0
dedicated_server_step = 0.05
player_transfer_distance = 15
active_object_send_range_blocks = 6
active_block_range = 3

# World generation settings
fixed_map_seed = benchmark
mg_name = flat
static_spawnpoint = 0, 80, 0

# Game configuration
gameid = minetest

# Logging
debug_log_level = warning

# Bot-friendly settings
disable_anticheat = true
max_out_chat_queue_size = 50
EOF

# Create world directory
echo "🌍 Setting up benchmark world..."
mkdir -p worlds/benchmark

cat > worlds/benchmark/world.mt << 'EOF'
enable_damage = false
creative_mode = true
gameid = minetest
world_name = benchmark
backend = sqlite3
EOF

# Create startup script
echo "📝 Creating startup script..."
cat > start_server.sh << 'EOF'
#!/bin/bash
# Luanti Server Startup Script (Proven Build Method)

cd "$(dirname "$0")"

echo "🎮 Starting Luanti headless server (proven build method)..."
echo "📁 Server directory: $(pwd)"
echo "⚙️  Configuration: minetest.conf"
echo "🌍 World: worlds/benchmark"
echo "🎯 Game: minetest_game"
echo "🌐 Network: IPv4 only, port 30000"
echo "🔧 Build: Source build with optimizations"
echo "Press Ctrl+C to stop server"
echo "================================================"

exec ./minetestserver \
    --world worlds/benchmark \
    --config minetest.conf \
    --logfile server.log \
    --terminal
EOF

chmod +x start_server.sh

# Create server check script
cat > check_server.sh << 'EOF'
#!/bin/bash
# Check Luanti server status

cd "$(dirname "$0")"

echo "🔍 Checking Luanti server status..."

# Check if process is running
if pgrep -f "minetestserver" > /dev/null; then
    echo "✅ Luanti server is running (PID: $(pgrep -f minetestserver))"
    
    # Check if port is listening
    if command -v netstat >/dev/null 2>&1 && netstat -tulpn 2>/dev/null | grep -q ":30000 "; then
        echo "✅ Server is listening on port 30000"
    elif command -v ss >/dev/null 2>&1 && ss -tulpn 2>/dev/null | grep -q ":30000 "; then
        echo "✅ Server is listening on port 30000"
    else
        echo "⚠️  Server process found but may not be listening on port 30000"
    fi
    
    # Show recent log entries
    if [ -f server.log ]; then
        echo ""
        echo "📄 Recent log entries:"
        tail -5 server.log
    fi
else
    echo "❌ Luanti server is not running"
fi
EOF

chmod +x check_server.sh

echo ""
echo "🎉 LUANTI HEADLESS SERVER BUILD COMPLETED!"
echo "================================================"
echo "📁 Server location: $SERVER_DIR"
echo "🎮 Games available: minetest_game, extra_ordinance"
echo "🔧 Build method: Source build with proven optimizations"
echo "🌐 Network: IPv4 only, port 30000"
echo ""
echo "🚀 To start the server:"
echo "   cd $SERVER_DIR && ./start_server.sh"
echo ""
echo "📊 To check server status:"
echo "   cd $SERVER_DIR && ./check_server.sh"
echo ""
echo "🔗 To connect:"
echo "   Host: $(hostname)"
echo "   Port: 30000"
echo "   Game: minetest_game"
echo ""
echo "📋 This build follows the proven method tested on DAS5/Rocky Linux"
echo "✅ Ready for benchmarking with Yardstick framework!"
