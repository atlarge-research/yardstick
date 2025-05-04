#!/usr/bin/env python3
"""
Luanti (Minetest) WalkAround workload for Yardstick benchmarking
"""
import os
import sys
import time
import random
import logging
import threading
from datetime import datetime
from luanti_bot import LuantiClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('LuantiWalkAround')

# Get parameters from environment variables
LUANTI_HOST = os.environ.get('LUANTI_HOST', 'localhost')
LUANTI_PORT = int(os.environ.get('LUANTI_PORT', '30000'))
DURATION = int(os.environ.get('DURATION', '60'))
SPAWN_X = float(os.environ.get('SPAWN_X', '0'))
SPAWN_Y = float(os.environ.get('SPAWN_Y', '0'))
SPAWN_Z = float(os.environ.get('SPAWN_Z', '0'))
BOX_WIDTH = int(os.environ.get('BOX_WIDTH', '32'))
BOX_X = int(os.environ.get('BOX_X', '-16'))
BOX_Z = int(os.environ.get('BOX_Z', '-16'))
BOTS_JOIN_DELAY = float(os.environ.get('BOTS_JOIN_DELAY', '5'))
BOTS_PER_NODE = int(os.environ.get('BOTS_PER_NODE', '1'))
BOT_INDEX = int(os.environ.get('BOT_INDEX', '0'))  # Index of this node

class WalkAroundBot:
    """Bot that walks around randomly in a defined area"""
    
    def __init__(self, username, host, port, box_x, box_z, box_width):
        self.username = username
        self.client = LuantiClient(username, host, port)
        self.running = False
        self.thread = None
        self.box_x = box_x
        self.box_z = box_z
        self.box_width = box_width
        # Initial position
        self.x = random.uniform(box_x, box_x + box_width)
        self.y = SPAWN_Y  # Start at ground level
        self.z = random.uniform(box_z, box_z + box_width)
        
    def start(self):
        """Start the bot's walking behavior"""
        if self.client.connect():
            logger.info(f"Bot {self.username} connected successfully")
            time.sleep(1)  # Wait a moment before starting to move
            
            # Move to initial position
            self.client.move(self.x, self.y, self.z)
            
            # Start walking thread
            self.running = True
            self.thread = threading.Thread(target=self._walk_loop)
            self.thread.daemon = True
            self.thread.start()
            return True
        else:
            logger.error(f"Bot {self.username} failed to connect")
            return False
            
    def _walk_loop(self):
        """Main loop for random walking behavior"""
        move_interval = 0.5  # Move every half second
        last_move = 0
        
        while self.running:
            now = time.time()
            if now - last_move >= move_interval:
                # Generate new target within the box
                target_x = random.uniform(self.box_x, self.box_x + self.box_width)
                target_z = random.uniform(self.box_z, self.box_z + self.box_width)
                
                # Move in small steps toward target
                step_size = 1.0
                dx = target_x - self.x
                dz = target_z - self.z
                
                # Normalize vector and apply step size
                distance = (dx**2 + dz**2)**0.5
                if distance > 0:
                    dx = dx / distance * min(step_size, distance)
                    dz = dz / distance * min(step_size, distance)
                
                self.x += dx
                self.z += dz
                
                # Send movement to server
                self.client.move(self.x, self.y, self.z)
                last_move = now
            
            # Small sleep to avoid CPU hogging
            time.sleep(0.05)
    
    def stop(self):
        """Stop the bot"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        self.client.disconnect()
        logger.info(f"Bot {self.username} stopped")


def main():
    """Start a group of WalkAround bots"""
    bots = []
    start_time = datetime.now()
    end_time = start_time.timestamp() + DURATION
    
    try:
        # Create and start bots
        logger.info(f"Starting {BOTS_PER_NODE} bots on node {BOT_INDEX}")
        for i in range(BOTS_PER_NODE):
            bot_id = (BOT_INDEX * BOTS_PER_NODE) + i
            bot_name = f"YardstickBot{bot_id}"
            
            bot = WalkAroundBot(
                bot_name, 
                LUANTI_HOST, 
                LUANTI_PORT,
                BOX_X, 
                BOX_Z, 
                BOX_WIDTH
            )
            
            if bot.start():
                bots.append(bot)
                logger.info(f"Started bot {bot_name}")
            else:
                logger.error(f"Failed to start bot {bot_name}")
            
            # Delay between bot starts to avoid overwhelming the server
            time.sleep(BOTS_JOIN_DELAY / BOTS_PER_NODE)
        
        # Run until duration expires
        logger.info(f"All bots started, running for {DURATION} seconds")
        while time.time() < end_time:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Interrupted, shutting down bots")
    finally:
        # Stop all bots
        for bot in bots:
            bot.stop()
        
        logger.info("All bots stopped")


if __name__ == "__main__":
    main() 