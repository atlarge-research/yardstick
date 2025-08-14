#!/bin/bash
#SBATCH --job-name=luanti_build_simple
#SBATCH --time=30:00
#SBATCH --mem=4G
#SBATCH --cpus-per-task=4
#SBATCH --output=/var/scratch/aco237/luanti_simple_build_%j.out
#SBATCH --error=/var/scratch/aco237/luanti_simple_build_%j.err

echo "🚀 Starting Luanti headless build on DAS5 compute node"
echo "Node: $(hostname)"
echo "Date: $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo "Working directory: $(pwd)"

# Load required modules on DAS5
echo "📦 Loading required modules..."
module load cmake/3.24.2
module list

echo "🔍 Checking dependencies..."
echo "GCC version: $(gcc --version | head -n1)"
echo "CMake version: $(cmake --version | head -n1)"
echo "Git version: $(git --version)"

# Set up build directory
BUILD_DIR="/var/scratch/aco237/luanti_headless_simple"
echo "🗂️  Setting up build directory: $BUILD_DIR"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Build LuaJIT first
echo "🔧 Building LuaJIT..."
git clone https://github.com/LuaJIT/LuaJIT.git luajit
cd luajit
make amalg
if [ $? -ne 0 ]; then
    echo "❌ LuaJIT build failed"
    exit 1
fi
echo "✅ LuaJIT build completed"
cd ..

# Clone and build Luanti
echo "🔧 Building Luanti..."
git clone -b stable-5 --depth 1 https://github.com/luanti-org/luanti.git
cd luanti
mkdir build
cd build

# Configure with CMake - use system libraries where possible
echo "⚙️  Configuring CMake..."
cmake .. \
    -DBUILD_CLIENT=0 \
    -DBUILD_SERVER=1 \
    -DRUN_IN_PLACE=1 \
    -DBUILD_UNITTESTS=0 \
    -DENABLE_GETTEXT=0 \
    -DENABLE_CURSES=0 \
    -DENABLE_CURL=0 \
    -DENABLE_POSTGRESQL=0 \
    -DENABLE_LEVELDB=0 \
    -DENABLE_REDIS=0 \
    -DLUA_INCLUDE_DIR=../../luajit/src/ \
    -DLUA_LIBRARY=../../luajit/src/libluajit.a

if [ $? -ne 0 ]; then
    echo "❌ CMake configuration failed"
    exit 1
fi

echo "🔨 Building Luanti server..."
make -j4

if [ $? -ne 0 ]; then
    echo "❌ Luanti build failed"
    exit 1
fi

# Check if binary was created
if [ -f "bin/luantiserver" ]; then
    echo "✅ Luanti server binary created successfully"
    ls -la bin/luantiserver
    
    # Set up a minimal test
    cd ../..
    echo "🧪 Setting up test environment..."
    
    # Copy essential files
    mkdir -p test_server
    cp luanti/build/bin/luantiserver test_server/
    cp -r luanti/builtin test_server/
    cp -r luanti/games test_server/
    
    # Create minimal config
    cat > test_server/luanti.conf << EOF
# Minimal test configuration
server_name = Test Server
server_address = 127.0.0.1
bind_address = 127.0.0.1
port = 30000
enable_ipv6 = false
ipv6_server = false
creative_mode = true
enable_damage = false
mg_name = flat
default_privs = interact, shout
EOF
    
    # Create minimal world
    mkdir -p test_server/worlds/test
    cat > test_server/worlds/test/world.mt << EOF
enable_damage = false
creative_mode = true
gameid = minetest
world_name = test
backend = sqlite3
EOF
    
    cd test_server
    chmod +x luantiserver
    
    echo "🎮 Testing server startup..."
    timeout 30s ./luantiserver --world worlds/test --config luanti.conf --terminal &
    SERVER_PID=$!
    
    # Give it a moment to start
    sleep 5
    
    # Check if server is running
    if kill -0 $SERVER_PID 2>/dev/null; then
        echo "✅ Server started successfully!"
        echo "🛑 Stopping test server..."
        kill $SERVER_PID
        wait $SERVER_PID 2>/dev/null
    else
        echo "❌ Server failed to start"
        exit 1
    fi
    
    echo "🏁 Build and test completed successfully!"
    echo "📁 Server ready at: $BUILD_DIR/test_server"
    
else
    echo "❌ Build failed - no binary found"
    exit 1
fi
