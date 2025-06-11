#!/usr/bin/env python3
import socket
import time
import random
import struct
import sys
import threading
import binascii

class LuantiBot:
    def __init__(self, host='localhost', port=30000, name='Bot'):
        self.host = host
        self.port = port
        self.name = name + str(random.randint(1, 1000))
        self.socket = None
        self.connected = False
        self.running = False
        self.debug = True  # Enable debug output
        
    def log(self, message):
        """Print debug message if debug is enabled"""
        if self.debug:
            print(f"[{self.name}] {message}")
        
    def connect(self):
        """Connect to the server using UDP"""
        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_addr = (self.host, self.port)
            self.log(f"Connecting to {self.host}:{self.port} via UDP")
            
            # Send TOSERVER_INIT packet (0x00)
            # Try simpler protocol initialization
            init_packet = b'\x00'  # Simple init packet
            self.log(f"Sending init packet: {binascii.hexlify(init_packet)}")
            self.socket.sendto(init_packet, self.server_addr)
            
            # Send player info
            player_packet = self.name.encode() + b'\0'
            self.log(f"Sending player packet: {player_packet}")
            self.socket.sendto(player_packet, self.server_addr)
            
            # Start a thread to receive messages
            self.running = True
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            self.connected = True
            self.log("Connection initiated")
            return True
        except Exception as e:
            self.log(f"Connection failed: {e}")
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
            
    def receive_messages(self):
        """Thread to receive and process server messages"""
        self.socket.settimeout(0.5)  # Set a timeout for recvfrom
        
        while self.running and self.socket:
            try:
                data, addr = self.socket.recvfrom(4096)
                if data:
                    # Log raw data for debugging
                    self.log(f"Received {len(data)} bytes: {binascii.hexlify(data)}")
                    
                    # Process incoming data (basic implementation)
                    if len(data) > 0:
                        self.log(f"Received data from server: {data[:20]}...")
            except socket.timeout:
                # Timeout is normal, just continue
                pass
            except Exception as e:
                self.log(f"Error receiving data: {e}")
                self.connected = False
                self.running = False
                break
            
    def send_movement(self):
        """Send random movement commands"""
        if not self.connected or not self.socket:
            return
            
        try:
            # Simple movement packet - just send position
            x = random.uniform(-10, 10)
            y = random.uniform(0, 5)
            z = random.uniform(-10, 10)
            
            # Position packet
            pos_packet = struct.pack(">fff", x, y, z)
            self.socket.sendto(pos_packet, self.server_addr)
        except Exception as e:
            self.log(f"Error sending movement: {e}")
            self.connected = False
            
    def send_chat(self, message=None):
        """Send a chat message"""
        if not self.connected or not self.socket:
            return
            
        if message is None:
            messages = [
                "Hello from a bot!",
                "Just exploring around",
                "Testing the server",
                "How's the performance?",
                "Bot reporting for duty!"
            ]
            message = random.choice(messages)
            
        try:
            # Send a simple chat message
            chat_packet = message.encode() + b'\0'
            self.socket.sendto(chat_packet, self.server_addr)
            self.log(f"Sent chat: {message}")
        except Exception as e:
            self.log(f"Error sending chat: {e}")
            self.connected = False
            
    def run(self, duration=60):
        """Run the bot for specified duration in seconds"""
        if not self.connect():
            return
            
        self.log(f"Running for {duration} seconds")
        start_time = time.time()
        
        try:
            last_chat = 0
            while time.time() - start_time < duration and self.connected:
                # Send a ping/movement every second
                self.send_movement()
                
                # Send chat message every 10 seconds
                now = time.time()
                if now - last_chat > 10:
                    self.send_chat()
                    last_chat = now
                    
                time.sleep(1)
        except KeyboardInterrupt:
            self.log("Stopped by user")
        finally:
            self.disconnect()
            
    def disconnect(self):
        """Disconnect from the server"""
        self.running = False
        if self.socket:
            try:
                # Send a disconnect packet
                disc_packet = b'\xff'  # Simple disconnect
                self.socket.sendto(disc_packet, self.server_addr)
                self.socket.close()
                self.log("Disconnected")
            except:
                pass
            self.socket = None
            self.connected = False
            
def main():
    num_bots = 1
    if len(sys.argv) > 1:
        try:
            num_bots = min(int(sys.argv[1]), 5)  # Limit to 5 bots for safety
        except:
            pass
    
    duration = 30
    if len(sys.argv) > 2:
        try:
            duration = int(sys.argv[2])
        except:
            pass
    
    print(f"Starting {num_bots} bots for {duration} seconds")
    
    bots = []
    for i in range(num_bots):
        bot = LuantiBot(name=f"TestBot_{i}")
        bots.append(bot)
    
    # Connect all bots
    for bot in bots:
        try:
            if bot.connect():
                print(f"Bot {bot.name} connection initiated")
            else:
                print(f"Failed to connect bot {bot.name}")
        except Exception as e:
            print(f"Failed to connect bot: {e}")
        time.sleep(2)  # Delay between connections to avoid overwhelming server
    
    try:
        # Let bots run for the specified duration
        print(f"Bots running for {duration} seconds...")
        start_time = time.time()
        
        # Keep sending data periodically to maintain connection
        while time.time() - start_time < duration:
            for bot in bots:
                if bot.connected:
                    bot.send_movement()
            time.sleep(2)
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        # Disconnect all bots
        for bot in bots:
            bot.disconnect()
        print("All bots disconnected")

if __name__ == "__main__":
    main() 