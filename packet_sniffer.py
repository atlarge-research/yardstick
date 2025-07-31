#!/usr/bin/env python3
"""
Packet Sniffer for Luanti protocol - Captures and decodes packets between client and server
"""

import socket
import struct
import argparse
import time
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs("sniffer_logs", exist_ok=True)

# Constants from Luanti protocol
PROTOCOL_ID = 0x4F457403
BASE_HEADER_SIZE = 7
PEER_ID_INEXISTENT = 0
PEER_ID_SERVER = 1

# Packet types
TYPE_CONTROL = 0
TYPE_ORIGINAL = 1
TYPE_SPLIT = 2
TYPE_RELIABLE = 3

# Control types
CONTROLTYPE_ACK = 0
CONTROLTYPE_SET_PEER_ID = 1
CONTROLTYPE_PING = 2
CONTROLTYPE_DISCO = 3

# Command mappings
toclient_commands = {
    0x02: "TOCLIENT_HELLO",
    0x03: "TOCLIENT_AUTH_ACCEPT",
    0x04: "TOCLIENT_ACCEPT_SUDO_MODE",
    0x05: "TOCLIENT_DENY_SUDO_MODE",
    0x0A: "TOCLIENT_ACCESS_DENIED",
    0x20: "TOCLIENT_BLOCKDATA",
    0x21: "TOCLIENT_ADDNODE",
    0x22: "TOCLIENT_REMOVENODE",
    0x27: "TOCLIENT_INVENTORY",
    0x29: "TOCLIENT_TIME_OF_DAY",
    0x2F: "TOCLIENT_CHAT_MESSAGE",
    0x31: "TOCLIENT_ACTIVE_OBJECT_REMOVE_ADD",
    0x32: "TOCLIENT_ACTIVE_OBJECT_MESSAGES",
    0x33: "TOCLIENT_HP",
    0x34: "TOCLIENT_MOVE_PLAYER",
    0x38: "TOCLIENT_MEDIA",
    0x3a: "TOCLIENT_NODEDEF",
}

toserver_commands = {
    0x02: "TOSERVER_INIT",
    0x11: "TOSERVER_INIT2",
    0x23: "TOSERVER_PLAYERPOS",
    0x24: "TOSERVER_GOTBLOCKS",
    0x25: "TOSERVER_DELETEDBLOCKS",
    0x37: "TOSERVER_INTERACT",
    0x38: "TOSERVER_REMOVED_SOUNDS",
    0x39: "TOSERVER_NODEMETA_FIELDS",
    0x3A: "TOSERVER_INVENTORY_ACTION",
    0x3B: "TOSERVER_CHAT_MESSAGE",
    0x40: "TOSERVER_REQUEST_MEDIA",
    0x70: "TOSERVER_CLICK_OBJECT",
}

class PacketLogger:
    def __init__(self, log_dir="sniffer_logs"):
        self.log_dir = log_dir
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.hex_log = open(f"{log_dir}/packets_{timestamp}.log", "w")
        self.summary_log = open(f"{log_dir}/summary_{timestamp}.log", "w")
    
    def log_hex(self, source, data):
        """Log raw hex data"""
        self.hex_log.write(f"\n{source} - {datetime.now().strftime('%H:%M:%S.%f')} - {len(data)} bytes\n")
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_values = ' '.join(f"{b:02x}" for b in chunk)
            ascii_values = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
            self.hex_log.write(f"{i:04x}: {hex_values.ljust(48)} {ascii_values}\n")
        self.hex_log.flush()
    
    def log_summary(self, message):
        """Log packet summary"""
        self.summary_log.write(f"{datetime.now().strftime('%H:%M:%S.%f')} - {message}\n")
        self.summary_log.flush()
        logger.info(message)
    
    def close(self):
        """Close all log files"""
        self.hex_log.close()
        self.summary_log.close()

class PacketDecoder:
    @staticmethod
    def decode_base_header(data):
        """Decode the base header of a packet"""
        if len(data) < BASE_HEADER_SIZE:
            return None
        
        protocol_id = struct.unpack(">I", data[0:4])[0]
        sender_peer_id = struct.unpack(">H", data[4:6])[0]
        channel = data[6]
        
        return {
            "protocol_id": protocol_id,
            "sender_peer_id": sender_peer_id,
            "channel": channel
        }
    
    @staticmethod
    def decode_packet_type(data, offset=BASE_HEADER_SIZE):
        """Decode the packet type"""
        if len(data) <= offset:
            return None
        
        packet_type = data[offset]
        result = {"type_id": packet_type}
        
        if packet_type == TYPE_CONTROL:
            result["type"] = "CONTROL"
            if len(data) <= offset + 1:
                return result
                
            control_type = data[offset + 1]
            result["control_type_id"] = control_type
            
            if control_type == CONTROLTYPE_ACK:
                result["control_type"] = "ACK"
                if len(data) <= offset + 3:
                    return result
                
                seqnum = struct.unpack(">H", data[offset+2:offset+4])[0]
                result["seqnum"] = seqnum
                
            elif control_type == CONTROLTYPE_SET_PEER_ID:
                result["control_type"] = "SET_PEER_ID"
                if len(data) <= offset + 3:
                    return result
                    
                peer_id_new = struct.unpack(">H", data[offset+2:offset+4])[0]
                result["peer_id_new"] = peer_id_new
                
            elif control_type == CONTROLTYPE_PING:
                result["control_type"] = "PING"
                
            elif control_type == CONTROLTYPE_DISCO:
                result["control_type"] = "DISCO"
            
        elif packet_type == TYPE_ORIGINAL:
            result["type"] = "ORIGINAL"
            result["payload_offset"] = offset + 1
            result["payload_size"] = len(data) - offset - 1
            
        elif packet_type == TYPE_SPLIT:
            result["type"] = "SPLIT"
            if len(data) <= offset + 6:
                return result
                
            seqnum = struct.unpack(">H", data[offset+1:offset+3])[0]
            chunk_count = struct.unpack(">H", data[offset+3:offset+5])[0]
            chunk_num = struct.unpack(">H", data[offset+5:offset+7])[0]
            
            result["seqnum"] = seqnum
            result["chunk_count"] = chunk_count
            result["chunk_num"] = chunk_num
            result["payload_offset"] = offset + 7
            result["payload_size"] = len(data) - offset - 7
            
        elif packet_type == TYPE_RELIABLE:
            result["type"] = "RELIABLE"
            if len(data) <= offset + 2:
                return result
                
            seqnum = struct.unpack(">H", data[offset+1:offset+3])[0]
            
            result["seqnum"] = seqnum
            result["payload_offset"] = offset + 3
            result["payload_size"] = len(data) - offset - 3
            
        return result
    
    @staticmethod
    def analyze_payload(data, offset, is_client_to_server):
        """Try to analyze the payload content based on the command"""
        if len(data) <= offset:
            return None
        
        # Check if we have a command ID
        if len(data) <= offset + 1:
            return {"raw": data[offset:].hex()}
        
        # Try to extract command ID (usually the first 2 bytes)
        if len(data) >= offset + 2:
            cmd_id = struct.unpack(">H", data[offset:offset+2])[0]
            
            cmd_dict = toserver_commands if is_client_to_server else toclient_commands
            cmd_name = cmd_dict.get(cmd_id, f"UNKNOWN(0x{cmd_id:04x})")
            
            result = {
                "command_id": cmd_id,
                "command_name": cmd_name,
                "raw": data[offset:offset+16].hex()  # First 16 bytes
            }
            
            # Special handling for certain commands
            if is_client_to_server:
                if cmd_id == 0x02:  # TOSERVER_INIT
                    if len(data) >= offset + 5:
                        ser_fmt = data[offset+2]
                        proto_ver = struct.unpack(">H", data[offset+3:offset+5])[0]
                        result["ser_fmt"] = ser_fmt
                        result["proto_ver"] = proto_ver
                        
                        if len(data) >= offset + 6:
                            auth_size = data[offset+5]
                            if len(data) >= offset + 6 + auth_size:
                                auth_data = data[offset+6:offset+6+auth_size]
                                try:
                                    result["username"] = auth_data.decode('utf-8')
                                except:
                                    try:
                                        # Maybe it's auth method + username
                                        if len(auth_data) >= 2:
                                            auth_method = struct.unpack(">H", auth_data[0:2])[0]
                                            result["auth_method"] = auth_method
                                            result["username_raw"] = auth_data[2:].hex()
                                    except:
                                        result["auth_data"] = auth_data.hex()
            else:
                if cmd_id == 0x02:  # TOCLIENT_HELLO
                    if len(data) >= offset + 3:
                        auth_methods_count = data[offset+2]
                        result["auth_methods_count"] = auth_methods_count
            
            return result
        
        return {"raw": data[offset:].hex()}

class PacketSniffer:
    def __init__(self, listen_port, server_port, log_dir="sniffer_logs"):
        self.listen_port = listen_port
        self.server_port = server_port
        self.listen_addr = ("0.0.0.0", listen_port)
        self.server_addr = ("127.0.0.1", server_port)
        self.logger = PacketLogger(log_dir)
        self.running = False
        self.socket = None
    
    def start(self):
        """Start the packet sniffer"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(self.listen_addr)
        self.socket.settimeout(0.1)  # Short timeout for checking self.running
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.running = True
        logger.info(f"Packet sniffer listening on port {self.listen_port}, forwarding to port {self.server_port}")
        
        try:
            while self.running:
                try:
                    # Receive data from client
                    data, client_addr = self.socket.recvfrom(4096)
                    if data:
                        # Log client packet
                        self.logger.log_hex(f"CLIENT {client_addr}", data)
                        
                        # Decode and log packet details
                        self.decode_and_log(data, True, client_addr)
                        
                        # Forward to server
                        self.server_socket.sendto(data, self.server_addr)
                        
                        # Try to receive response from server
                        for _ in range(5):  # Try a few times
                            try:
                                self.server_socket.settimeout(0.05)
                                server_data, _ = self.server_socket.recvfrom(4096)
                                if server_data:
                                    # Log server packet
                                    self.logger.log_hex(f"SERVER -> {client_addr}", server_data)
                                    
                                    # Decode and log packet details
                                    self.decode_and_log(server_data, False, client_addr)
                                    
                                    # Forward to client
                                    self.socket.sendto(server_data, client_addr)
                            except socket.timeout:
                                pass
                                
                except socket.timeout:
                    pass
                    
        except KeyboardInterrupt:
            logger.info("Packet sniffer stopping due to keyboard interrupt")
        finally:
            self.stop()
    
    def decode_and_log(self, data, is_client_to_server, client_addr):
        """Decode and log packet details"""
        direction = "CLIENT -> SERVER" if is_client_to_server else "SERVER -> CLIENT"
        
        # Decode base header
        header = PacketDecoder.decode_base_header(data)
        if not header:
            self.logger.log_summary(f"{direction} - Invalid header")
            return
            
        if header["protocol_id"] != PROTOCOL_ID:
            self.logger.log_summary(f"{direction} - Invalid protocol ID: 0x{header['protocol_id']:08x}")
            return
            
        # Decode packet type
        packet_info = PacketDecoder.decode_packet_type(data)
        if not packet_info:
            self.logger.log_summary(f"{direction} - Unknown packet type")
            return
            
        # Create summary based on packet type
        if packet_info["type"] == "CONTROL":
            summary = f"{direction} - Control {packet_info.get('control_type', 'UNKNOWN')}"
            if "seqnum" in packet_info:
                summary += f", seqnum={packet_info['seqnum']}"
            if "peer_id_new" in packet_info:
                summary += f", peer_id_new={packet_info['peer_id_new']}"
                
        elif packet_info["type"] in ["ORIGINAL", "RELIABLE"]:
            summary = f"{direction} - {packet_info['type']}"
            if "seqnum" in packet_info:
                summary += f", seqnum={packet_info['seqnum']}"
                
            # Analyze payload if available
            if "payload_offset" in packet_info:
                payload_info = PacketDecoder.analyze_payload(
                    data, packet_info["payload_offset"], is_client_to_server)
                if payload_info:
                    if "command_name" in payload_info:
                        summary += f", Command: {payload_info['command_name']}"
                        
                    if "proto_ver" in payload_info:
                        summary += f", Proto={payload_info['proto_ver']}"
                        
                    if "username" in payload_info:
                        summary += f", User='{payload_info['username']}'"
                    
                    # Include raw data for debugging
                    if "raw" in payload_info and len(payload_info["raw"]) > 0:
                        summary += f", Raw={payload_info['raw'][:32]}..."
                        
        elif packet_info["type"] == "SPLIT":
            summary = f"{direction} - Split chunk {packet_info.get('chunk_num', '?')}/{packet_info.get('chunk_count', '?')}"
            if "seqnum" in packet_info:
                summary += f", seqnum={packet_info['seqnum']}"
                
        else:
            summary = f"{direction} - Unknown packet type: {packet_info.get('type_id', '?')}"
            
        # Log the summary
        self.logger.log_summary(summary)
    
    def stop(self):
        """Stop the packet sniffer"""
        self.running = False
        
        if self.socket:
            self.socket.close()
            
        if self.server_socket:
            self.server_socket.close()
            
        if self.logger:
            self.logger.close()
            
        logger.info("Packet sniffer stopped")

def main():
    parser = argparse.ArgumentParser(description="Packet Sniffer for Luanti Protocol")
    parser.add_argument("--listen-port", type=int, default=30002,
                      help="Port to listen on (default: 30002)")
    parser.add_argument("--server-port", type=int, default=30000,
                      help="Server port to forward to (default: 30000)")
    parser.add_argument("--log-dir", default="sniffer_logs",
                      help="Directory for log files (default: sniffer_logs)")
    
    args = parser.parse_args()
    
    # Create log directory
    os.makedirs(args.log_dir, exist_ok=True)
    
    # Create and start sniffer
    sniffer = PacketSniffer(
        listen_port=args.listen_port,
        server_port=args.server_port,
        log_dir=args.log_dir
    )
    
    sniffer.start()

if __name__ == "__main__":
    main() 