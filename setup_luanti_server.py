#!/usr/bin/env python3
"""
Luanti Headless Server Setup and Test Script

This script downloads, sets up, and tests a headless Luanti server on DAS5.
Uses the pre-built binaries from rollerozxa/luantiserver for easy setup.
"""

import logging
import os
import subprocess
import sys
import time
import urllib.request
import tarfile
import tempfile
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class LuantiServerSetup:
    """Setup and manage a Luanti headless server."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            self.base_dir = Path.cwd() / "luanti_server"
        else:
            self.base_dir = Path(base_dir)
        
        self.server_binary = self.base_dir / "luanti" / "bin" / "luantiserver"
        self.worlds_dir = self.base_dir / "luanti" / "worlds"
        self.games_dir = self.base_dir / "luanti" / "games"
        self.server_process = None
        
    def check_dependencies(self):
        """Check if required system dependencies are available."""
        logger.info("Checking system dependencies...")
        
        required_packages = [
            "libcurl4",
            "libncurses6",
            "libsqlite3-0",
            "libzstd1",
            "zlib1g"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                # Check if package is installed using dpkg
                result = subprocess.run(
                    ["dpkg", "-l", package],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode != 0:
                    missing_packages.append(package)
                else:
                    logger.info(f"✓ {package} is installed")
            except FileNotFoundError:
                logger.warning("dpkg not found, skipping dependency check")
                break
        
        if missing_packages:
            logger.warning(f"Missing packages: {', '.join(missing_packages)}")
            logger.info("These should be available on most Linux systems")
        else:
            logger.info("✓ All required dependencies appear to be available")
    
    def download_server(self, version: str = "5.11.0"):
        """Download the Luanti server binary."""
        logger.info(f"Downloading Luanti server version {version}...")
        
        url = f"https://github.com/rollerozxa/luantiserver/releases/download/{version}/luantiserver-{version}.tar.gz"
        
        # Create temporary file for download
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
        
        try:
            logger.info(f"Downloading from: {url}")
            urllib.request.urlretrieve(url, tmp_path)
            logger.info(f"✓ Downloaded to {tmp_path}")
            
            # Extract the archive
            self.extract_server(tmp_path)
            
        except Exception as e:
            logger.error(f"✗ Failed to download server: {e}")
            raise
        finally:
            # Clean up temporary file
            if tmp_path.exists():
                tmp_path.unlink()
    
    def extract_server(self, archive_path: Path):
        """Extract the server archive."""
        logger.info("Extracting server archive...")
        
        # Remove existing server directory if it exists
        if self.base_dir.exists():
            logger.info(f"Removing existing directory: {self.base_dir}")
            import shutil
            shutil.rmtree(self.base_dir)
        
        # Create base directory
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with tarfile.open(archive_path, 'r:gz') as tar:
                # Extract all files to base directory
                tar.extractall(self.base_dir)
                logger.info(f"✓ Extracted server to {self.base_dir}")
            
            # Make server binary executable
            if self.server_binary.exists():
                self.server_binary.chmod(0o755)
                logger.info("✓ Made server binary executable")
            else:
                logger.error(f"✗ Server binary not found at {self.server_binary}")
                raise FileNotFoundError(f"Server binary not found at {self.server_binary}")
                
        except Exception as e:
            logger.error(f"✗ Failed to extract server: {e}")
            raise
    
    def setup_default_game(self):
        """Set up a default game for the server."""
        logger.info("Setting up default game...")
        
        # Create games directory
        self.games_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if minetest_game already exists
        minetest_game_dir = self.games_dir / "minetest_game"
        if minetest_game_dir.exists():
            logger.info("✓ minetest_game already exists")
            return
        
        # Download minetest_game
        game_url = "https://github.com/minetest/minetest_game/archive/refs/heads/master.zip"
        
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
        
        try:
            logger.info(f"Downloading minetest_game from: {game_url}")
            urllib.request.urlretrieve(game_url, tmp_path)
            
            # Extract the game
            import zipfile
            with zipfile.ZipFile(tmp_path, 'r') as zip_file:
                zip_file.extractall(self.games_dir)
            
            # Rename the extracted directory
            extracted_dir = self.games_dir / "minetest_game-master"
            if extracted_dir.exists():
                extracted_dir.rename(minetest_game_dir)
                logger.info("✓ minetest_game set up successfully")
            else:
                logger.error("✗ Failed to find extracted minetest_game directory")
                
        except Exception as e:
            logger.error(f"✗ Failed to setup default game: {e}")
            raise
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
    
    def create_world(self, world_name: str = "testworld"):
        """Create a test world."""
        logger.info(f"Creating world: {world_name}")
        
        # Create worlds directory
        self.worlds_dir.mkdir(parents=True, exist_ok=True)
        
        world_dir = self.worlds_dir / world_name
        world_dir.mkdir(exist_ok=True)
        
        # Create world.mt file
        world_mt = world_dir / "world.mt"
        world_config = f"""gameid = minetest_game
world_name = {world_name}
backend = sqlite3
player_backend = sqlite3
auth_backend = sqlite3
mod_storage_backend = sqlite3
"""
        
        world_mt.write_text(world_config)
        logger.info(f"✓ Created world at {world_dir}")
    
    def create_server_config(self):
        """Create a basic server configuration."""
        logger.info("Creating server configuration...")
        
        config_path = self.base_dir / "luanti" / "minetest.conf"
        
        config_content = """# Basic Luanti server configuration
# Server settings
server_name = DAS5 Test Server
server_description = Test server running on DAS5
port = 30000
bind_address = 0.0.0.0

# World settings
default_game = minetest_game
world_name = testworld

# Security settings
default_privs = interact,shout
enable_damage = false
creative_mode = true

# Performance settings
max_users = 20
dedicated_server_step = 0.1

# Logging
debug_log_level = action
"""
        
        config_path.write_text(config_content)
        logger.info(f"✓ Created server config at {config_path}")
    
    def test_server_binary(self):
        """Test if the server binary works."""
        logger.info("Testing server binary...")
        
        try:
            # Run server with --version flag
            result = subprocess.run(
                [str(self.server_binary), "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.base_dir / "luanti"
            )
            
            if result.returncode == 0:
                logger.info(f"✓ Server binary works: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"✗ Server binary failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("✗ Server binary test timed out")
            return False
        except Exception as e:
            logger.error(f"✗ Failed to test server binary: {e}")
            return False
    
    def start_server(self, timeout: int = 30):
        """Start the server for testing."""
        logger.info("Starting Luanti server...")
        
        cmd = [
            str(self.server_binary),
            "--config", "minetest.conf",
            "--world", "testworld",
            "--gameid", "minetest_game",
            "--logfile", "server.log"
        ]
        
        try:
            # Start server process
            self.server_process = subprocess.Popen(
                cmd,
                cwd=self.base_dir / "luanti",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            logger.info(f"✓ Server started with PID {self.server_process.pid}")
            
            # Wait a bit and check if server is still running
            time.sleep(5)
            
            if self.server_process.poll() is None:
                logger.info("✓ Server appears to be running successfully")
                return True
            else:
                stdout, stderr = self.server_process.communicate()
                logger.error(f"✗ Server exited early:")
                logger.error(f"stdout: {stdout}")
                logger.error(f"stderr: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the server."""
        if self.server_process and self.server_process.poll() is None:
            logger.info("Stopping server...")
            self.server_process.terminate()
            
            # Wait for graceful shutdown
            try:
                self.server_process.wait(timeout=10)
                logger.info("✓ Server stopped gracefully")
            except subprocess.TimeoutExpired:
                logger.warning("Server didn't stop gracefully, killing...")
                self.server_process.kill()
                self.server_process.wait()
                logger.info("✓ Server killed")
    
    def check_server_logs(self):
        """Check server logs for any issues."""
        log_file = self.base_dir / "luanti" / "server.log"
        
        if log_file.exists():
            logger.info("Server log contents:")
            print("=" * 60)
            print(log_file.read_text())
            print("=" * 60)
        else:
            logger.warning("No server log file found")
    
    def setup_and_test(self):
        """Complete setup and test process."""
        logger.info("="*60)
        logger.info("LUANTI HEADLESS SERVER SETUP AND TEST")
        logger.info("="*60)
        
        try:
            # Step 1: Check dependencies
            self.check_dependencies()
            
            # Step 2: Download server
            self.download_server()
            
            # Step 3: Test binary
            if not self.test_server_binary():
                raise RuntimeError("Server binary test failed")
            
            # Step 4: Setup game
            self.setup_default_game()
            
            # Step 5: Create world
            self.create_world()
            
            # Step 6: Create config
            self.create_server_config()
            
            # Step 7: Start server
            if self.start_server():
                logger.info("✓ Server test successful!")
                
                # Let it run for a bit
                logger.info("Letting server run for 10 seconds...")
                time.sleep(10)
                
                # Check logs
                self.check_server_logs()
                
            else:
                raise RuntimeError("Failed to start server")
            
            logger.info("="*60)
            logger.info("SETUP COMPLETED SUCCESSFULLY")
            logger.info("="*60)
            logger.info(f"Server installed at: {self.base_dir}")
            logger.info(f"Binary: {self.server_binary}")
            logger.info("You can now use this server setup with the yardstick benchmark")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise
        finally:
            self.stop_server()

def main():
    """Main function."""
    # Setup server in a subdirectory
    server_dir = Path.cwd() / "luanti_server_test"
    
    try:
        setup = LuantiServerSetup(server_dir)
        setup.setup_and_test()
    except KeyboardInterrupt:
        logger.info("Setup interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
