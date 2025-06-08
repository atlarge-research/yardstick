#!/usr/bin/env python3
"""
Luanti bot client for Yardstick benchmarking
This script connects multiple bots to a Luanti server and makes them walk around
"""

import socket
import struct
import random
import time
import logging
import os
import threading
import math
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('luanti_bot')

# Environment variables
LUANTI_HOST = os.environ.get('LUANTI_HOST', 'localhost')
LUANTI_PORT = int(os.environ.get('LUANTI_PORT', '30000'))
BOT_COUNT = int(os.environ.get('BOTS_PER_NODE', '1'))
DURATION = int(os.environ.get('DURATION', '60'))
BOT_JOIN_DELAY = float(os.environ.get('BOTS_JOIN_DELAY', '5'))
BOT_INDEX = int(os.environ.get('BOT_INDEX', '0'))
BOX_X = int(os.environ.get('BOX_X', '-16'))
BOX_Z = int(os.environ.get('BOX_Z', '-16'))
BOX_WIDTH = int(os.environ.get('BOX_WIDTH', '32'))

# Luanti protocol constants
PROTOCOL_ID = 0x4f457403
PROTOCOL_VERSION = 39
SER_FMT_VER_HIGHEST_READ = 29

# Packet types
TOSERVER_INIT = 0x10
TOSERVER_INIT2 = 0x11
TOSERVER_PLAYERPOS = 0x23
TOSERVER_CHAT = 0x32
TOSERVER_BREATH = 0x39
TOSERVER_INTERACT = 0x37
TOSERVER_KEEPALIVE = 0x3f
TOCLIENT_KEEPALIVE = 0x3f

class LuantiBot:
    def __init__(self, host, port, username):
        self.host = host
        self.port = port
        self.username = username
        self.sock = None
        self.connected = False
        self.running = False
        self.pos_x = random.uniform(BOX_X, BOX_X + BOX_WIDTH)
        self.pos_y = 80
        self.pos_z = random.uniform(BOX_Z, BOX_Z + BOX_WIDTH)
        self.last_keepalive = time.time()
        self.peer_id = 0

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(5)
            logger.info(f"Bot {self.username} connecting to {self.host}:{self.port}")
            self.sock.connect((self.host, self.port))
            
            # Send init packet
            self.send_init()
            
            # Wait for server response
            data = self.sock.recv(1024)
            if data:
                self.connected = True
                logger.info(f"Bot {self.username} connected successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    def send_init(self):
        # Prepare init packet
        packet = struct.pack(
            "!IBHB",
            PROTOCOL_ID,
            TOSERVER_INIT,
            SER_FMT_VER_HIGHEST_READ,
            len(self.username)
        )
        packet += self.username.encode('utf-8')
        packet += struct.pack("!H", PROTOCOL_VERSION)
        
        self.sock.send(packet)
        
        # Send init2 packet
        init2_packet = struct.pack("!IB", PROTOCOL_ID, TOSERVER_INIT2)
        self.sock.send(init2_packet)

    def send_position(self):
        packet = struct.pack(
            "!IBddd",
            PROTOCOL_ID,
            TOSERVER_PLAYERPOS,
            self.pos_x,
            self.pos_y,
            self.pos_z
        )
        self.sock.send(packet)

    def send_chat(self, message):
        msg_bytes = message.encode('utf-8')
        packet = struct.pack(
            "!IBB",
            PROTOCOL_ID,
            TOSERVER_CHAT,
            len(msg_bytes)
        )
        packet += msg_bytes
        self.sock.send(packet)

    def send_keepalive(self):
        packet = struct.pack("!IB", PROTOCOL_ID, TOSERVER_KEEPALIVE)
        self.sock.send(packet)

    def update_position(self):
        # Random walk algorithm
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(0.1, 0.5)
        
        self.pos_x += distance * math.cos(angle)
        self.pos_z += distance * math.sin(angle)
        
        # Keep within boundaries
        self.pos_x = max(BOX_X, min(BOX_X + BOX_WIDTH, self.pos_x))
        self.pos_z = max(BOX_Z, min(BOX_Z + BOX_WIDTH, self.pos_z))
        
        # Check for ground level
        self.pos_y = 80  # Fixed height for now

    def run(self):
        self.running = True
        
        # Initial position
        self.send_position()
        
        # Send initial chat message
        self.send_chat(f"Hello, I'm bot {self.username}")
        
        try:
            while self.running:
                # Try to receive any packets
                try:
                    data = self.sock.recv(1024)
                    if data:
                        # Simple packet handling logic
                        if len(data) >= 5:
                            packet_type = data[4]
                            if packet_type == TOCLIENT_KEEPALIVE:
                                self.last_keepalive = time.time()
                except socket.timeout:
                    pass
                
                # Update and send position
                self.update_position()
                self.send_position()
                
                # Send keepalive every 10 seconds
                if time.time() - self.last_keepalive > 10:
                    self.send_keepalive()
                    self.last_keepalive = time.time()
                
                # Random chat messages
                if random.random() < 0.01:  # 1% chance per update
                    messages = [
                        "This is a benchmarking test",
                        "Walking around",
                        "Testing server performance",
                        f"Bot {self.username} is active",
                        "How's the performance?"
                    ]
                    self.send_chat(random.choice(messages))
                
                time.sleep(0.2)  # Update at 5Hz
        except Exception as e:
            logger.error(f"Error in bot run loop: {e}")
        finally:
            self.disconnect()

    def disconnect(self):
        self.running = False
        if self.sock:
            self.sock.close()
        logger.info(f"Bot {self.username} disconnected")


def start_bot(bot_id):
    username = f"YardBot{BOT_INDEX}{bot_id}"
    bot = LuantiBot(LUANTI_HOST, LUANTI_PORT, username)
    
    if bot.connect():
        bot.run()
    else:
        logger.error(f"Failed to connect bot {username}")


def main():
    start_time = time.time()
    end_time = start_time + DURATION
    
    logger.info(f"Starting {BOT_COUNT} bots with index {BOT_INDEX}")
    logger.info(f"Target area: ({BOX_X},{BOX_Z}) to ({BOX_X+BOX_WIDTH},{BOX_Z+BOX_WIDTH})")
    logger.info(f"Duration: {DURATION} seconds")
    
    threads = []
    
    # Start bots with delay
    for i in range(BOT_COUNT):
        bot_thread = threading.Thread(target=start_bot, args=(i,))
        bot_thread.daemon = True
        bot_thread.start()
        threads.append(bot_thread)
        time.sleep(BOT_JOIN_DELAY)
    
    # Wait until duration expires
    try:
        remaining = end_time - time.time()
        while remaining > 0:
            logger.info(f"Test running, {int(remaining)} seconds left")
            time.sleep(min(10, remaining))
            remaining = end_time - time.time()
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    
    logger.info("Test completed, shutting down bots")
    
    # Wait for all threads to finish
    for thread in threads:
        thread.join(1.0)
    
    logger.info("All bots shut down")


if __name__ == "__main__":
    main() 