#!/usr/bin/env python3
"""
Local Minecraft (PaperMC) Benchmark Script for macOS

This script runs a Minecraft server benchmark locally on macOS, including:
- PaperMC server deployment and management
- Telegraf metrics collection
- Node.js-based bot workload
- Local metrics collection and analysis
"""

import argparse
import json
import logging
import os
import shutil
import signal
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

class LocalMinecraftBenchmark:
    """Local Minecraft benchmark orchestrator."""
    
    def __init__(self, args):
        self.args = args
        self.pm = ProcessManager()
        self.base_dir = Path(args.output_dir)
        self.benchmark_dir = self.setup_benchmark_directory()
        
        # Process references
        self.papermc_process = None
        self.telegraf_process = None
        self.bot_processes = []
        
    def setup_benchmark_directory(self) -> Path:
        """Set up the benchmark output directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        benchmark_dir = self.base_dir / f"minecraft_benchmark_{timestamp}"
        benchmark_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Benchmark directory: {benchmark_dir}")
        return benchmark_dir
    
    def check_dependencies(self):
        """Check if required dependencies are available."""
        dependencies = {
            'java': ['java', '-version'],
            'node': ['node', '--version'],
            'npm': ['npm', '--version']
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
                if dep == 'java':
                    logger.error("  - Java 17+: brew install openjdk@17")
                elif dep == 'node':
                    logger.error("  - Node.js: brew install node")
                elif dep == 'npm':
                    logger.error("  - npm (comes with Node.js)")
            sys.exit(1)
    
    def download_papermc(self) -> Path:
        """Download PaperMC server if not already present."""
        papermc_jar = self.benchmark_dir / "paper-1.20.1-58.jar"
        
        if papermc_jar.exists():
            logger.info("PaperMC already downloaded")
            return papermc_jar
        
        logger.info("Downloading PaperMC...")
        url = "https://api.papermc.io/v2/projects/paper/versions/1.20.1/builds/58/downloads/paper-1.20.1-58.jar"
        
        try:
            import urllib.request
            urllib.request.urlretrieve(url, papermc_jar)
            logger.info(f"Downloaded PaperMC to {papermc_jar}")
        except Exception as e:
            logger.error(f"Failed to download PaperMC: {e}")
            sys.exit(1)
        
        return papermc_jar
    
    def download_jolokia(self) -> Path:
        """Download Jolokia JVM agent for metrics."""
        jolokia_jar = self.benchmark_dir / "jolokia-agent-jvm-2.0.3-javaagent.jar"
        
        if jolokia_jar.exists():
            logger.info("Jolokia already downloaded")
            return jolokia_jar
        
        logger.info("Downloading Jolokia JVM agent...")
        url = "https://search.maven.org/remotecontent?filepath=org/jolokia/jolokia-agent-jvm/2.0.3/jolokia-agent-jvm-2.0.3-javaagent.jar"
        
        try:
            import urllib.request
            urllib.request.urlretrieve(url, jolokia_jar)
            logger.info(f"Downloaded Jolokia to {jolokia_jar}")
        except Exception as e:
            logger.error(f"Failed to download Jolokia: {e}")
            sys.exit(1)
        
        return jolokia_jar
    
    def setup_server_config(self):
        """Create server configuration files."""
        # EULA
        eula_path = self.benchmark_dir / "eula.txt"
        with open(eula_path, 'w') as f:
            f.write("eula=true\n")
        
        # Server properties
        server_props = self.benchmark_dir / "server.properties"
        with open(server_props, 'w') as f:
            f.write(f"""# Minecraft server properties for local benchmark
enable-jmx-monitoring=true
server-port={self.args.port}
gamemode=creative
enable-command-block=false
enable-query=false
difficulty=peaceful
network-compression-threshold=256
max-tick-time=60000
max-players=100
online-mode=false
enable-status=true
allow-flight=true
view-distance=10
server-ip=127.0.0.1
allow-nether=true
enable-rcon=true
sync-chunk-writes=true
op-permission-level=4
prevent-proxy-connections=false
resource-pack=
entity-broadcast-range-percentage=100
simulation-distance=10
rcon.password=password
rcon.port=25575
player-idle-timeout=0
force-gamemode=false
rate-limit=0
hardcore=false
white-list=false
broadcast-console-to-ops=true
spawn-npcs=true
spawn-animals=true
function-permission-level=2
level-type=minecraft:flat
spawn-monsters=false
enforce-whitelist=false
spawn-protection=0
max-world-size=29999984
""")
    
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
# Telegraf Configuration for Local Minecraft Benchmark

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

# Minecraft JMX metrics via Jolokia
[[inputs.jolokia2_agent]]
  urls = ["http://localhost:8778/jolokia"]
  
  [[inputs.jolokia2_agent.metric]]
    name = "jvm_memory"
    mbean = "java.lang:type=Memory"
    paths = ["HeapMemoryUsage", "NonHeapMemoryUsage"]
  
  [[inputs.jolokia2_agent.metric]]
    name = "jvm_garbage_collector"
    mbean = "java.lang:name=*,type=GarbageCollector"
    paths = ["CollectionTime", "CollectionCount"]
    tag_keys = ["name"]
  
  [[inputs.jolokia2_agent.metric]]
    name = "minecraft_tick_times"
    mbean = "net.minecraft.server:type=Server"
    paths = ["averageTickTime", "tickTimes"]
"""
        
        with open(config_path, 'w') as f:
            f.write(config)
        
        return config_path
    
    def start_papermc_server(self, papermc_jar: Path, jolokia_jar: Path):
        """Start the PaperMC server with Jolokia agent."""
        logger.info("Starting PaperMC server...")
        
        cmd = [
            'java',
            f'-javaagent:{jolokia_jar.absolute()}',
            '-Xmx2G',
            '-Xms1G',
            '-jar', str(papermc_jar.absolute()),
            '--nogui'
        ]
        
        # Start server without capturing output so we can see logs in real-time
        self.papermc_process = self.pm.start_process(
            cmd, 
            cwd=self.benchmark_dir,
            name="PaperMC Server",
            capture_output=False
        )
        
        # Wait for server to start - check multiple times
        logger.info("Waiting for server to start...")
        max_wait_time = 30  # 30 seconds max wait
        check_interval = 2  # Check every 2 seconds
        
        for i in range(max_wait_time // check_interval):
            time.sleep(check_interval)
            
            # Check if process died
            if self.papermc_process.poll() is not None:
                logger.error("PaperMC server process exited unexpectedly")
                # Try to read any error output
                try:
                    stdout, stderr = self.papermc_process.communicate()
                    if stderr:
                        logger.error(f"Server stderr: {stderr}")
                    if stdout:
                        logger.info(f"Server stdout: {stdout}")
                except:
                    pass
                sys.exit(1)
            
            # Check if server is ready by looking for log files or testing connection
            logs_dir = self.benchmark_dir / "logs"
            if logs_dir.exists():
                latest_log = logs_dir / "latest.log"
                if latest_log.exists():
                    try:
                        with open(latest_log, 'r') as f:
                            log_content = f.read()
                            if "Done (" in log_content and "For help, type" in log_content:
                                logger.info("Server startup completed successfully")
                                return
                    except:
                        pass
            
            # Try to connect to server port to check if it's ready
            import socket
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', self.args.port))
                sock.close()
                if result == 0:
                    logger.info("Server is accepting connections")
                    return
            except:
                pass
            
            logger.info(f"Waiting for server... ({(i+1)*check_interval}s elapsed)")
        
        # Final check
        if self.papermc_process.poll() is None:
            logger.info("Server appears to be running (final check passed)")
        else:
            logger.error("PaperMC server failed to start within timeout period")
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
    
    def setup_bot_environment(self) -> Path:
        """Set up Node.js environment for bots."""
        bot_dir = self.benchmark_dir / "bots"
        bot_dir.mkdir(exist_ok=True)
        
        # Copy bot scripts from yardstick
        scripts_dir = Path("yardstick_benchmark/games/minecraft/workload")
        if scripts_dir.exists():
            for script in ["walkaround_bot.js", "walkaround_worker_bot.js"]:
                src = scripts_dir / script
                if src.exists():
                    shutil.copy2(src, bot_dir / script)
        
        # Create package.json
        package_json = {
            "name": "minecraft-bots",
            "version": "1.0.0",
            "dependencies": {
                "mineflayer": "^4.17.0",
                "mineflayer-pathfinder": "^2.4.0",
                "vec3": "^0.1.8"
            }
        }
        
        with open(bot_dir / "package.json", 'w') as f:
            json.dump(package_json, f, indent=2)
        
        # Install dependencies
        logger.info("Installing bot dependencies...")
        subprocess.run(['npm', 'install'], cwd=bot_dir, check=True)
        
        return bot_dir
    
    def start_bots(self, bot_dir: Path):
        """Start the bot workload."""
        logger.info(f"Starting {self.args.bots} bots...")
        
        # Create a simple bot script
        bot_script = bot_dir / "simple_bot.js"
        with open(bot_script, 'w') as f:
            f.write(f"""
const mineflayer = require('mineflayer');

const botCount = {self.args.bots};
const duration = {self.args.duration} * 1000; // Convert to milliseconds

for (let i = 0; i < botCount; i++) {{
    setTimeout(() => {{
        const bot = mineflayer.createBot({{
            host: 'localhost',
            port: {self.args.port},
            username: `bot_${{i}}`,
            version: false
        }});

        bot.on('spawn', () => {{
            console.log(`Bot ${{i}} spawned`);
            
            // Simple movement
            setInterval(() => {{
                if (bot.entity && bot.entity.position) {{
                    const x = bot.entity.position.x + (Math.random() - 0.5) * 10;
                    const z = bot.entity.position.z + (Math.random() - 0.5) * 10;
                    bot.setControlState('forward', true);
                    setTimeout(() => bot.setControlState('forward', false), 1000);
                }}
            }}, 3000);
        }});

        bot.on('error', (err) => console.log(`Bot ${{i}} error:`, err.message));
        
        // Disconnect after duration
        setTimeout(() => {{
            bot.quit();
        }}, duration);
    }}, i * 1000); // Stagger bot connections
}}
""")
        
        # Start bots
        cmd = ['node', str(bot_script)]
        bot_process = self.pm.start_process(cmd, cwd=bot_dir, name="Minecraft Bots")
        self.bot_processes.append(bot_process)
    
    def run_benchmark(self):
        """Run the complete benchmark."""
        logger.info("="*60)
        logger.info("LOCAL MINECRAFT BENCHMARK")
        logger.info("="*60)
        logger.info(f"Duration: {self.args.duration}s")
        logger.info(f"Bots: {self.args.bots}")
        logger.info(f"Port: {self.args.port}")
        logger.info(f"Output: {self.benchmark_dir}")
        logger.info("="*60)
        
        try:
            # Check dependencies
            self.check_dependencies()
            
            # Download and setup
            papermc_jar = self.download_papermc()
            jolokia_jar = self.download_jolokia()
            self.setup_server_config()
            
            # Setup monitoring
            telegraf_bin = self.install_telegraf()
            telegraf_config = self.create_telegraf_config(telegraf_bin)
            
            # Start server
            self.start_papermc_server(papermc_jar, jolokia_jar)
            
            # Start monitoring
            self.start_telegraf(telegraf_bin, telegraf_config)
            
            # Setup and start bots
            bot_dir = self.setup_bot_environment()
            self.start_bots(bot_dir)
            
            # Run benchmark
            logger.info(f"Running benchmark for {self.args.duration} seconds...")
            time.sleep(self.args.duration)
            
            logger.info("="*60)
            logger.info("BENCHMARK COMPLETED")
            logger.info(f"Results saved to: {self.benchmark_dir}")
            logger.info("Metrics file: metrics.json")
            logger.info("Server logs: logs/latest.log")
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
        description="Run local Minecraft benchmark on macOS",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument("--duration", type=int, default=120,
                       help="Benchmark duration in seconds")
    parser.add_argument("--bots", type=int, default=5,
                       help="Number of bots to spawn")
    parser.add_argument("--port", type=int, default=25565,
                       help="Minecraft server port")
    parser.add_argument("--output-dir", default="./local_benchmark_results",
                       help="Output directory for benchmark results")
    
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
    benchmark = LocalMinecraftBenchmark(args)
    benchmark.run_benchmark()

if __name__ == "__main__":
    main() 