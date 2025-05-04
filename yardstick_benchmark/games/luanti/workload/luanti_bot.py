#!/usr/bin/env python3
"""
Luanti (Minetest) bot client for Yardstick benchmarking
"""
import socket
import struct
import random
import time
import threading
import logging
import math
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('LuantiBot')

class LuantiBot:
    """Bot client for Luanti engine"""
    
    # Protocol constants
    PROTOCOL_ID = 0x4f457403
    TOSERVER_INIT = 0x10
    TOSERVER_POSITION = 0x23
    TOSERVER_CHAT_MESSAGE = 0x32
    TOSERVER_KEEPALIVE = 0x00
    
    def __init__(self, server, port, username):
        self.server = server
        self.port = port
        self.username = username
        self.socket = None
        self.running = False
        self.position = (0.0, 0.0, 0.0)  # x, y, z
        self.move_speed = 5.0  # blocks per second
        
    def connect(self):
        """Connect to the Luanti server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(5.0)
            logger.info(f"Bot {self.username} connecting to {self.server}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def send_init_packet(self):
        """Send initialization packet"""
        try:
            # Create and send init packet
            init_packet = struct.pack(
                "!IBBxx20s",
                self.PROTOCOL_ID,         # Protocol ID
                self.TOSERVER_INIT,       # Packet type
                0,                   # Serialization version
                self.username.encode()  # Username (max 20 chars)
            )
            self.socket.sendto(init_packet, (self.server, self.port))
            logger.info(f"Bot {self.username} sent init packet")
            return True
        except Exception as e:
            logger.error(f"Error sending init packet: {e}")
            return False
    
    def send_move_packet(self, x, y, z):
        """Send position update packet"""
        try:
            move_packet = struct.pack(
                "!IBxxddd",
                self.PROTOCOL_ID,     # Protocol ID
                self.TOSERVER_POSITION,  # Packet type
                x, y, z          # Position
            )
            self.socket.sendto(move_packet, (self.server, self.port))
            return True
        except Exception as e:
            logger.error(f"Error sending move packet: {e}")
            return False
    
    def send_chat_message(self, message):
        """Send chat message packet"""
        try:
            # Convert message to bytes, limit to 256 chars
            message_bytes = message.encode()[:256]
            msg_len = len(message_bytes)
            
            # Create packet with message length prefix
            chat_packet = struct.pack(
                f"!IBxx{msg_len}s",
                self.PROTOCOL_ID,         # Protocol ID
                self.TOSERVER_CHAT_MESSAGE,  # Packet type
                message_bytes
            )
            
            self.socket.sendto(chat_packet, (self.server, self.port))
            return True
        except Exception as e:
            logger.error(f"Error sending chat message: {e}")
            return False
    
    def send_keepalive(self):
        """Send keepalive packet"""
        try:
            keepalive_packet = struct.pack(
                "!IBxx",
                self.PROTOCOL_ID,     # Protocol ID
                self.TOSERVER_KEEPALIVE  # Packet type
            )
            self.socket.sendto(keepalive_packet, (self.server, self.port))
            return True
        except Exception as e:
            logger.error(f"Error sending keepalive: {e}")
            return False
    
    def receive_packets(self):
        """Receive and process packets from server"""
        self.socket.settimeout(1.0)
        while self.running:
            try:
                data, _ = self.socket.recvfrom(4096)
                # Just log packet reception, don't process the contents for this test
                logger.debug(f"Bot {self.username} received packet: {len(data)} bytes")
            except socket.timeout:
                # Timeout is normal, continue
                pass
            except Exception as e:
                if self.running:
                    logger.error(f"Error receiving packets: {e}")
                    break
    
    def random_walk(self):
        """Move in a random walk pattern"""
        # Start at a random position
        x, y, z = random.uniform(-10, 10), 0.0, random.uniform(-10, 10)
        self.position = (x, y, z)
        
        while self.running:
            # Calculate new position
            angle = random.uniform(0, 2 * math.pi)
            dx = math.cos(angle) * self.move_speed * 0.2
            dz = math.sin(angle) * self.move_speed * 0.2
            
            x = self.position[0] + dx
            z = self.position[2] + dz
            
            # Update position
            self.position = (x, self.position[1], z)
            self.send_move_packet(*self.position)
            
            # Send keepalive every 10 seconds
            if random.random() < 0.05:
                self.send_keepalive()
            
            # Send chat message occasionally
            if random.random() < 0.01:
                self.send_chat_message(f"Hello from bot {self.username}!")
            
            # Sleep for a short time
            time.sleep(0.2)
    
    def run(self, duration):
        """Run the bot for the specified duration"""
        if not self.connect():
            return False
        
        # Send initialization
        if not self.send_init_packet():
            return False
        
        # Start receiver thread
        self.running = True
        receiver_thread = threading.Thread(target=self.receive_packets)
        receiver_thread.daemon = True
        receiver_thread.start()
        
        # Start random walk behavior
        walker_thread = threading.Thread(target=self.random_walk)
        walker_thread.daemon = True
        walker_thread.start()
        
        # Run for the specified duration
        logger.info(f"Bot {self.username} running for {duration} seconds")
        time.sleep(duration)
        
        # Stop threads
        self.running = False
        if self.socket:
            self.socket.close()
        
        logger.info(f"Bot {self.username} finished")
        return True


if __name__ == "__main__":
    # Simple test 
    bot = LuantiBot("localhost", 30000, "TestBot")
    if bot.run(30):
        logger.info("Bot test completed successfully")
    else:
        logger.error("Bot test failed") 