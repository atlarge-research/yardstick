#!/usr/bin/env python3
"""
Simple test script for connecting to a Luanti server without using the Yardstick framework.
This script will:
1. Connect to a local Luanti server
2. Send some basic commands
3. Analyze server responses
"""

import socket
import time
import random
import struct
import sys
import binascii
import threading

class LuantiClientTest:
    def __init__(self, host='localhost', port=30000):
        self.host = host
        self.port = port
        self.protocol_id = "Minetest"
        self.min_net_proto_version = 37
        self.max_net_proto_version = 40
        self.socket = None
        self.server_addr = None
        self.running = False
        self.connected = False
        self.received_data = []
        
    def connect(self):
        """Connect to the server and establish a connection"""
        try:
            # Check if server is running with TCP - this is just to check
            tcp_check = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                tcp_check.connect((self.host, self.port))
                print(f"TCP connection possible to {self.host}:{self.port}")
                tcp_check.close()
            except:
                print(f"No TCP connection available to {self.host}:{self.port}")
            
            # Create the UDP socket for the actual connection
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(1)
            self.server_addr = (self.host, self.port)
            print(f"Created UDP socket to {self.host}:{self.port}")
            
            # Try with different protocols and packet formats
            self.test_protocol_formats()
            
            # Start a thread to receive and log server responses
            self.running = True
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            return True
        except Exception as e:
            print(f"Connection setup failed: {e}")
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
    
    def test_protocol_formats(self):
        """Try different protocol formats to see what works"""
        
        # Format 1 - Simple raw string
        packet = "MINETEST_INIT".encode()
        print(f"Sending format 1: {packet}")
        self.socket.sendto(packet, self.server_addr)
        time.sleep(0.5)
        
        # Format 2 - Protocol ID with version
        packet = self.protocol_id.encode() + struct.pack(">HH", 
                                                       self.min_net_proto_version, 
                                                       self.max_net_proto_version)
        print(f"Sending format 2: {binascii.hexlify(packet)}")
        self.socket.sendto(packet, self.server_addr)
        time.sleep(0.5)
        
        # Format 3 - TOSERVER_INIT with version 29 for serialization
        packet = struct.pack(">BHB", 0x01, 29, 39)
        print(f"Sending format 3: {binascii.hexlify(packet)}")
        self.socket.sendto(packet, self.server_addr)
        time.sleep(0.5)
        
        # Format 4 - TOSERVER_INIT with binary safe strings
        packet = struct.pack(">B", 0x01) + self.protocol_id.encode() + b'\0' + struct.pack(">HH", 37, 40)
        print(f"Sending format 4: {binascii.hexlify(packet)}")
        self.socket.sendto(packet, self.server_addr)
        time.sleep(0.5)
        
        # Format 5 - Attempt connection as a client with player name
        player_name = f"TestPlayer_{random.randint(1000, 9999)}"
        packet = struct.pack(">B", 0x00) + player_name.encode() + b'\0'
        print(f"Sending format 5 (player: {player_name}): {binascii.hexlify(packet)}")
        self.socket.sendto(packet, self.server_addr)
        time.sleep(0.5)
        
    def receive_messages(self):
        """Thread to receive and log server responses"""
        while self.running and self.socket:
            try:
                data, addr = self.socket.recvfrom(4096)
                if data:
                    # Save and log the data
                    self.received_data.append((time.time(), data))
                    print(f"Received {len(data)} bytes: {binascii.hexlify(data)}")
                    
                    # Try to interpret the data
                    if len(data) > 0:
                        cmd = data[0]
                        print(f"Command byte: 0x{cmd:02x}")
                        
                        if cmd == 0x02:
                            print("Received TOCLIENT_HELLO")
                        elif cmd == 0x03:
                            print("Received TOCLIENT_AUTH_ACCEPT")
                        elif cmd == 0x0A:
                            print("Received TOCLIENT_INIT")
                        else:
                            print(f"Unknown command: 0x{cmd:02x}")
            except socket.timeout:
                # Timeout is normal, just continue
                pass
            except Exception as e:
                print(f"Error receiving data: {e}")
                break
    
    def send_keepalive(self):
        """Send a keepalive packet"""
        if not self.socket:
            return
            
        try:
            # Try a few different keepalive formats
            packet1 = struct.pack(">B", 0x00)  # Simple null command
            self.socket.sendto(packet1, self.server_addr)
            print("Sent keepalive packet 1")
            
            packet2 = b"ping"
            self.socket.sendto(packet2, self.server_addr)
            print("Sent keepalive packet 2")
            
            # More complex keepalive with player position
            packet3 = struct.pack(">Bfff", 0x23, 0.0, 0.0, 0.0)  # Player position at origin
            self.socket.sendto(packet3, self.server_addr)
            print("Sent keepalive packet 3 (position)")
        except Exception as e:
            print(f"Error sending keepalive: {e}")
    
    def disconnect(self):
        """Close the connection"""
        self.running = False
        if self.socket:
            try:
                disc_packet = struct.pack(">B", 0x02)  # TOSERVER_DISCONNECT
                self.socket.sendto(disc_packet, self.server_addr)
                self.socket.close()
                print("Disconnected from server")
            except:
                pass
            self.socket = None
    
    def run_test(self, duration=30):
        """Run the test for a specified duration"""
        if not self.connect():
            return
            
        print(f"Running test for {duration} seconds")
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                # Send a keepalive every 5 seconds
                if time.time() - start_time > 5 and (time.time() - start_time) % 5 < 0.1:
                    self.send_keepalive()
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Test stopped by user")
        finally:
            self.disconnect()
            
        # Analyze results
        print("\nTest Results:")
        print(f"Received {len(self.received_data)} packets from server")
        for i, (timestamp, data) in enumerate(self.received_data):
            print(f"Packet {i+1}: {len(data)} bytes, command: 0x{data[0]:02x}")
            
        if not self.received_data:
            print("No response received from server. Possible issues:")
            print("1. Server is not accepting connections")
            print("2. Protocol implementation doesn't match server expectations")
            print("3. Server configuration doesn't allow external connections")
            print("4. Firewall is blocking traffic")
            
            print("\nNext steps:")
            print("1. Check server logs for connection attempts")
            print("2. Verify server is running with --debug flag")
            print("3. Try running the test with a different protocol version")
        
if __name__ == "__main__":
    test = LuantiClientTest()
    test.run_test(30) 