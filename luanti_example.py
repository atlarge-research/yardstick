import logging
import os
import subprocess
import shutil
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from yardstick_benchmark.provisioning import Das
from yardstick_benchmark.monitoring import Telegraf
from yardstick_benchmark.games.luanti.server import LuantiServer
from yardstick_benchmark.games.luanti.workload import RustWalkAround, RustBlockBot
import yardstick_benchmark

from time import sleep
import tempfile

# Configure logging for better visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

print("✓ Imports successful")

# === Benchmark Management Helpers (from notebook) ===
from pathlib import Path as _Path

def prepare_enhanced_benchmark_run(num_bots, duration=120, bot_type="walkbot",
                                   movement_mode="random", notes=""):
    """Create a timestamped benchmark directory with rich metadata and update luanti_output symlink."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = _Path("/var/scratch/aco237/yardstick")
    new_output_dir = base_path / f"luanti_benchmark_{timestamp}_bots{num_bots}_{bot_type}_{movement_mode}"
    new_output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "benchmark_id": f"luanti_{timestamp}_bots{num_bots}",
        "timestamp": datetime.now().isoformat(),
        "configuration": {
            "num_bots": num_bots,
            "duration_seconds": duration,
            "bot_type": bot_type,
            "movement_mode": movement_mode,
            "server_version": "luanti-5.11.0",
            "world_type": "benchmark",
            "game_mode": "minetest_game"
        },
        "experiment_context": {
            "research_question": "player_capacity_scaling",
            "hypothesis": f"Server can handle {num_bots} {bot_type}s with {movement_mode} movement",
            "notes": notes,
            "related_benchmarks": [],
            "expected_outcomes": {
                "target_tps": 20.0,
                "acceptable_lag_threshold_ms": 75.0,
                "expected_performance_category": "excellent" if num_bots <= 50 else "good"
            }
        },
        "system_info": {
            "cluster": "DAS-5",
            "nodes_planned": 2,
            "collection_methods": ["telegraf_system", "luanti_tick_metrics", "player_events"]
        }
    }

    metadata_file = new_output_dir / "benchmark_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    params_file = new_output_dir / "benchmark_params.txt"
    with open(params_file, 'w') as f:
        f.write(f"Number of bots: {num_bots}\n")
        f.write(f"Bot type: {bot_type}\n")
        f.write(f"Movement mode: {movement_mode}\n")
        f.write(f"Benchmark duration: {duration}s\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Notes: {notes}\n")

    # Update symlink used by analysis code
    original_output = base_path / "luanti_output"
    try:
        if original_output.exists() or original_output.is_symlink():
            original_output.unlink()
        # Use relative link to keep paths portable inside base path
        original_output.symlink_to(new_output_dir.name)
    except Exception as e:
        logger.warning(f"Could not update luanti_output symlink: {e}")

    print(f"🎯 Enhanced benchmark directory: {new_output_dir}")
    return str(new_output_dir), metadata

def list_benchmark_runs():
    """List existing benchmark directories for quick reference."""
    base_path = _Path("/var/scratch/aco237/yardstick")
    pattern = "luanti_benchmark_*"
    benchmark_dirs = list(base_path.glob(pattern))
    benchmark_dirs.sort()
    print("📊 Available benchmark runs:")
    print("-" * 60)
    for i, directory in enumerate(benchmark_dirs, 1):
        params_file = directory / "benchmark_params.txt"
        if params_file.exists():
            try:
                with open(params_file, 'r') as f:
                    first_line = f.readline().strip()
                print(f"{i:2d}. {directory.name} — {first_line}")
            except Exception:
                print(f"{i:2d}. {directory.name} (metadata unreadable)")
        else:
            print(f"{i:2d}. {directory.name} (no params file)")
    current_link = base_path / "luanti_output"
    if current_link.is_symlink():
        print(f"🔗 Current analysis target: {current_link.readlink()}")
    return benchmark_dirs

def check_dependencies():
    """Check if required tools and paths are available."""
    logger.info("Checking dependencies...")
    
    # Check if yardstick_benchmark is properly installed
    try:
        import yardstick_benchmark
        logger.info("✓ yardstick_benchmark module available")
    except ImportError:
        logger.error("✗ yardstick_benchmark module not found")
        raise ImportError("Please ensure the yardstick benchmark framework is properly installed")
    
    # Check if bot components exist
    bot_dir = Path("bot_components/texmodbot")
    if not bot_dir.exists():
        logger.error(f"✗ Rust bot directory not found: {bot_dir}")
        raise FileNotFoundError("Please ensure bot_components/texmodbot exists")
    logger.info(f"✓ Rust bot components found: {bot_dir}")
    
    # Check output directory permissions
    dest = Path(f"/var/scratch/{os.getlogin()}/yardstick/luanti_output")
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Output directory accessible: {dest}")
    except Exception as e:
        logger.error(f"✗ Cannot access output directory: {e}")
        raise
    
    return dest

# Run dependency check
dest = check_dependencies()
print(f"Dependencies checked successfully. Results will be saved to: {dest}")

# 🎮 LUANTI BENCHMARK CONFIGURATION - UPDATED PROVEN BUILD METHOD
# ================================================================
# This configuration uses our tested and proven build method that works on DAS5

# === MAIN SETTINGS ===
BOTS_PER_NODE = 50          # Number of bots per bot node (tested and working)
BENCHMARK_DURATION = 90    # Benchmark duration in seconds
NUM_NODES = 2          # Start with 2 nodes: 1 server + 1 bot node

# === BOT TYPE SETTINGS ===
BOT_TYPE = "walkbot"        # walkbot, blockbot
MOVEMENT_MODE = "random"    # Random movement (tested)
BUILDING_PATTERN = "tower"  # tower, wall, platform, house
MOVEMENT_SPEED = 2.0        # Speed in seconds between actions
MAX_BUILDING_BLOCKS = -1    # (-1) for unlimited building blocks; 
SPAWN_RADIUS = 0          # 0 is for hotspot

# === GAME CONFIGURATION ===
GAME_MODE = "extra_ordinance" # Use standard minetest_game (most reliable)

# === PROVEN BUILD CONFIGURATION ===
# Based on our successful manual testing and documentation
USE_HEADLESS_BUILD = True           # Use headless server build (no client dependencies)
BUILD_WITH_LUAJIT = True            # Build with LuaJIT for better performance
ENABLE_IPV4_ONLY = True             # Use IPv4 only (fixes connection issues)
USE_SYSTEM_LIBS = True              # Use system libraries where available
DISABLE_UNNECESSARY_FEATURES = True  # Disable gettext, client features, etc.

# === NETWORK CONFIGURATION ===
SERVER_PORT = 30000         # Standard Luanti port
SERVER_BIND_ADDRESS = "127.0.0.1"  # IPv4 localhost binding
DISABLE_IPV6 = True         # Explicitly disable IPv6

# === SPAWN AREA POSITIONING ===
SPAWN_X = 0
SPAWN_Y = 9.5
SPAWN_Z = 123
BUILD_NEAR_SPAWN = True     # Position bots near spawn area

# === ADVANCED SETTINGS ===
COLLECT_ALL_NODES = True    # Monitor all nodes (server + all bot nodes)
VERBOSE_PROGRESS = True     # Show detailed progress during benchmark

# === CALCULATED VALUES ===
TOTAL_BOTS = BOTS_PER_NODE * (NUM_NODES - 1)  # Total bots across all bot nodes


for i in range(2, NUM_NODES + 1):
    bot_group = chr(64 + i - 1)  # A, B, C, etc.


expected_runtime = BENCHMARK_DURATION + 300  # 5 minutes overhead for build
movement_mode_arg = f"{MOVEMENT_MODE}:{SPAWN_RADIUS}" if BOT_TYPE == "walkbot" else f"{BUILDING_PATTERN}:{SPAWN_RADIUS}"

prepare_enhanced_benchmark_run(num_bots=BOTS_PER_NODE, movement_mode=movement_mode_arg, bot_type=BOT_TYPE, duration=BENCHMARK_DURATION)  # or whatever number you want
try:
    def provision_nodes_with_validation(num_nodes: int = 2):
        """Provision nodes on the DAS cluster with validation."""
        logger.info(f"Provisioning {num_nodes} nodes on DAS cluster...")
        
        das = Das()
        try:
            nodes = das.provision(num=num_nodes, time_s=5500)
            
            logger.info(f"✓ Successfully provisioned {len(nodes)} nodes:")
            for i, node in enumerate(nodes):
                logger.info(f"  Node {i}: {node.host} (wd: {node.wd})")
            return das, nodes
        except Exception as e:
            logger.error(f"✗ Failed to provision nodes: {e}")
            raise

    start_time = datetime.now()


    das, nodes = provision_nodes_with_validation(num_nodes=NUM_NODES)

    yardstick_benchmark.clean(nodes)


    telegraf = Telegraf(nodes)
        
    telegraf.add_input_luanti_metrics(nodes[0])  # Server node
    res = telegraf.deploy()
    telegraf.start()
    telegraf.deploy()
    telegraf.start()


    luanti_server = LuantiServer(
        nodes[:1], 
        game_mode=GAME_MODE,        # Use our configured game mode
        use_source_build=False,     # Use source build method (for headless)
        enable_luajit=False,        # Enable LuaJIT
        ipv4_only=ENABLE_IPV4_ONLY  # IPv4 only configuration
    )

    try:
        luanti_server.deploy()
        luanti_server.start()

        
        # Give server time to fully initialize
        sleep(10)
    except Exception as e:
        print(f"❌ Error starting Luanti server: {e}")
        print("Server may have failed to bind to the configured address/port.")
        raise

    node = nodes[0]
    if BOT_TYPE == "walkbot":
        try:
            walkbot_workload = RustWalkAround(
                nodes[1:] if len(nodes) > 1 else nodes[:1],  # Use second node if available
                server_host=node.host,
                server_port=30000,
                bots_per_node=BOTS_PER_NODE,
                duration=timedelta(seconds=BENCHMARK_DURATION),
                movement_mode=MOVEMENT_MODE,
                movement_speed=2.0,
                spawn_radius=SPAWN_RADIUS
            )
            
            walkbot_workload.deploy()
            
            walkbot_workload.start()
            time.sleep(BENCHMARK_DURATION + 10)  # Extra 10 seconds for cleanup

        except Exception as e:
                print(f"❌ Error running walkbot benchmark: {e}")
    elif BOT_TYPE == "blockbot":
        try:
            blockbot_workload = RustBlockBot(
                nodes[1:] if len(nodes) > 1 else nodes[:1],  # Use second node if available
                server_host=node.host,
                server_port=30000,
                bots_per_node=BOTS_PER_NODE,
                duration=timedelta(seconds=BENCHMARK_DURATION),
                building_pattern=BUILDING_PATTERN,    # Try tower pattern
                building_speed=2.0,          # 2 seconds between blocks
                max_blocks=MAX_BUILDING_BLOCKS,               # Limit blocks per bot
                destructive_mode=False,      # Don't dig blocks initially
                start_x=10.0,                # Build away from spawn
                start_y=8.0,                 # Ground level
                start_z=130.0,                # Near spawn Z coordinate
                spawn_radius=SPAWN_RADIUS
            )
            
            print("🏗️ Deploying blockbots...")
            blockbot_workload.deploy()
            
            print("🏃 Starting blockbot workload...")
            blockbot_workload.start()
            
            print(f"⏳ Running benchmark for {BENCHMARK_DURATION + 10} seconds...")
            print("📊 Monitor server metrics during this time...")
            
            # Wait for the benchmark to complete
            time.sleep(BENCHMARK_DURATION + 10)
        except Exception as e:
                print(f"❌ Error running blockbot benchmark: {e}")

    luanti_server.stop()

    telegraf.stop()
    yardstick_benchmark.fetch(dest, nodes)
finally:
    print('done')
    list_benchmark_runs()

    # yardstick_benchmark.clean(nodes)
    # das.release(nodes)

    # CELL 1 — Gather + normalize Luanti metrics, then cache (Parquet if possible, otherwise CSV)

import os
from pathlib import Path
import pandas as pd

def _get_user():
    try:
        return os.getlogin()
    except Exception:
        for k in ("USER", "LOGNAME", "USERNAME"):
            v = os.environ.get(k)
            if v:
                return v
    return "unknown"

USER = _get_user()
BASE = Path(f"/var/scratch/{USER}/yardstick/luanti_output")

def _find_latest_server_dir(base: Path) -> Path | None:
    dirs = sorted(base.glob("*/luanti_server-*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return dirs[0] if dirs else None

def _load_local_metrics(base: Path):
    latest = _find_latest_server_dir(base)
    if latest is None:
        print("No local luanti_server-* directory found.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    ms = latest / "worlds" / "benchmark" / "mod_storage"
    tick = pd.read_csv(ms / "tick_metrics.tsv", sep="\t") if (ms / "tick_metrics.tsv").exists() else pd.DataFrame()
    player = pd.read_csv(ms / "player_metrics.tsv", sep="\t") if (ms / "player_metrics.tsv").exists() else pd.DataFrame()
    inter = pd.read_csv(ms / "interaction_metrics.tsv", sep="\t") if (ms / "interaction_metrics.tsv").exists() else pd.DataFrame()
    for df in (tick, player, inter):
        if not df.empty:
            df["source_node"] = latest.parent.name
    return tick, player, inter

def _normalize_ticks(df_raw: pd.DataFrame) -> pd.DataFrame:
    if df_raw.empty:
        return df_raw
    df = df_raw.copy()
    # tick_duration
    if "tick_duration_ms" in df.columns:
        df["tick_duration"] = pd.to_numeric(df["tick_duration_ms"], errors="coerce")
    elif "tick_duration" in df.columns:
        df["tick_duration"] = pd.to_numeric(df["tick_duration"], errors="coerce")
    else:
        raise ValueError("tick_duration_ms not found in tick_metrics.tsv")
    # tick_number
    if "tick_count" in df.columns:
        df["tick_number"] = pd.to_numeric(df["tick_count"], errors="coerce")
    else:
        df["tick_number"] = range(1, len(df) + 1)
    # players_online (optional)
    df["players_online"] = pd.to_numeric(df.get("players_online", pd.NA), errors="coerce")
    # relative time
    if "timestamp_s" in df.columns:
        df["timestamp_s"] = pd.to_numeric(df["timestamp_s"], errors="coerce")
        df["t_rel_s"] = df["timestamp_s"] - df["timestamp_s"].min()
    else:
        df["t_rel_s"] = pd.Series(range(len(df)), dtype=float)
    # derived
    df["tps"] = (1000.0 / df["tick_duration"]).clip(lower=0, upper=1000)
    df = df.dropna(subset=["tick_duration", "tick_number", "tps"]).sort_values("tick_number").reset_index(drop=True)
    return df[["tick_number", "tick_duration", "tps", "players_online", "t_rel_s", "source_node"]]

def _normalize_players(df_raw: pd.DataFrame) -> pd.DataFrame:
    if df_raw.empty:
        return df_raw
    df = df_raw.copy()
    if "timestamp_s" in df.columns:
        df["timestamp_s"] = pd.to_numeric(df["timestamp_s"], errors="coerce")
        df["t_rel_s"] = df["timestamp_s"] - df["timestamp_s"].min()
    else:
        df["t_rel_s"] = pd.NA
    for col in ("event_type", "player_name", "total_players"):
        if col not in df.columns:
            df[col] = pd.NA
    keep = ["timestamp_s", "event_type", "player_name", "total_players", "t_rel_s", "source_node"]
    return df[[c for c in keep if c in df.columns]]

def _save_with_fallback(df: pd.DataFrame, parquet_path: Path):
    """
    Try Parquet (pyarrow). If any error occurs (ArrowKeyError, engine missing, etc.),
    fall back to CSV next to it.
    """
    if df.empty:
        return None
    try:
        # Light touch: avoid extension types by ensuring objects are plain Python types
        df_to_save = df.copy()
        for col in df_to_save.columns:
            if pd.api.types.is_object_dtype(df_to_save[col]):
                df_to_save[col] = df_to_save[col].astype("string").astype(object)
        df_to_save.to_parquet(parquet_path, index=False, engine="pyarrow")
        print(f"✔ Saved Parquet: {parquet_path}")
        return parquet_path
    except Exception as e:
        csv_path = parquet_path.with_suffix(".csv")
        df.to_csv(csv_path, index=False)
        print(f"⚠ Parquet failed ({type(e).__name__}: {e}). Saved CSV instead: {csv_path}")
        return csv_path

# --- load + normalize ---
tick_raw, player_raw, interaction_raw = _load_local_metrics(BASE)
tick_df = _normalize_ticks(tick_raw) if not tick_raw.empty else pd.DataFrame()
player_df = _normalize_players(player_raw) if not player_raw.empty else pd.DataFrame()
interaction_df = interaction_raw.copy()  # not used in plots, keep raw

# --- summary ---
print("=== METRICS LOAD SUMMARY ===")
print(f"Ticks: {len(tick_df):,}")
if not tick_df.empty:
    print(f"  mean tick (ms)={tick_df['tick_duration'].mean():.2f}, TPS={tick_df['tps'].mean():.2f}")
print(f"Players: {len(player_df):,}")
print(f"Interactions: {len(interaction_df):,}")

# --- cache with fallback ---
cache_dir = BASE / "_cache_for_plots"
cache_dir.mkdir(parents=True, exist_ok=True)
tick_cache = _save_with_fallback(tick_df, cache_dir / "tick_df.parquet")
player_cache = _save_with_fallback(player_df, cache_dir / "player_df.parquet")
interaction_cache = _save_with_fallback(interaction_df, cache_dir / "interaction_df.parquet")
print("Cache ready.")


# CELL 2 — Visualize metrics; reads Parquet if present, otherwise CSV (from Cell 1)

import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def _get_user():
    try:
        return os.getlogin()
    except Exception:
        for k in ("USER", "LOGNAME", "USERNAME"):
            v = os.environ.get(k)
            if v:
                return v
    return "unknown"

USER = _get_user()
BASE = Path(f"/var/scratch/{USER}/yardstick/luanti_output/_cache_for_plots")

def _read_cached(name: str) -> pd.DataFrame:
    pq = BASE / f"{name}.parquet"
    csv = BASE / f"{name}.csv"
    if pq.exists():
        try:
            return pd.read_parquet(pq, engine="pyarrow")
        except Exception as e:
            print(f"⚠ Failed to read Parquet ({name}): {e}")
    if csv.exists():
        return pd.read_csv(csv)
    return pd.DataFrame()

tick_df = _read_cached("tick_df")
player_df = _read_cached("player_df")

if tick_df.empty:
    raise FileNotFoundError("No cached tick dataframe found. Run Cell 1 first.")

# Lower bound for x-axis (tick number)
X_MIN = 6000
max_tick = tick_df["tick_number"].max() if "tick_number" in tick_df.columns else None
apply_xlim = max_tick is not None and max_tick >= X_MIN

# 1) TPS over time
plt.figure(figsize=(10, 4))
plt.plot(tick_df["tick_number"], tick_df["tps"], linewidth=0.8)
plt.axhline(y=20, linestyle="--", linewidth=1)
plt.xlabel("Tick number")
plt.ylabel("TPS")
plt.title("TPS over time")
plt.grid(True, alpha=0.3)
if apply_xlim:
    plt.xlim(left=X_MIN)
plt.show()

# 2) Tick duration histogram (not tick-number based; leave unchanged)
plt.figure(figsize=(10, 4))
plt.hist(tick_df["tick_duration"], bins=50, edgecolor="black", linewidth=0.5)
plt.axvline(x=50, linestyle="--", linewidth=1)  # 50 ms ≈ 20 TPS
plt.xlabel("Tick duration (ms)")
plt.ylabel("Count")
plt.title("Tick duration distribution")
plt.grid(True, alpha=0.3)
plt.show()

# 3) Performance categories (aggregate; unchanged)
excellent = (tick_df["tick_duration"] <= 50).sum()
good      = ((tick_df["tick_duration"] > 50) & (tick_df["tick_duration"] <= 75)).sum()
fair      = ((tick_df["tick_duration"] > 75) & (tick_df["tick_duration"] <= 100)).sum()
poor      = (tick_df["tick_duration"] > 100).sum()
total     = len(tick_df)

plt.figure(figsize=(8, 4))
cats = ["≤50 ms", "50–75 ms", "75–100 ms", ">100 ms"]
vals = [excellent, good, fair, poor]
plt.bar(cats, vals)
for i, v in enumerate(vals):
    pct = (v/total*100) if total else 0
    plt.text(i, v + max(1, total*0.01), f"{pct:.1f}%", ha="center", va="bottom")
plt.ylabel("Ticks")
plt.title("Performance categories")
plt.grid(True, axis="y", alpha=0.3)
plt.show()

# 4) Rolling average TPS
window = max(5, min(100, total // 20))
roll = tick_df["tps"].rolling(window=window, center=True).mean()

plt.figure(figsize=(10, 4))
plt.plot(tick_df["tick_number"], roll, linewidth=1.5, label=f"{window}-tick rolling avg")
plt.axhline(y=20, linestyle="--", linewidth=1)
plt.xlabel("Tick number")
plt.ylabel("TPS (rolling)")
plt.title("TPS rolling average")
plt.grid(True, alpha=0.3)
if apply_xlim:
    plt.xlim(left=X_MIN)
plt.legend()
plt.show()

# 5) Lag timeline
lag_thr, sev_thr = 75, 100
lag = tick_df[tick_df["tick_duration"] > lag_thr]
sev = tick_df[tick_df["tick_duration"] > sev_thr]

plt.figure(figsize=(10, 4))
plt.scatter(tick_df["tick_number"], tick_df["tick_duration"], s=4, alpha=0.3, label="all")
if not lag.empty:
    plt.scatter(lag["tick_number"], lag["tick_duration"], s=6, alpha=0.8, label=f">{lag_thr} ms")
if not sev.empty:
    plt.scatter(sev["tick_number"], sev["tick_duration"], s=8, alpha=0.9, label=f">{sev_thr} ms")
plt.axhline(y=50, linestyle="--", linewidth=1)
plt.xlabel("Tick number")
plt.ylabel("Tick duration (ms)")
plt.title("Lag events over time")
plt.grid(True, alpha=0.3)
if apply_xlim:
    plt.xlim(left=X_MIN)
plt.legend()
plt.show()

# 6) Summary
def pct(x):
    return (x/total*100) if total else 0

# Peak tick duration & lowest TPS
peak_tick_ms = float(tick_df["tick_duration"].max()) if not tick_df.empty else float("nan")
lowest_tps   = float(tick_df["tps"].min())           if not tick_df.empty else float("nan")

# Max concurrent players (joins/leaves over time)
max_concurrent = "N/A"
if not player_df.empty and "event_type" in player_df.columns:
    time_col = next((c for c in ["timestamp", "event_time", "time", "ts"] if c in player_df.columns), None)
    if time_col is not None:
        ev = player_df[[time_col, "event_type"]].copy()
        ev = ev[ev["event_type"].str.lower().isin(["join", "leave"])].copy()
        if not ev.empty:
            ev["delta"] = ev["event_type"].str.lower().map({"join": 1, "leave": -1})
            ev = ev.sort_values([time_col, "delta"])
            cur = ev["delta"].cumsum()
            if not cur.empty:
                max_concurrent = int(cur.max())

print("\n===== PERFORMANCE SUMMARY =====")
print(f"Ticks: {total:,}")
print(f"Avg tick duration: {tick_df['tick_duration'].mean():.2f} ms")
print(f"Avg TPS: {tick_df['tps'].mean():.2f} (target: 20)")
print(f"≤50 ms: {excellent:,} ({pct(excellent):.1f}%)")
print(f"50–75 ms: {good:,} ({pct(good):.1f}%)")
print(f"75–100 ms: {fair:,} ({pct(fair):.1f}%)")
print(f">100 ms: {poor:,} ({pct(poor):.1f}%)")

if not player_df.empty and "player_name" in player_df.columns and "event_type" in player_df.columns:
    print(f"Players: unique={player_df['player_name'].nunique(dropna=True)}, "
          f"joins={(player_df['event_type'].str.lower()=='join').sum()}, "
          f"leaves={(player_df['event_type'].str.lower()=='leave').sum()}")

print(f"Max players online (concurrent): {max_concurrent}")
print(f"Peak tick duration (ms): {peak_tick_ms:.2f}")
print(f"Lowest TPS recorded: {lowest_tps:.2f}")


# --- Cell: CPU & MEM visualization from telegraf CSVs (robust, headerless) ---

from pathlib import Path
import glob, math
import pandas as pd
import matplotlib.pyplot as plt

base = Path("/var/scratch/aco237/yardstick/luanti_output")

print("===== DEBUG: METRICS DIRECTORY SEARCH =====")
print(f"Base directory: {base}")
print(f"Exists: {base.exists()}\n")

# Show a few interesting paths to confirm the structure
print("Contents of base directory (first 3 levels):")
for p in sorted(base.rglob("*")):
    rel = str(p.relative_to(base))
    # keep output short
    if len(rel.split("/")) <= 3:
        print(" ", base / rel)
print()

# Glob patterns we are using (matches your example metrics-nodeXXX.csv files)
cpu_mem_glob = str(base / "node*/telegraf-*/*metrics*.csv")
print("Searching for metric files with pattern:", cpu_mem_glob)

metric_files = sorted(glob.glob(cpu_mem_glob))
print(f"Found {len(metric_files)} metric files:")
for f in metric_files:
    print(" ", f)
if not metric_files:
    print("\nNo metric files found. Double-check the experiment output paths.")
    raise SystemExit

def _to_float(x):
    try:
        return float(x)
    except Exception:
        return math.nan

def parse_metrics_csv(path):
    """
    Parse only CPU and MEM rows from a mixed, headerless telegraf CSV:
      - CPU rows format (observed):
        ts, cpu, core_id, cpu_name, host, physical_id,
        time_active, time_guest, time_guest_nice, time_idle,
        time_iowait, time_irq, time_nice, time_softirq, time_steal,
        time_system, time_user
      - MEM rows (typical telegraf order, no header):
        ts, mem, host, total, available, used, free, buffered, cached, used_percent, ...
    """
    cpu_rows = []
    mem_rows = []
    p = Path(path)
    node = p.parent.parent.name  # .../nodeXYZ/telegraf-.../metrics-nodeXYZ.csv

    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line or "," not in line:
                continue
            parts = line.split(",")
            # need at least measurement
            if len(parts) < 3:
                continue

            measurement = parts[1].strip()

            # --- CPU rows ---
            if measurement == "cpu":
                # minimally: ts, cpu, core_id, cpu_name, host, physical_id + 11 time_* fields
                if len(parts) >= 17:
                    ts = _to_float(parts[0])
                    core_id = parts[2].strip()
                    cpu_name = parts[3].strip()
                    host = parts[4].strip()
                    # fields layout (based on your sample)
                    time_active      = _to_float(parts[6])
                    time_guest       = _to_float(parts[7])   # not used in util
                    time_guest_nice  = _to_float(parts[8])   # not used in util
                    time_idle        = _to_float(parts[9])
                    time_iowait      = _to_float(parts[10])  # not used in util
                    time_irq         = _to_float(parts[11])  # not used in util
                    time_nice        = _to_float(parts[12])  # not used in util
                    time_softirq     = _to_float(parts[13])  # not used in util
                    time_steal       = _to_float(parts[14])  # not used in util
                    time_system      = _to_float(parts[15])  # not used in util
                    time_user        = _to_float(parts[16])  # not used in util

                    time_total = time_active + time_idle
                    util = 100.0 * time_active / time_total if time_total > 0 else math.nan

                    # Keep only total row to mirror your earlier plot (cpu-total)
                    if cpu_name == "cpu-total":
                        cpu_rows.append({
                            "timestamp": ts,
                            "node": node,
                            "host": host,
                            "cpu": cpu_name,
                            "core_id": core_id,
                            "util": util
                        })

            # --- MEM rows ---
            elif measurement == "mem":
                # Try common telegraf order:
                # ts, mem, host, total, available, used, free, buffered, cached, used_percent, ...
                # Some deployments omit available; we handle length flexibly.
                ts = _to_float(parts[0])
                host = parts[2].strip()
                total = available = used = free = used_percent = math.nan

                if len(parts) >= 6:
                    total = _to_float(parts[3])
                if len(parts) >= 7:
                    available = _to_float(parts[4])
                if len(parts) >= 8:
                    used = _to_float(parts[5])
                if len(parts) >= 9:
                    free = _to_float(parts[6])
                if len(parts) >= 10:
                    # buffered
                    pass
                if len(parts) >= 11:
                    # cached
                    pass
                if len(parts) >= 12:
                    # used_percent (typical index 9 from start -> parts[10], but here we are at 12th)
                    # Many telegraf builds put used_percent right after cached; if this value
                    # looks like a percentage, take it. Otherwise we compute below.
                    maybe_pct = _to_float(parts[10])  # best-guess
                    if 0.0 <= maybe_pct <= 100.0:
                        used_percent = maybe_pct

                if math.isnan(used_percent):
                    # Compute if we can
                    denom = used + free
                    if denom > 0 and not math.isnan(used) and not math.isnan(free):
                        used_percent = 100.0 * used / denom
                    elif total > 0 and not math.isnan(used):
                        used_percent = 100.0 * used / total

                mem_rows.append({
                    "timestamp": ts,
                    "node": node,
                    "host": host,
                    "mem_used_percent": used_percent,
                    "mem_used": used,
                    "mem_total": total,
                    "mem_free": free,
                    "mem_available": available
                })

            # ignore other measurements (net, nstat, kernel, swap, …)

    cpu_df = pd.DataFrame(cpu_rows)
    mem_df = pd.DataFrame(mem_rows)
    return cpu_df, mem_df

# Parse all files
cpu_parts, mem_parts = [], []
for f in metric_files:
    c, m = parse_metrics_csv(f)
    if not c.empty:
        cpu_parts.append(c)
    if not m.empty:
        mem_parts.append(m)

cpu_df = pd.concat(cpu_parts, ignore_index=True) if cpu_parts else pd.DataFrame(columns=["timestamp","node","host","cpu","core_id","util"])
mem_df = pd.concat(mem_parts, ignore_index=True) if mem_parts else pd.DataFrame(columns=["timestamp","node","host","mem_used_percent"])

# Report counts
print(f"\nCPU points: {len(cpu_df)} | MEM points: {len(mem_df)}")

if cpu_df.empty and mem_df.empty:
    print("\nNo CPU or MEM rows parsed from the metric files above.")
    print("Tip: open one of the files and check the measurement names in the 2nd column.")
else:
    # Normalize timestamps per node to start at zero and add minutes
    for df in (cpu_df, mem_df):
        if not df.empty:
            df["t0"] = df.groupby("node")["timestamp"].transform("min")
            df["timestamp_s"] = df["timestamp"] - df["t0"]
            df["timestamp_m"] = df["timestamp_s"] / 60.0

    # --- Plot CPU utilization over time (per node, cpu-total only) ---
    if not cpu_df.empty:
        fig = plt.figure(figsize=(8,4))
        for node, grp in cpu_df.groupby("node"):
            grp = grp.sort_values("timestamp_s")
            plt.plot(grp["timestamp_m"], grp["util"], label=node)
        plt.xlim(9, 15)
        plt.ylim(bottom=0)
        plt.xlabel("Time [min]")
        plt.ylabel("CPU utilization [%] (cpu-total)")
        plt.title("CPU utilization over time")
        plt.grid(axis="y")
        plt.legend(title="node", bbox_to_anchor=(1.02, 1), loc="upper left")
        plt.tight_layout()
        plt.show()
    else:
        print("No cpu-total rows found to plot CPU utilization.")

    # --- Plot Memory utilization over time (per node) ---
    if not mem_df.empty:
        fig = plt.figure(figsize=(8,4))
        for node, grp in mem_df.groupby("node"):
            grp = grp.sort_values("timestamp_s")
            plt.plot(grp["timestamp_m"], grp["mem_used_percent"], label=node)
        plt.ylim(bottom=0)
        plt.xlabel("Time [min]")
        plt.ylabel("Memory utilization [%]")
        plt.title("Memory utilization over time")
        plt.grid(axis="y")
        plt.legend(title="node", bbox_to_anchor=(1.02, 1), loc="upper left")
        plt.tight_layout()
        plt.show()
    else:
        print("No MEM rows found to plot memory utilization.")

# Optional: identify the first node (server) if you want to highlight it later
if not cpu_df.empty:
    first_node = sorted(cpu_df['node'].unique())[0]
    print("\nAssuming first node is the server node:", first_node)


# Updated download script to get BOTH log files
def download_complete_server_logs():
    """Download both server.log and startup.log for complete analysis"""
    
    print("📥 COMPLETE SERVER LOG DOWNLOAD")
    print("=" * 35)
    
    import subprocess
    import os
    from pathlib import Path
    from datetime import datetime
    
    username = os.getlogin()
    import json
    download_dir = Path(f"/var/scratch/aco237/server_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    download_dir.mkdir(parents=True, exist_ok=True)
    
    # Both important log files
    log_files_to_download = [
        'server.log',    # Performance warnings, errors
        'startup.log',   # Player joins, leaves, actions
    ]
    
    total_downloaded = 0
    
    for node in nodes:
        print(f"\n🔍 Downloading from: {node.host}")
        
        try:
            # Find server directory
            find_cmd = f'ssh {node.host} "find /local/{username}/yardstick/*/luanti_server-* -type d 2>/dev/null | head -1"'
            server_dir_result = subprocess.run(find_cmd, shell=True, capture_output=True, text=True)
            
            if server_dir_result.returncode == 0 and server_dir_result.stdout.strip():
                server_dir = server_dir_result.stdout.strip()
                server_name = Path(server_dir).name
                
                for log_file in log_files_to_download:
                    remote_path = f"{server_dir}/logs/{log_file}"
                    local_path = download_dir / f"{node.host}_{log_file}"
                    
                    # Check file size first
                    size_cmd = f'ssh {node.host} "ls -l {remote_path} 2>/dev/null | awk \'{{print \\$5}}\' || echo 0"'
                    size_result = subprocess.run(size_cmd, shell=True, capture_output=True, text=True)
                    
                    try:
                        file_size = int(size_result.stdout.strip())
                        if file_size > 0:
                            # Download the file
                            scp_cmd = f"scp {username}@{node.host}:{remote_path} {local_path}"
                            scp_res = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
                            
                            if scp_res.returncode == 0:
                                print(f"  ✅ {log_file}: {file_size:,} bytes downloaded")
                                total_downloaded += 1
                            else:
                                print(f"  ❌ {log_file}: Download failed")
                        else:
                            print(f"  ⚠️  {log_file}: Empty or missing")
                    except ValueError:
                        print(f"  ❌ {log_file}: Could not check size")
            else:
                print(f"  ❌ No server directory found")
                
        except Exception as e:
            print(f"  ❌ Error accessing {node.host}: {e}")
    
    print(f"\n🎯 DOWNLOAD COMPLETE")
    print(f"📊 Total files downloaded: {total_downloaded}")
    print(f"📁 Saved to: {download_dir}")
    
    # Analyze the downloaded logs
    if total_downloaded > 0:
        print(f"\n📋 Log Analysis Summary:")
        print("-" * 25)
        
        for log_file in download_dir.glob("*"):
            print(f"\n📄 {log_file.name}:")
            
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                # Count different types of events
                if 'server.log' in log_file.name:
                    warnings = len([line for line in lines if 'WARNING' in line])
                    errors = len([line for line in lines if 'ERROR' in line])
                    yardstick_warnings = len([line for line in lines if 'YARDSTICK: High tick duration' in line])
                    
                    print(f"  ⚠️  Total warnings: {warnings:,}")
                    print(f"  ❌ Total errors: {errors:,}")
                    print(f"  🐌 High tick warnings: {yardstick_warnings:,}")
                    
                elif 'startup.log' in log_file.name:
                    joins = len([line for line in lines if 'joins game' in line])
                    leaves = len([line for line in lines if 'leaves game' in line])
                    actions = len([line for line in lines if 'ACTION[' in line])
                    
                    print(f"  🚪 Player joins: {joins:,}")
                    print(f"  🚪 Player leaves: {leaves:,}")
                    print(f"  🎮 Total actions: {actions:,}")
                
                # Show time range
                import re
                timestamp_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
                first_match = re.search(timestamp_pattern, content)
                
                last_lines = lines[-50:]  # Check last 50 lines for timestamp
                last_match = None
                for line in reversed(last_lines):
                    last_match = re.search(timestamp_pattern, line)
                    if last_match:
                        break
                
                if first_match and last_match:
                    print(f"  ⏰ Time range: {first_match.group(1)} to {last_match.group(1)}")
                
            except Exception as e:
                print(f"  ❌ Error analyzing {log_file.name}: {e}")
    
    return download_dir

# Download both log files
complete_logs_dir = download_complete_server_logs()
luanti_server.cleanup()
telegraf.cleanup()

# === BLOCKBOT vs WALKBOT COMPARISON (resource demand & dominant resource) ===

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

BASE_PATH = Path("/var/scratch/aco237/yardstick")
OUTPUT_DIR = (BASE_PATH / "analysis_outputs").resolve()
AGG_CSV = OUTPUT_DIR / "all_runs_aggregated.csv"

TPS_TARGET = 20.0
TICK_BUDGET_MS = 50.0

def list_dir_with_sizes(path: Path, header: str):
    print(f"\n📁 {header}: {path}")
    files = sorted(path.glob("*"))
    if not files:
        print("   (empty)")
        return
    for f in files:
        try:
            print(f"   {f.name}  —  {f.stat().st_size:,} bytes")
        except Exception:
            print(f"   {f.name}  —  (size unavailable)")

def xcol(df: pd.DataFrame):
    if "peak_concurrent" in df.columns and df["peak_concurrent"].fillna(0).max() > 0:
        return "peak_concurrent"
    if "unique_joins" in df.columns and df["unique_joins"].fillna(0).max() > 0:
        return "unique_joins"
    return "bot_count"

def choose_blockbot_major_pattern(block_df: pd.DataFrame) -> pd.DataFrame:
    if "build_pattern" not in block_df.columns or block_df.empty:
        return block_df
    counts = block_df["build_pattern"].value_counts()
    if counts.empty:
        return block_df
    major = counts.idxmax()
    print(f"ℹ Using dominant blockbot pattern for fairness: '{major}' "
          f"({int(counts.max())} runs of {int(counts.sum())})")
    return block_df[block_df["build_pattern"] == major].copy()

def overlap_by_load(a: pd.DataFrame, b: pd.DataFrame, load_col: str):
    if a.empty or b.empty or load_col not in a.columns or load_col not in b.columns:
        return a.copy(), b.copy(), None
    a2 = a.dropna(subset=[load_col]).copy()
    b2 = b.dropna(subset=[load_col]).copy()
    if a2.empty or b2.empty:
        return a2, b2, None
    lo = max(a2[load_col].min(), b2[load_col].min())
    hi = min(a2[load_col].max(), b2[load_col].max())
    if not np.isfinite(lo) or not np.isfinite(hi) or lo >= hi:
        return a2, b2, None
    return a2[(a2[load_col] >= lo) & (a2[load_col] <= hi)], \
           b2[(b2[load_col] >= lo) & (b2[load_col] <= hi)], \
           (int(lo), int(hi))

def bin_and_aggregate(df: pd.DataFrame, load_col: str, bin_width: int = 25):
    if df.empty:
        return pd.DataFrame()
    lo = int(np.floor(df[load_col].min()))
    hi = int(np.ceil(df[load_col].max()))
    if hi <= lo:
        return pd.DataFrame()
    # make at least a couple of bins
    bw = max(5, bin_width)
    bins = np.arange(lo, hi + bw, bw)
    df = df.copy()
    df["load_bin"] = pd.cut(df[load_col], bins=bins, include_lowest=True)
    grp = df.groupby("load_bin", observed=True)
    out = grp.agg(
        load_mid=(load_col, "mean"),
        n_runs=("avg_tps", "count"),
        avg_tps=("avg_tps", "mean"),
        avg_tick_ms=("avg_tick_duration_ms", "mean"),
        cpu_avg=("cpu_avg", "mean"),
        mem_avg=("mem_avg", "mean"),
        excellent_pct=("excellent_pct", "mean"),
    ).reset_index(drop=True)
    return out.dropna(subset=["load_mid"])

def fit_slope(df: pd.DataFrame, load_col: str, ycol: str):
    """Return slope per bot, intercept, r, n (ignoring NaN)."""
    sub = df.dropna(subset=[load_col, ycol]).copy()
    if len(sub) < 3:
        return np.nan, np.nan, np.nan, len(sub)
    x = sub[load_col].values
    y = sub[ycol].values
    # simple linear regression
    A = np.vstack([x, np.ones_like(x)]).T
    m, c = np.linalg.lstsq(A, y, rcond=None)[0]
    # r (Pearson)
    r = np.corrcoef(x, y)[0, 1] if len(sub) > 1 else np.nan
    return float(m), float(c), float(r), len(sub)

def compare_block_vs_walk():
    if not AGG_CSV.exists():
        raise FileNotFoundError(f"Aggregated CSV not found: {AGG_CSV}")
    df = pd.read_csv(AGG_CSV, parse_dates=["timestamp"], infer_datetime_format=True)
    print(f"Loaded aggregated: {AGG_CSV} ({AGG_CSV.stat().st_size:,} bytes)")
    print(f"Total runs: {len(df)}")

    # Split
    walk = df[df["bot_type"] == "walkbot"].copy()
    block = df[df["bot_type"] == "blockbot"].copy()

    if walk.empty or block.empty:
        print("❌ Need both walkbot and blockbot runs to compare.")
        return

    # Use major blockbot pattern (e.g., 'tower')
    block = choose_blockbot_major_pattern(block)

    load = xcol(df)
    print(f"Using load column: {load}")

    # Align by overlapping load range
    walk_ol, block_ol, overlap = overlap_by_load(walk, block, load)
    if overlap is None:
        print("⚠ No overlapping load range; comparing as-is.")
    else:
        print(f"Overlapping load range: {overlap[0]}..{overlap[1]} concurrent players")

    # --- Slope estimates (per extra concurrent bot) ---
    wm_cpu, wcpu_c, wcpu_r, wn_cpu = fit_slope(walk_ol, load, "cpu_avg")
    bm_cpu, bcpu_c, bcpu_r, bn_cpu = fit_slope(block_ol, load, "cpu_avg")
    wm_mem, wmem_c, wmem_r, wn_mem = fit_slope(walk_ol, load, "mem_avg")
    bm_mem, bmem_c, bmem_r, bn_mem = fit_slope(block_ol, load, "mem_avg")
    wm_tick, _, wr_tick, _ = fit_slope(walk_ol, load, "avg_tick_duration_ms")
    bm_tick, _, br_tick, _ = fit_slope(block_ol, load, "avg_tick_duration_ms")

    # --- Binned curves for visuals ---
    walk_binned = bin_and_aggregate(walk_ol, load)
    block_binned = bin_and_aggregate(block_ol, load)

    # --- Plot 1: TPS and Tick vs Load ---
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("Walkbot vs Blockbot — Performance vs Load", fontsize=16, fontweight="bold")

    ax = axes[0]
    if not walk_binned.empty:
        ax.plot(walk_binned["load_mid"], walk_binned["avg_tps"], marker="o", label="Walkbot TPS")
    if not block_binned.empty:
        ax.plot(block_binned["load_mid"], block_binned["avg_tps"], marker="o", label="Blockbot TPS")
    ax.axhline(TPS_TARGET, linestyle="--", alpha=0.7, label=f"Target {TPS_TARGET} TPS")
    ax.set_xlabel("Concurrent players (peak, binned)")
    ax.set_ylabel("Average TPS")
    ax.set_title("TPS vs Load (binned means)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    ax = axes[1]
    if not walk_binned.empty:
        ax.plot(walk_binned["load_mid"], walk_binned["avg_tick_ms"], marker="o", label="Walkbot Tick (ms)")
    if not block_binned.empty:
        ax.plot(block_binned["load_mid"], block_binned["avg_tick_ms"], marker="o", label="Blockbot Tick (ms)")
    ax.axhline(TICK_BUDGET_MS, linestyle="--", alpha=0.7, label=f"Budget {int(TICK_BUDGET_MS)} ms")
    ax.set_xlabel("Concurrent players (peak, binned)")
    ax.set_ylabel("Avg tick duration (ms)")
    ax.set_title("Tick duration vs Load (binned means)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    out1 = OUTPUT_DIR / "walk_vs_block__performance.png"
    fig.savefig(out1, dpi=150, bbox_inches="tight")
    print(f"Saved: {out1} ({out1.stat().st_size:,} bytes)")
    plt.show()
    plt.close(fig)

    # --- Plot 2: CPU and Memory vs Load ---
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("Walkbot vs Blockbot — Resource Usage vs Load", fontsize=16, fontweight="bold")

    ax = axes[0]
    if not walk_binned.empty and not walk_binned["cpu_avg"].isna().all():
        ax.plot(walk_binned["load_mid"], walk_binned["cpu_avg"], marker="o", label="Walkbot CPU%")
    if not block_binned.empty and not block_binned["cpu_avg"].isna().all():
        ax.plot(block_binned["load_mid"], block_binned["cpu_avg"], marker="o", label="Blockbot CPU%")
    ax.set_xlabel("Concurrent players (peak, binned)")
    ax.set_ylabel("CPU utilization (%)")
    ax.set_title("CPU vs Load")
    ax.grid(True, alpha=0.3)
    ax.legend()

    ax = axes[1]
    if not walk_binned.empty and not walk_binned["mem_avg"].isna().all():
        ax.plot(walk_binned["load_mid"], walk_binned["mem_avg"], marker="o", label="Walkbot Mem%")
    if not block_binned.empty and not block_binned["mem_avg"].isna().all():
        ax.plot(block_binned["load_mid"], block_binned["mem_avg"], marker="o", label="Blockbot Mem%")
    ax.set_xlabel("Concurrent players (peak, binned)")
    ax.set_ylabel("Memory utilization (%)")
    ax.set_title("Memory vs Load")
    ax.grid(True, alpha=0.3)
    ax.legend()

    out2 = OUTPUT_DIR / "walk_vs_block__resources.png"
    fig.savefig(out2, dpi=150, bbox_inches="tight")
    print(f"Saved: {out2} ({out2.stat().st_size:,} bytes)")
    plt.show()
    plt.close(fig)

    # --- Plot 3: Differences (Blockbot - Walkbot) per bin ---
    # Merge on nearest bin center for fair visual difference
    diff = None
    if not walk_binned.empty and not block_binned.empty:
        wb = walk_binned.copy()
        bb = block_binned.copy()
        # Align on closest load_mid by simple nearest join
        wb = wb.rename(columns={c: f"w_{c}" for c in wb.columns})
        bb = bb.rename(columns={c: f"b_{c}" for c in bb.columns})
        # cartesian merge then choose nearest pairs
        wb["key"] = 1
        bb["key"] = 1
        cart = wb.merge(bb, on="key").drop(columns=["key"])
        cart["delta_load"] = (cart["w_load_mid"] - cart["b_load_mid"]).abs()
        nearest_idx = cart.groupby("w_load_mid")["delta_load"].idxmin()
        aligned = cart.loc[nearest_idx].copy()
        aligned["d_cpu"] = aligned["b_cpu_avg"] - aligned["w_cpu_avg"]
        aligned["d_mem"] = aligned["b_mem_avg"] - aligned["w_mem_avg"]
        aligned["d_tick"] = aligned["b_avg_tick_ms"] - aligned["w_avg_tick_ms"]
        diff = aligned[["w_load_mid", "d_cpu", "d_mem", "d_tick"]].sort_values("w_load_mid")

        fig, ax = plt.subplots(1, 1, figsize=(10, 5))
        ax.plot(diff["w_load_mid"], diff["d_cpu"], marker="o", label="Δ CPU% (block - walk)")
        ax.plot(diff["w_load_mid"], diff["d_mem"], marker="o", label="Δ Mem% (block - walk)")
        ax.axhline(0, color="k", linewidth=1)
        ax.set_xlabel("Concurrent players (peak, binned by walkbot centers)")
        ax.set_ylabel("Difference (percentage points / ms)")
        ax.set_title("Resource and Tick differences (Blockbot minus Walkbot)")
        ax.grid(True, alpha=0.3)
        ax.legend()
        out3 = OUTPUT_DIR / "walk_vs_block__differences.png"
        fig.savefig(out3, dpi=150, bbox_inches="tight")
        print(f"Saved: {out3} ({out3.stat().st_size:,} bytes)")
        plt.show()
        plt.close(fig)

    # --- Textual Summary ---
    print("\n================= SUMMARY (Walkbot vs Blockbot) =================")
    print(f"Load column used: {load}")
    if overlap:
        print(f"Overlapping load range used for regression: {overlap[0]}..{overlap[1]} players")
    print("\nPer-bot slopes (percentage points per extra concurrent player):")
    print(f"  Walkbot: CPU {wm_cpu:.3f} pp/bot  | Mem {wm_mem:.3f} pp/bot  | Tick {wm_tick:.3f} ms/bot "
          f"(n_cpu={wn_cpu}, n_mem={wn_mem})")
    print(f"  Blockbot: CPU {bm_cpu:.3f} pp/bot | Mem {bm_mem:.3f} pp/bot | Tick {bm_tick:.3f} ms/bot "
          f"(n_cpu={bn_cpu}, n_mem={bn_mem})")

    # Dominant resource per type (compare slope magnitudes)
    walk_dom = "CPU" if abs(wm_cpu) >= abs(wm_mem) else "Memory"
    block_dom = "CPU" if abs(bm_cpu) >= abs(bm_mem) else "Memory"
    print("\nDominant resource pressure (by slope magnitude):")
    print(f"  Walkbot: {walk_dom}")
    print(f"  Blockbot: {block_dom}")

    # Representative median-load comparison
    def median_row(d: pd.DataFrame):
        d2 = d.dropna(subset=[load]).sort_values(load)
        if d2.empty:
            return None
        return d2.iloc[len(d2)//2]

    walk_med = median_row(walk_ol)
    block_med = median_row(block_ol)
    if walk_med is not None and block_med is not None:
        print("\nRepresentative median-run comparison (overlap region):")
        print(f"  Walkbot @ ~{int(walk_med[load])} players: "
              f"TPS {walk_med['avg_tps']:.2f}, Tick {walk_med['avg_tick_duration_ms']:.1f} ms, "
              f"CPU {walk_med['cpu_avg'] if pd.notna(walk_med['cpu_avg']) else float('nan'):.1f}%, "
              f"Mem {walk_med['mem_avg'] if pd.notna(walk_med['mem_avg']) else float('nan'):.1f}%")
        print(f"  Blockbot @ ~{int(block_med[load])} players: "
              f"TPS {block_med['avg_tps']:.2f}, Tick {block_med['avg_tick_duration_ms']:.1f} ms, "
              f"CPU {block_med['cpu_avg'] if pd.notna(block_med['cpu_avg']) else float('nan'):.1f}%, "
              f"Mem {block_med['mem_avg'] if pd.notna(block_med['mem_avg']) else float('nan'):.1f}%")

    # Save a one-line CSV summary for the thesis
    summary = pd.DataFrame([{
        "load_col": load,
        "overlap_lo": overlap[0] if overlap else np.nan,
        "overlap_hi": overlap[1] if overlap else np.nan,
        "walk_slope_cpu_pct_per_bot": wm_cpu,
        "walk_slope_mem_pct_per_bot": wm_mem,
        "walk_slope_tick_ms_per_bot": wm_tick,
        "block_slope_cpu_pct_per_bot": bm_cpu,
        "block_slope_mem_pct_per_bot": bm_mem,
        "block_slope_tick_ms_per_bot": bm_tick,
        "walk_dominant_resource": walk_dom,
        "block_dominant_resource": block_dom
    }])
    out_csv = OUTPUT_DIR / "walk_vs_block__summary.csv"
    summary.to_csv(out_csv, index=False)
    print(f"\nSaved summary CSV: {out_csv} ({out_csv.stat().st_size:,} bytes)")

    list_dir_with_sizes(OUTPUT_DIR, "Analysis outputs (updated)")

    # --- Additional Plot: Actual Max Concurrent vs Configured Bot Count ---
    print("\n--- Plotting actual max concurrent players vs configured bot count ---")
    
    # Check which columns are available for bot count and max concurrent
    bot_col = "bot_count" if "bot_count" in df.columns else None
    concurrent_col = "peak_concurrent" if "peak_concurrent" in df.columns else None
    
    if bot_col and concurrent_col:
        # Plot for both walkbot and blockbot
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        
        # Walkbot data
        if not walk.empty:
            ax.scatter(walk[bot_col], walk[concurrent_col], alpha=0.7, 
                      label="Walkbot", marker="o", s=50)
        
        # Blockbot data  
        if not block.empty:
            ax.scatter(block[bot_col], block[concurrent_col], alpha=0.7, 
                      label="Blockbot", marker="^", s=50)
        
        # Add diagonal line for reference (perfect efficiency: concurrent = configured)
        if not df.empty:
            max_bots = df[bot_col].max()
            ax.plot([0, max_bots], [0, max_bots], 'k--', alpha=0.5, 
                   label="Perfect efficiency (1:1)")
        
        ax.set_xlabel("Configured bot count")
        ax.set_ylabel("Actual max concurrent players")
        ax.set_title("Bot Configuration vs Actual Concurrency")
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Save the plot
        out_concurrent = OUTPUT_DIR / "bot_config_vs_actual_concurrent.png"
        fig.savefig(out_concurrent, dpi=150, bbox_inches="tight")
        print(f"Saved concurrent plot: {out_concurrent}")
        plt.show()
        plt.close(fig)
        
    else:
        print(f"❌ Cannot plot: missing columns bot_col={bot_col}, concurrent_col={concurrent_col}")
        print(f"Available columns: {list(df.columns)}")

# Run
compare_block_vs_walk()

if __name__ == "__main__":
    pass