#!/usr/bin/env python3
"""
Local Luanti Benchmark Script for macOS

This script runs a Luanti server benchmark locally on macOS, including:
- Luanti server deployment and management
- Telegraf metrics collection
- Python-based bot workload
- Local metrics collection and analysis
"""

import argparse
import json
import logging
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ProcessManager:
    """Manages local processes for the benchmark."""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.temp_dirs: List[Path] = []
        
    def start_process(self, cmd: List[str], cwd: Optional[Path] = None, 
                     name: str = "process", capture_output: bool = True) -> subprocess.Popen:
        """Start a process and track it for cleanup."""
        logger.info(f"Starting {name}: {' '.join(cmd)}")
        if capture_output:
            proc = subprocess.Popen(
                cmd, 
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        else:
            proc = subprocess.Popen(
                cmd, 
                cwd=cwd,
                text=True
            )
        self.processes.append(proc)
        return proc
    
    def create_temp_dir(self, prefix: str = "benchmark_") -> Path:
        """Create a temporary directory and track it for cleanup."""
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def cleanup(self):
        """Clean up all processes and temporary directories."""
        logger.info("Cleaning up processes and temporary files...")
        
        # Terminate processes
        for proc in self.processes:
            if proc.poll() is None:  # Still running
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        
        # Clean up temp directories
        for temp_dir in self.temp_dirs:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

class LocalLuantiBenchmark:
    """Local Luanti benchmark orchestrator."""
    
    def __init__(self, args):
        self.args = args
        self.pm = ProcessManager()
        self.base_dir = Path(args.output_dir)
        self.benchmark_dir = self.setup_benchmark_directory()
        
        # Process references
        self.luanti_process = None
        self.telegraf_process = None
        self.bot_processes = []
        
    def setup_benchmark_directory(self) -> Path:
        """Set up the benchmark output directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        benchmark_dir = self.base_dir / f"luanti_benchmark_{timestamp}"
        benchmark_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Benchmark directory: {benchmark_dir}")
        return benchmark_dir
    
    def check_dependencies(self):
        """Check if required dependencies are available."""
        dependencies = {
            'python3': ['python3', '--version']
        }
        
        missing = []
        for name, cmd in dependencies.items():
            try:
                subprocess.run(cmd, capture_output=True, check=True)
                logger.info(f"✓ {name} is available")
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing.append(name)
                logger.error(f"✗ {name} is not available")
        
        if missing:
            logger.error("Missing dependencies. Please install:")
            for dep in missing:
                if dep == 'python3':
                    logger.error("  - Python 3: Available in macOS or install via Homebrew")
            sys.exit(1)
        
        # Check if Luanti executable exists
        luanti_path = Path(self.args.luanti_path)
        if not luanti_path.exists():
            logger.error(f"Luanti executable not found at: {luanti_path}")
            logger.error("Please provide a valid path to the Luanti executable")
            sys.exit(1)
        
        logger.info(f"✓ Luanti executable found at: {luanti_path}")
    
    def setup_luanti_config(self):
        """Create Luanti server configuration files."""
        # Create world directory
        world_dir = self.benchmark_dir / "worlds" / "yardstick_benchmark"
        world_dir.mkdir(parents=True, exist_ok=True)
        
        # Create world.mt file with appropriate game
        game_id = "extra_ordinance" if self.args.mod_config == "extra_ordinance" else "minetest_game"
        
        with open(world_dir / "world.mt", 'w') as f:
            f.write(f"""gameid = {game_id}
backend = sqlite3
creative_mode = true
disable_anticheat = true
enable_damage = false
""")
        
        # Create mods directory in the world directory (where Luanti expects them)
        world_mods_dir = world_dir / "worldmods"
        world_mods_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup games and mods based on configuration
        self.setup_games_and_mods(world_mods_dir)
        
        # Update world.mt to enable mods based on configuration (only for mod-based configs)
        if self.args.mod_config not in ["extra_ordinance", "vanilla"]:
            self.update_world_mt_for_mods(world_dir)
        
        # Server configuration
        config_file = self.benchmark_dir / "minetest.conf"
        with open(config_file, 'w') as f:
            f.write(f"""# Luanti benchmark server configuration
server_name = Local Luanti Benchmark Server ({self.args.mod_config})
server_description = Performance benchmark for Luanti with {self.args.mod_config} mod configuration
server_address = 127.0.0.1
port = {self.args.port}
disable_anticheat = true
creative_mode = true
enable_damage = false
default_privs = interact, shout, build, give, use, kick, ban, op, privs, server, admin, owner
max_users = 500
motd = Welcome to the Luanti benchmark server! Mod config: {self.args.mod_config}

# Game mechanics settings
creative_mode = true
enable_damage = false

# Performance settings
max_block_send_distance = 10
max_simultaneous_block_sends_per_client = 40
max_simultaneous_block_sends_server_total = 250
time_speed = 0

# # Network settings to handle more bots
max_packets_per_iteration = 2048
max_out_chat_queue_size = 50
dedicated_server_step = 0.05
player_transfer_distance = 15
active_object_send_range_blocks = 6
active_block_range = 3

# World generation settings
fixed_map_seed = benchmark
mg_name = v7
mg_flags = trees, caves, dungeons, decorations
water_level = 1
static_spawn_point = 0,20,0

# HTTP API settings for metrics
secure.enable_security = false
secure.trusted_mods = yardstick_collector
secure.http_mods = yardstick_collector
enable_http_api = true

# Logging settings for enhanced debugging
debug_log_level = action
enable_debug_log = true

# Mod settings
load_mod_yardstick_collector = true
""")
        
        return config_file, world_dir
    
    def setup_games_and_mods(self, world_mods_dir):
        """Setup different game/mod configurations for testing."""
        logger.info(f"Setting up configuration: {self.args.mod_config}")
        
        if self.args.mod_config == "extra_ordinance":
            # Extra Ordinance is already available as a game, just create yardstick collector
            logger.info("✅ Extra Ordinance game is available, using it directly")
            # Still create yardstick collector as a world mod for metrics
            self.create_yardstick_collector_mod(world_mods_dir)
        else:
            # For other configs, use default minetest_game with mods
            # Always create yardstick collector mod
            self.create_yardstick_collector_mod(world_mods_dir)
            
            if self.args.mod_config == "weather":
                self.setup_weather_mod(world_mods_dir)
            elif self.args.mod_config == "performance_test":
                self.setup_performance_test_mod(world_mods_dir)
            # vanilla = no additional mods
    
    def update_world_mt_for_mods(self, world_dir):
        """Update world.mt file to enable mods according to ContentDB instructions."""
        world_mt_path = world_dir / "world.mt"
        
        # Read existing content
        with open(world_mt_path, 'r') as f:
            content = f.read()
        
        # Add mod loading directives
        mod_lines = []
        mod_lines.append("load_mod_yardstick_collector = true")
        
        if self.args.mod_config == "extra_ordinance":
            mod_lines.append("load_mod_extra_ordinance = true")
        elif self.args.mod_config == "weather":
            mod_lines.append("load_mod_weather = true")
        elif self.args.mod_config == "performance_test":
            mod_lines.append("load_mod_performance_test = true")
        
        # Append mod loading directives
        content += "\n# Mod loading configuration\n"
        content += "\n".join(mod_lines) + "\n"
        
        # Write back to file
        with open(world_mt_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Updated world.mt with mod configuration: {self.args.mod_config}")
    
    def create_yardstick_collector_mod(self, world_mods_dir):
        """Create the yardstick collector mod (always present)."""
        mods_dir = world_mods_dir / "yardstick_collector"
        mods_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy existing mod if available
        src_mod_dir = Path("luanti_server/mods/yardstick_collector")
        if src_mod_dir.exists():
            shutil.copytree(src_mod_dir, mods_dir, dirs_exist_ok=True)
        else:
            # Create mod.conf file for the mod
            with open(mods_dir / "mod.conf", 'w') as f:
                f.write("""name = yardstick_collector
description = Luanti performance metrics collector for benchmarking
depends = 
optional_depends = 
""")
            
            # Create TSV-based metrics collector
            with open(mods_dir / "init.lua", 'w') as f:
                f.write('''-- Luanti Tick Duration Collector for Yardstick Benchmarking
-- TSV-based metrics collection

local last_time = minetest.get_us_time()
local tick_count = 0
local start_time = minetest.get_us_time()

-- Create metrics file in mod_storage (where Luanti has write permissions)
local metrics_file = minetest.get_worldpath() .. "/mod_storage/tick_metrics.tsv"
local player_file = minetest.get_worldpath() .. "/mod_storage/player_metrics.tsv"

-- Initialize metrics files
local function init_metrics()
    -- Create mod_storage directory if it doesn't exist
    minetest.mkdir(minetest.get_worldpath() .. "/mod_storage")
    
    -- Initialize tick metrics file
    local file = io.open(metrics_file, "w")
    if file then
        file:write("timestamp_s\\ttick_duration_ms\\ttick_count\\tplayers_online\\n")
        file:close()
        minetest.log("action", "YARDSTICK: Initialized tick metrics file: " .. metrics_file)
    else
        minetest.log("error", "YARDSTICK: Failed to create tick metrics file: " .. metrics_file)
    end
    
    -- Initialize player metrics file
    local pfile = io.open(player_file, "w")
    if pfile then
        pfile:write("timestamp_s\\tevent_type\\tplayer_name\\ttotal_players\\n")
        pfile:close()
        minetest.log("action", "YARDSTICK: Initialized player metrics file: " .. player_file)
    else
        minetest.log("error", "YARDSTICK: Failed to create player metrics file: " .. player_file)
    end
end

-- Record tick performance
minetest.register_globalstep(function(dtime)
    local now = minetest.get_us_time()
    local duration_us = now - last_time
    last_time = now
    tick_count = tick_count + 1
    
    -- Convert to useful units
    local timestamp_s = now / 1e6  -- seconds since epoch
    local duration_ms = duration_us / 1000  -- milliseconds
    local players_online = #minetest.get_connected_players()
    
    -- Write metrics every tick (for detailed analysis)
    local file = io.open(metrics_file, "a")
    if file then
        file:write(string.format("%.3f\\t%.3f\\t%d\\t%d\\n", 
            timestamp_s, duration_ms, tick_count, players_online))
        file:close()
    end
    
    -- Log significant lag events
    if duration_ms > 100 then  -- More than 100ms (should be ~50ms for 20 TPS)
        minetest.log("warning", string.format("YARDSTICK: High tick duration: %.2fms (players: %d)", 
            duration_ms, players_online))
    end
end)

-- Track player connections
minetest.register_on_joinplayer(function(player)
    local now = minetest.get_us_time()
    local timestamp_s = now / 1e6
    local player_name = player:get_player_name()
    local total_players = #minetest.get_connected_players()
    
    local file = io.open(player_file, "a")
    if file then
        file:write(string.format("%.3f\\tjoin\\t%s\\t%d\\n", 
            timestamp_s, player_name, total_players))
        file:close()
    end
    
    minetest.log("action", string.format("YARDSTICK: Player joined: %s (total: %d)", 
        player_name, total_players))
end)

minetest.register_on_leaveplayer(function(player, timed_out)
    local now = minetest.get_us_time()
    local timestamp_s = now / 1e6
    local player_name = player:get_player_name()
    local total_players = #minetest.get_connected_players() - 1  -- Player hasn't left yet
    
    local file = io.open(player_file, "a")
    if file then
        file:write(string.format("%.3f\\tleave\\t%s\\t%d\\n", 
            timestamp_s, player_name, total_players))
        file:close()
    end
    
    local reason = timed_out and "timeout" or "quit"
    minetest.log("action", string.format("YARDSTICK: Player left: %s (%s, total: %d)", 
        player_name, reason, total_players))
end)

-- Initialize when mods are loaded
minetest.register_on_mods_loaded(function()
    init_metrics()
    minetest.log("action", "YARDSTICK: Tick duration collector loaded successfully")
end)

-- Final summary on shutdown
minetest.register_on_shutdown(function()
    local now = minetest.get_us_time()
    local total_time_s = (now - start_time) / 1e6
    local avg_tps = tick_count / total_time_s
    
    minetest.log("action", string.format("YARDSTICK: Shutdown summary - Ticks: %d, Time: %.1fs, Avg TPS: %.2f", 
        tick_count, total_time_s, avg_tps))
end)
''')
    
    def setup_extra_ordinance_game(self):
        """Set up Extra Ordinance as a complete game."""
        logger.info("Setting up Extra Ordinance game...")
        
        # Copy to the Luanti.app's games directory so it can find it
        luanti_app_path = Path(self.args.luanti_path).parent.parent.parent  # Go up from MacOS/luanti to Luanti.app
        luanti_games_dir = luanti_app_path / "Contents" / "Resources" / "games"
        
        # Source: downloaded game directory
        source_game_dir = Path("./luanti_server/mods/extra_ordinance")
        target_game_dir = luanti_games_dir / "extra_ordinance"
        
        if not source_game_dir.exists():
            logger.error("❌ Extra Ordinance game not found!")
            logger.error("Please download it manually from ContentDB")
            raise FileNotFoundError("Extra Ordinance game not available")
        
        # Copy the game to Luanti.app
        try:
            if target_game_dir.exists():
                shutil.rmtree(target_game_dir)
            shutil.copytree(source_game_dir, target_game_dir)
            logger.info(f"✅ Extra Ordinance game copied to {target_game_dir}")
        except Exception as e:
            logger.error(f"Failed to copy Extra Ordinance game: {e}")
            logger.error("You may need to run with sudo or adjust permissions")
            # Fallback: just log the error and continue with placeholder
            logger.info("Continuing with vanilla game instead...")
            return False
        
        return True

    def setup_extra_ordinance_mod(self, world_mods_dir):
        """Copy Extra Ordinance mod from the downloaded version."""
        logger.info("Setting up Extra Ordinance mod...")
        
        # Source: downloaded mod directory
        source_mod_dir = Path("./luanti_server/mods/extra_ordinance")
        target_mod_dir = world_mods_dir / "extra_ordinance"
        
        if not source_mod_dir.exists():
            logger.error("❌ Extra Ordinance mod not found!")
            logger.error("Please run: python3 setup_extra_ordinance.py")
            logger.info("Creating a simple placeholder mod instead...")
            
            # Create placeholder mod
            target_mod_dir.mkdir(parents=True, exist_ok=True)
            with open(target_mod_dir / "mod.conf", 'w') as f:
                f.write("""name = extra_ordinance_placeholder
description = Placeholder for Extra Ordinance mod (mod not downloaded)
depends = default
""")
            
            with open(target_mod_dir / "init.lua", 'w') as f:
                f.write('''-- Placeholder for Extra Ordinance mod
-- Simulates some computational load

local function simulate_ordinance_load()
    -- Simulate some CPU-intensive operations
    local sum = 0
    for i = 1, 1000 do
        sum = sum + math.sin(i) * math.cos(i)
    end
    return sum
end

minetest.register_globalstep(function(dtime)
    -- Run every 5 seconds to simulate mod activity
    if math.random() < 0.01 then  -- ~1% chance per tick
        simulate_ordinance_load()
        minetest.log("action", "Extra Ordinance placeholder: simulated load")
    end
end)

minetest.log("action", "Extra Ordinance placeholder mod loaded")
''')
            return
        
        # Copy the real mod
        try:
            if target_mod_dir.exists():
                shutil.rmtree(target_mod_dir)
            shutil.copytree(source_mod_dir, target_mod_dir)
            logger.info(f"✅ Extra Ordinance mod copied to {target_mod_dir}")
        except Exception as e:
            logger.error(f"Failed to copy Extra Ordinance mod: {e}")
            raise
    
    def setup_weather_mod(self, world_mods_dir):
        """Create a simple weather mod for testing."""
        logger.info("Setting up weather mod...")
        
        mod_dir = world_mods_dir / "weather"
        mod_dir.mkdir(parents=True, exist_ok=True)
        
        with open(mod_dir / "mod.conf", 'w') as f:
            f.write("""name = weather
description = Simple weather simulation for benchmarking
depends = default
""")
        
        with open(mod_dir / "init.lua", 'w') as f:
            f.write('''-- Simple weather mod for testing
local weather_timer = 0
local weather_effects = {"rain", "snow", "clear", "storm"}
local current_weather = 1

minetest.register_globalstep(function(dtime)
    weather_timer = weather_timer + dtime
    if weather_timer > 30 then  -- Change weather every 30 seconds
        weather_timer = 0
        current_weather = (current_weather % #weather_effects) + 1
        local weather = weather_effects[current_weather]
        
        -- Broadcast weather change to all players
        for _, player in pairs(minetest.get_connected_players()) do
            minetest.chat_send_player(player:get_player_name(), 
                "Weather changed to: " .. weather)
        end
        
        minetest.log("action", "Weather changed to: " .. weather)
    end
end)

minetest.log("action", "Weather mod loaded")
''')
    
    def setup_performance_test_mod(self, world_mods_dir):
        """Create a performance-intensive test mod."""
        logger.info("Setting up performance test mod...")
        
        mod_dir = world_mods_dir / "performance_test"
        mod_dir.mkdir(parents=True, exist_ok=True)
        
        with open(mod_dir / "mod.conf", 'w') as f:
            f.write("""name = performance_test
description = Performance test mod - intentionally CPU/memory intensive
depends = default
""")
        
        with open(mod_dir / "init.lua", 'w') as f:
            f.write('''-- Performance test mod - intentionally CPU/memory intensive
local particle_count = 0
local calculation_timer = 0

-- Heavy calculation function
local function heavy_calculation()
    local sum = 0
    for i = 1, 10000 do
        sum = sum + math.sin(i) * math.cos(i) * math.sqrt(i)
    end
    return sum
end

-- Spawn lots of particles for visual/network load
local function spawn_particles(pos)
    if particle_count < 500 then
        minetest.add_particlespawner({
            amount = 50,
            time = 1,
            minpos = {x=pos.x-10, y=pos.y-10, z=pos.z-10},
            maxpos = {x=pos.x+10, y=pos.y+10, z=pos.z+10},
            minvel = {x=-2, y=-2, z=-2},
            maxvel = {x=2, y=2, z=2},
            minacc = {x=0, y=-10, z=0},
            maxacc = {x=0, y=-5, z=0},
            minexptime = 1,
            maxexptime = 3,
            minsize = 1,
            maxsize = 3,
            texture = "default_dirt.png",
        })
        particle_count = particle_count + 50
    end
end

minetest.register_globalstep(function(dtime)
    calculation_timer = calculation_timer + dtime
    if calculation_timer > 0.1 then  -- Every 100ms
        calculation_timer = 0
        
        -- Do heavy calculations
        local result = heavy_calculation()
        
        -- Spawn particles around players
        for _, player in pairs(minetest.get_connected_players()) do
            local pos = player:get_pos()
            spawn_particles(pos)
        end
        
        -- Reset particle count periodically
        if particle_count > 1000 then
            particle_count = 0
        end
    end
end)

minetest.log("action", "Performance test mod loaded")
''')
    
    def install_telegraf(self) -> Path:
        """Install Telegraf for metrics collection."""
        telegraf_dir = self.benchmark_dir / "telegraf"
        telegraf_dir.mkdir(exist_ok=True)
        
        # Check if Telegraf is installed via Homebrew
        try:
            result = subprocess.run(['which', 'telegraf'], capture_output=True, text=True)
            if result.returncode == 0:
                telegraf_bin = Path(result.stdout.strip())
                logger.info(f"Using system Telegraf: {telegraf_bin}")
                return telegraf_bin
        except:
            pass
        
        # Download Telegraf binary
        telegraf_bin = telegraf_dir / "telegraf"
        if telegraf_bin.exists():
            logger.info("Telegraf already downloaded")
            return telegraf_bin
        
        logger.info("Downloading Telegraf...")
        import platform
        arch = platform.machine().lower()
        if arch == 'arm64':
            url = "https://dl.influxdata.com/telegraf/releases/telegraf-1.28.5_darwin_arm64.tar.gz"
        else:
            url = "https://dl.influxdata.com/telegraf/releases/telegraf-1.28.5_darwin_amd64.tar.gz"
        
        try:
            import urllib.request
            import tarfile
            
            # Download and extract
            tar_path = telegraf_dir / "telegraf.tar.gz"
            urllib.request.urlretrieve(url, tar_path)
            
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(telegraf_dir)
            
            # Find the extracted binary
            for item in telegraf_dir.rglob("telegraf"):
                if item.is_file() and os.access(item, os.X_OK):
                    telegraf_bin = item
                    break
            
            os.chmod(telegraf_bin, 0o755)
            logger.info(f"Downloaded and extracted Telegraf to {telegraf_bin}")
            
        except Exception as e:
            logger.error(f"Failed to download Telegraf: {e}")
            logger.info("You can install Telegraf manually with: brew install telegraf")
            sys.exit(1)
        
        return telegraf_bin
    
    def create_telegraf_config(self, telegraf_bin: Path) -> Path:
        """Create Telegraf configuration for local monitoring."""
        config_path = self.benchmark_dir / "telegraf.conf"
        
        config = f"""
# Telegraf Configuration for Local Luanti Benchmark

[agent]
  interval = "1s"
  round_interval = true
  metric_batch_size = 1000
  metric_buffer_limit = 10000
  collection_jitter = "0s"
  flush_interval = "1s"
  flush_jitter = "0s"
  precision = ""

# Output to file (since we don't have InfluxDB locally)
[[outputs.file]]
  files = ["{self.benchmark_dir}/metrics.json"]
  data_format = "json"
  json_timestamp_units = "1s"

# System metrics
[[inputs.cpu]]
  percpu = true
  totalcpu = true

[[inputs.disk]]
  ignore_fs = ["tmpfs", "devtmpfs"]

[[inputs.diskio]]

[[inputs.mem]]

[[inputs.processes]]

[[inputs.system]]

# Luanti tick metrics from TSV file
[[inputs.tail]]
  files = ["{self.benchmark_dir}/luanti_tick_metrics.tsv"]
  from_beginning = true
  data_format = "csv"
  csv_header_row_count = 1
  csv_delimiter = "\\t"
  csv_column_names = ["timestamp_s", "tick_duration_ms", "tick_count", "players_online"]
  csv_column_types = ["float", "float", "int", "int"]
  name_override = "luanti_tick_metrics"
  csv_timestamp_column = "timestamp_s"
  csv_timestamp_format = "unix"

# Luanti player events from TSV file
[[inputs.tail]]
  files = ["{self.benchmark_dir}/luanti_player_metrics.tsv"]
  from_beginning = true
  data_format = "csv"
  csv_header_row_count = 1
  csv_delimiter = "\\t"
  csv_column_names = ["timestamp_s", "event_type", "player_name", "total_players"]
  csv_column_types = ["float", "string", "string", "int"]
  name_override = "luanti_player_events"
  csv_timestamp_column = "timestamp_s"
  csv_timestamp_format = "unix"
"""
        
        with open(config_path, 'w') as f:
            f.write(config)
        
        return config_path
    
    def start_luanti_server(self, config_file: Path, world_dir: Path):
        """Start the Luanti server."""
        logger.info("Starting Luanti server...")
        
        # Determine game ID and setup games path
        game_id = "extra_ordinance" if self.args.mod_config == "extra_ordinance" else "minetest_game"
        
        cmd = [
            str(Path(self.args.luanti_path).absolute()),
            '--config', str(config_file.absolute()),
            '--world', str(world_dir.absolute()),
            '--gameid', game_id,
            '--server'
        ]
        
        # Note: Extra Ordinance game should be installed in Luanti.app/Contents/Resources/games/
        
        # Start server without capturing output so we can see logs in real-time
        self.luanti_process = self.pm.start_process(
            cmd, 
            cwd=self.benchmark_dir,
            name="Luanti Server",
            capture_output=False
        )
        
        # Wait for server to start
        logger.info("Waiting for server to start...")
        max_wait_time = 30  # 30 seconds max wait
        check_interval = 2  # Check every 2 seconds
        
        for i in range(max_wait_time // check_interval):
            time.sleep(check_interval)
            
            # Check if process died
            if self.luanti_process.poll() is not None:
                logger.error("Luanti server process exited unexpectedly")
                sys.exit(1)
            
            # Check if server is ready by testing UDP connection
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(1)
                sock.connect(('127.0.0.1', self.args.port))
                sock.close()
                logger.info("Server is accepting connections")
                return
            except:
                pass
            
            logger.info(f"Waiting for server... ({(i+1)*check_interval}s elapsed)")
        
        # Final check
        if self.luanti_process.poll() is None:
            logger.info("Server appears to be running (final check passed)")
        else:
            logger.error("Luanti server failed to start within timeout period")
            sys.exit(1)
    
    def start_telegraf(self, telegraf_bin: Path, config_path: Path):
        """Start Telegraf with local configuration."""
        logger.info("Starting Telegraf...")
        
        cmd = [str(telegraf_bin), '--config', str(config_path)]
        
        self.telegraf_process = self.pm.start_process(
            cmd,
            name="Telegraf"
        )
        
        time.sleep(2)
        
        if self.telegraf_process.poll() is not None:
            logger.error("Telegraf failed to start")
            sys.exit(1)
        
        logger.info("Telegraf started successfully")
    
    def build_rust_bots(self) -> tuple[Path, Path]:
        """Build the Rust bots (walkbot and blockbot) if needed."""
        bot_dir = Path("bot_components/texmodbot")
        
        if not bot_dir.exists():
            logger.error("Rust bot directory not found. Please ensure bot_components/texmodbot exists")
            sys.exit(1)
        
        # Check if binaries exist
        walkbot_bin = bot_dir / "target" / "release" / "walkbot"
        blockbot_bin = bot_dir / "target" / "release" / "blockbot"
        
        if walkbot_bin.exists() and blockbot_bin.exists():
            logger.info(f"Using existing bot binaries: {walkbot_bin}, {blockbot_bin}")
            return walkbot_bin, blockbot_bin
        
        # Build the bots
        logger.info("Building Rust bots (walkbot and blockbot)...")
        try:
            # Check if Cargo is available
            subprocess.run(['cargo', '--version'], capture_output=True, check=True)
            logger.info("✓ Cargo is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("✗ Cargo (Rust) is not available")
            logger.error("Please install Rust: https://rustup.rs/")
            sys.exit(1)
        
        # Build in release mode
        build_cmd = ['cargo', 'build', '--release']
        result = subprocess.run(build_cmd, cwd=bot_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error("Failed to build bots:")
            logger.error(result.stderr)
            sys.exit(1)
        
        if not walkbot_bin.exists():
            logger.error("Walkbot binary not found after build")
            sys.exit(1)
            
        if not blockbot_bin.exists():
            logger.error("Blockbot binary not found after build")
            sys.exit(1)
        
        logger.info(f"Successfully built bots: {walkbot_bin}, {blockbot_bin}")
        return walkbot_bin, blockbot_bin
    
    def start_bots(self, walkbot_bin: Path, blockbot_bin: Path):
        """Start the Rust bot workload (walkbots or blockbots)."""
        bot_type = self.args.bot_type
        logger.info(f"Starting {self.args.bots} Rust {bot_type}s...")
        
        # Choose the appropriate binary
        bot_bin = walkbot_bin if bot_type == "walkbot" else blockbot_bin
        
        # Start individual bots with staggered connections
        for i in range(self.args.bots):
            username = f"bench{bot_type}_{i:03d}"
            
            if bot_type == "walkbot":
                cmd = [
                    str(bot_bin),
                    f"127.0.0.1:{self.args.port}",
                    "--username", username,
                    "--password", "benchmark123",
                    "--auto-register",
                    "--quit-after-seconds", str(self.args.duration),
                    "--mode", self.args.movement_mode,
                    "--speed", "2.0"
                ]
            else:  # blockbot
                # Build near spawn location (0, 9.5, 123)
                start_x = (i % 5) * 3  # Spread bots in X direction (0, 3, 6, 9, 12...)
                start_z = 120 + (i // 5) * 3  # Near Z=123 spawn coordinate (120, 123, 126...)
                cmd = [
                    str(bot_bin),
                    f"127.0.0.1:{self.args.port}",
                    "--username", username,
                    "--password", "benchmark123",
                    "--auto-register",
                    "--quit-after-seconds", str(self.args.duration),
                    "--pattern", self.args.building_pattern,
                    "--speed", "2.0",
                    "--max-blocks", "200",  # Limit blocks per bot to avoid infinite building
                    "--start-x", str(start_x),  # Build near spawn X coordinate
                    "--start-z", str(start_z),  # Build near spawn Z coordinate (123)
                    "--start-y", "9.0",  # Build near spawn Y coordinate
                ]
            
            bot_process = self.pm.start_process(
                cmd, 
                name=f"{bot_type.capitalize()}-{username}",
                capture_output=False  # Don't capture output so we can see debug messages
            )
            self.bot_processes.append(bot_process)
            
            # Stagger bot connections more to avoid overwhelming the server
            time.sleep(0.8)
            
            logger.info(f"Started {bot_type} {i+1}/{self.args.bots}: {username}")
        
        logger.info(f"All {self.args.bots} {bot_type}s started successfully")
        
        # Wait longer for all bots to connect and check status
        logger.info("Waiting for all bots to connect...")
        time.sleep(10)
        self.check_bot_status()
    
    def check_bot_status(self):
        """Check the status of running bots."""
        running_bots = 0
        failed_bots = 0
        
        for i, bot_process in enumerate(self.bot_processes):
            if bot_process.poll() is None:
                running_bots += 1
            else:
                failed_bots += 1
                # Get error output if available
                try:
                    stdout, stderr = bot_process.communicate(timeout=1)
                    if stderr:
                        logger.warning(f"Bot {i} failed with error: {stderr}")
                except Exception:
                    pass
    
        logger.info(f"Bot status: {running_bots} running, {failed_bots} failed")
        
        if running_bots == 0:
            logger.error("No bots are running! Check server connectivity and bot configuration")
        elif failed_bots > 0:
            logger.warning(f"{failed_bots} bots failed to start or connect")
    
    def check_luanti_metrics(self):
        """Check and display Luanti application metrics from mod_storage TSV files."""
        # Check for metrics files in the world's mod_storage directory
        world_dir = self.benchmark_dir / "worlds" / "yardstick_benchmark"
        tick_metrics_file = world_dir / "mod_storage" / "tick_metrics.tsv"
        player_metrics_file = world_dir / "mod_storage" / "player_metrics.tsv"
        
        if tick_metrics_file.exists():
            logger.info("✓ Luanti tick metrics collected!")
            logger.info(f"  Tick metrics file: {tick_metrics_file}")
            
            # Quick analysis of the tick metrics
            try:
                import pandas as pd
                df = pd.read_csv(tick_metrics_file, sep='\t')
                
                if len(df) > 0:
                    logger.info(f"  Total tick records: {len(df)}")
                    logger.info(f"  Max players online: {df['players_online'].max()}")
                    logger.info(f"  Average tick duration: {df['tick_duration_ms'].mean():.2f}ms")
                    logger.info(f"  Peak tick duration: {df['tick_duration_ms'].max():.2f}ms")
                    logger.info(f"  Total ticks processed: {df['tick_count'].max()}")
                    
                    # Calculate TPS (ticks per second)
                    if len(df) > 1:
                        time_span = df['timestamp_s'].max() - df['timestamp_s'].min()
                        tick_span = df['tick_count'].max() - df['tick_count'].min()
                        avg_tps = tick_span / time_span if time_span > 0 else 0
                        logger.info(f"  Average TPS: {avg_tps:.2f} (target: 20.0)")
                    
                    # Count lag events (> 100ms tick duration)
                    lag_events = df[df['tick_duration_ms'] > 100]
                    if len(lag_events) > 0:
                        logger.info(f"  Lag events (>100ms): {len(lag_events)}")
                        logger.info(f"  Worst lag: {lag_events['tick_duration_ms'].max():.2f}ms")
                        
                        # Show worst lag events
                        worst_lags = lag_events.nlargest(3, 'tick_duration_ms')
                        for _, row in worst_lags.iterrows():
                            logger.info(f"    {row['tick_duration_ms']:.1f}ms lag at tick {row['tick_count']} ({row['players_online']} players)")
                    else:
                        logger.info("  No significant lag events detected")
                else:
                    logger.warning("  Tick metrics file is empty - server may not have started properly")
                    
            except ImportError:
                logger.info("  (Install pandas for detailed metrics analysis)")
                # Basic analysis without pandas
                try:
                    with open(tick_metrics_file, 'r') as f:
                        lines = f.readlines()[1:]  # Skip header
                        logger.info(f"  Total tick records: {len(lines)}")
                        if lines:
                            last_line = lines[-1].strip().split('\t')
                            logger.info(f"  Final tick count: {last_line[2]}")
                            logger.info(f"  Final player count: {last_line[3]}")
                except Exception as e:
                            logger.warning(f"  Could not analyze tick metrics: {e}")
        else:
            logger.warning("⚠️ No Luanti tick metrics file found")
            logger.warning(f"  Expected location: {tick_metrics_file}")
            logger.warning("  Check server logs for mod loading issues")
        
        # Check player metrics
        if player_metrics_file.exists():
            logger.info("✓ Luanti player metrics collected!")
            logger.info(f"  Player metrics file: {player_metrics_file}")
            
            try:
                with open(player_metrics_file, 'r') as f:
                    lines = f.readlines()[1:]  # Skip header
                    logger.info(f"  Total player events: {len(lines)}")
                    
                    # Count joins vs leaves
                    joins = sum(1 for line in lines if '\tjoin\t' in line)
                    leaves = sum(1 for line in lines if '\tleave\t' in line)
                    logger.info(f"  Player joins: {joins}, leaves: {leaves}")
                    
            except Exception as e:
                logger.warning(f"  Could not analyze player metrics: {e}")
        else:
            logger.info("ℹ️ No player metrics file found (this is normal if no player events occurred)")

    def copy_luanti_metrics_for_telegraf(self):
        """Copy Luanti metrics from mod_storage to benchmark directory for Telegraf."""
        world_dir = self.benchmark_dir / "worlds" / "yardstick_benchmark"
        source_tick_file = world_dir / "mod_storage" / "tick_metrics.tsv"
        source_player_file = world_dir / "mod_storage" / "player_metrics.tsv"
        
        # Copy tick metrics for Telegraf
        dest_tick_file = self.benchmark_dir / "luanti_tick_metrics.tsv"
        if source_tick_file.exists():
            shutil.copy2(source_tick_file, dest_tick_file)
            logger.info(f"✓ Copied tick metrics for Telegraf: {dest_tick_file}")
        else:
            logger.warning(f"⚠️ Source tick metrics not found: {source_tick_file}")
        
        # Copy player metrics for Telegraf
        dest_player_file = self.benchmark_dir / "luanti_player_metrics.tsv"
        if source_player_file.exists():
            shutil.copy2(source_player_file, dest_player_file)
            logger.info(f"✓ Copied player metrics for Telegraf: {dest_player_file}")
        else:
            logger.info("ℹ️ No player metrics to copy (normal if no player events occurred)")
        
        return dest_tick_file.exists()
    
    def run_benchmark(self):
        """Run the complete benchmark."""
        logger.info("="*60)
        logger.info("LOCAL LUANTI BENCHMARK")
        logger.info("="*60)
        logger.info(f"Duration: {self.args.duration}s")
        logger.info(f"Bots: {self.args.bots} ({self.args.bot_type})")
        if self.args.bot_type == "walkbot":
            logger.info(f"Movement Mode: {self.args.movement_mode}")
        else:
            logger.info(f"Building Pattern: {self.args.building_pattern}")
        logger.info(f"Port: {self.args.port}")
        logger.info(f"Luanti Path: {self.args.luanti_path}")
        logger.info(f"Output: {self.benchmark_dir}")
        logger.info("="*60)
        
        try:
            # Check dependencies
            self.check_dependencies()
            
            # Setup Luanti server
            config_file, world_dir = self.setup_luanti_config()
            
            # Setup monitoring
            telegraf_bin = self.install_telegraf()
            telegraf_config = self.create_telegraf_config(telegraf_bin)
            
            # Start server
            self.start_luanti_server(config_file, world_dir)
            
            # Start monitoring
            self.start_telegraf(telegraf_bin, telegraf_config)
            
            # Build and start Rust bots
            walkbot_bin, blockbot_bin = self.build_rust_bots()
            self.start_bots(walkbot_bin, blockbot_bin)
            
            # Run benchmark
            logger.info(f"Running benchmark for {self.args.duration} seconds...")
            time.sleep(self.args.duration)
            
            # Give server a moment to write final metrics
            logger.info("Waiting for final metrics collection...")
            time.sleep(5)
            
            # Copy Luanti metrics from mod_storage for analysis
            self.copy_luanti_metrics_for_telegraf()
            
            logger.info("="*60)
            logger.info("BENCHMARK COMPLETED")
            logger.info(f"Results saved to: {self.benchmark_dir}")
            logger.info("="*60)
            
            # Check metrics
            metrics_file = self.benchmark_dir / "metrics.json"
            if metrics_file.exists():
                size_mb = metrics_file.stat().st_size / (1024 * 1024)
                logger.info(f"✓ System metrics: {metrics_file} ({size_mb:.2f} MB)")
            else:
                logger.warning("⚠️ System metrics file not found")
            
            # Check Luanti-specific metrics
            self.check_luanti_metrics()
            
            logger.info("="*60)
            
        except KeyboardInterrupt:
            logger.info("Benchmark interrupted by user")
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            raise
        finally:
            self.pm.cleanup()

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run local Luanti benchmark on macOS",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument("--duration", type=int, default=60,
                       help="Benchmark duration in seconds")
    parser.add_argument("--bots", type=int, default=2,
                       help="Number of bots to spawn")
    parser.add_argument("--port", type=int, default=30000,
                       help="Luanti server port")
    parser.add_argument("--luanti-path", 
                       default="/Users/alx/Documents/Thesis/code/luantick/luanti_server/Luanti.app/Contents/MacOS/luanti",
                       help="Path to Luanti executable")
    parser.add_argument("--output-dir", default="./local_benchmark_results",
                       help="Output directory for benchmark results")
    parser.add_argument("--movement-mode", type=str, default="circular",
                       choices=["random", "circular", "straight", "static"],
                       help="Bot movement pattern")
    parser.add_argument("--bot-type", type=str, default="walkbot",
                       choices=["walkbot", "blockbot"],
                       help="Type of bot to use (walkbot for movement, blockbot for building)")
    parser.add_argument("--building-pattern", type=str, default="tower",
                       choices=["tower", "wall", "platform", "random", "spiral", "house"],
                       help="Building pattern for blockbot (ignored for walkbot)")
    parser.add_argument("--mod-config", type=str, default="vanilla",
                       choices=["vanilla", "extra_ordinance", "weather", "performance_test"],
                       help="Mod configuration to test")
    
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_arguments()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        logger.info("Received interrupt signal, cleaning up...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run benchmark
    benchmark = LocalLuantiBenchmark(args)
    benchmark.run_benchmark()

if __name__ == "__main__":
    main()
