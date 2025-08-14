# How to Build and Run Luanti Server Headless on Linux

This guide covers building and running a Luanti (formerly Minetest) headless server on Linux systems, specifically tested on DAS5/Rocky Linux.

## Prerequisites

### Required System Packages
- `git` - for cloning repositories
- `cmake` (3.5+) - build system
- `gcc/g++` - C++ compiler
- `make` - build tool

### Required Development Libraries
- `sqlite-devel` (or `libsqlite3-dev` on Debian/Ubuntu)
- `libcurl-devel` (or `libcurl4-openssl-dev`)
- `zlib-devel` (or `zlib1g-dev`)
- `gmp-devel` (or `libgmp-dev`)
- `jsoncpp-devel` (or `libjsoncpp-dev`)
- `ncurses-devel` (or `libncurses5-dev`)

### Optional (for better performance)
- `ninja-build` - faster build system

## Step-by-Step Build Process

### 1. Set Up Build Environment

```bash
# Create a working directory
mkdir -p /tmp/luanti_build
cd /tmp/luanti_build

# On module-based systems (like DAS5), load required modules
module load cmake/3.24.2  # or whatever version is available
```

### 2. Build LuaJIT (Recommended)

```bash
# Clone LuaJIT
git clone https://github.com/LuaJIT/LuaJIT.git luajit
cd luajit

# Build LuaJIT
make amalg

# Verify build
ls -la src/libluajit.a  # Should exist
cd ..
```

### 3. Clone and Build Luanti

```bash
# Clone Luanti stable version
git clone -b stable-5 --depth 1 https://github.com/luanti-org/luanti.git
cd luanti

# Create build directory
mkdir build
cd build

# Configure with CMake (headless server only)
cmake .. \
    -DBUILD_CLIENT=0 \
    -DBUILD_SERVER=1 \
    -DRUN_IN_PLACE=1 \
    -DBUILD_UNITTESTS=0 \
    -DENABLE_GETTEXT=0 \
    -DLUA_INCLUDE_DIR=../../luajit/src/ \
    -DLUA_LIBRARY=../../luajit/src/libluajit.a

# Build (use -j4 for parallel build)
make -j4

# Verify binary was created
ls -la bin/luantiserver  # Should exist and be executable
```

## Server Configuration

### 1. Set Up Server Directory Structure

```bash
# From the luanti directory
cd ..
mkdir -p server_deploy

# Copy essential files
cp build/bin/luantiserver server_deploy/
cp -r builtin server_deploy/
cp -r games server_deploy/

# Create directories
mkdir -p server_deploy/worlds/testworld
mkdir -p server_deploy/logs
```

### 2. Download Minetest Game (if not included)

```bash
cd server_deploy/games
git clone https://github.com/minetest/minetest_game.git
cd ../..
```

### 3. Create Server Configuration

Create `server_deploy/luanti.conf`:

```ini
# Server settings
server_name = My Luanti Server
server_description = Headless Luanti server
server_address = 127.0.0.1
bind_address = 127.0.0.1
port = 30000
max_users = 100

# Admin settings
name = admin

# Network settings - IPv4 only
enable_ipv6 = false
ipv6_server = false
enable_server = true

# Game settings
creative_mode = true
enable_damage = false
default_privs = interact, shout

# World generation
mg_name = flat
static_spawnpoint = 0, 80, 0
fixed_map_seed = 12345

# Performance settings
dedicated_server_step = 0.1
time_speed = 0

# Logging
debug_log_level = action
logfile = logs/server.log
```

### 4. Create World Configuration

Create `server_deploy/worlds/testworld/world.mt`:

```ini
enable_damage = false
creative_mode = true
gameid = minetest
world_name = testworld
backend = sqlite3
```

## Running the Server

### Basic Server Start

```bash
cd server_deploy
./luantiserver --world worlds/testworld --config luanti.conf --port 30000
```

### Background Server with Logging

```bash
cd server_deploy
nohup ./luantiserver --world worlds/testworld --config luanti.conf --port 30000 --logfile logs/server.log &
echo $! > server.pid
```

### Stop Background Server

```bash
# Read PID and stop server
if [ -f server.pid ]; then
    kill $(cat server.pid)
    rm server.pid
fi
```

## Common Issues and Solutions

### 1. IPv6 Binding Errors
**Problem**: Server tries to bind to IPv6 addresses
**Solution**: Set `enable_ipv6 = false` and `bind_address = 127.0.0.1`

### 2. Missing Game Error
**Problem**: "No games found" or "Game not found"
**Solution**: Ensure `minetest_game` is in the `games/` directory and `gameid = minetest` in world.mt

### 3. Permission Denied
**Problem**: Binary not executable
**Solution**: `chmod +x luantiserver`

### 4. Missing Libraries
**Problem**: Shared library errors at runtime
**Solution**: Install missing development packages or use static linking

### 5. Port Already in Use
**Problem**: Address already in use
**Solution**: Change port in config or kill existing server process

## Testing the Server

### 1. Quick Startup Test
```bash
timeout 10s ./luantiserver --world worlds/testworld --config luanti.conf
# Should start and run for 10 seconds without errors
```

### 2. Check if Port is Open
```bash
netstat -an | grep :30000
# Should show LISTEN state when server is running
```

### 3. Connect with Client
- Set up SSH tunnel if on remote server: `ssh -L 30000:hostname:30000 user@server`
- Connect Luanti client to `localhost:30000`

## Automation Scripts

### Build Script Example
```bash
#!/bin/bash
set -e

BUILD_DIR="/tmp/luanti_build"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Build LuaJIT
git clone https://github.com/LuaJIT/LuaJIT.git luajit
cd luajit && make amalg && cd ..

# Build Luanti
git clone -b stable-5 --depth 1 https://github.com/luanti-org/luanti.git
cd luanti && mkdir build && cd build

cmake .. -DBUILD_CLIENT=0 -DBUILD_SERVER=1 -DRUN_IN_PLACE=1 \
    -DLUA_INCLUDE_DIR=../../luajit/src/ -DLUA_LIBRARY=../../luajit/src/libluajit.a

make -j4

echo "Build complete. Binary at: $(pwd)/bin/luantiserver"
```

### Deployment Script Example
```bash
#!/bin/bash
DEPLOY_DIR="/path/to/server"
BUILD_DIR="/tmp/luanti_build"

mkdir -p "$DEPLOY_DIR"
cp "$BUILD_DIR/luanti/build/bin/luantiserver" "$DEPLOY_DIR/"
cp -r "$BUILD_DIR/luanti/builtin" "$DEPLOY_DIR/"
cp -r "$BUILD_DIR/luanti/games" "$DEPLOY_DIR/"

# Setup configuration files...
```

## Performance Considerations

1. **CPU**: Use `-j$(nproc)` for parallel building
2. **Memory**: Ensure at least 1GB available for building
3. **Storage**: Build requires ~500MB, deployment ~100MB
4. **Network**: IPv4-only configuration reduces complexity

This guide provides a complete workflow for building and running Luanti headless servers on Linux systems.
