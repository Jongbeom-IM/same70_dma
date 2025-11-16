#!/usr/bin/env python3
"""
SAME70-XPLD UART Communication Tool
===================================

This module provides communication interface with SAME70-XPLD board
via UART/USB CDC interface.

Features:
- Real-time data monitoring
- Command sending with response parsing
- Data logging and visualization
- Protocol analysis tools

Author: Your Name
Date: 2025-11-17
"""

import serial
import time
import threading
from typing import Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SerialConfig:
    """Serial port configuration for SAME70-XPLD communication."""
    port: str = "COM3"  # Default Windows COM port
    baudrate: int = 115200
    timeout: float = 1.0
    bytesize: int = 8
    parity: str = 'N'
    stopbits: int = 1

class SAME70Communicator:
    """Main communication class for SAME70-XPLD board."""
    
    def __init__(self, config: SerialConfig):
        self.config = config
        self.serial_port: Optional[serial.Serial] = None
        self.is_connected = False
        self.rx_callback: Optional[Callable[[bytes], None]] = None
        self.rx_thread: Optional[threading.Thread] = None
        self.running = False
        
    def connect(self) -> bool:
        """Connect to SAME70-XPLD board."""
        try:
            self.serial_port = serial.Serial(
                port=self.config.port,
                baudrate=self.config.baudrate,
                timeout=self.config.timeout,
                bytesize=self.config.bytesize,
                parity=self.config.parity,
                stopbits=self.config.stopbits
            )
            self.is_connected = True
            self.start_rx_thread()
            print(f"✅ Connected to {self.config.port} at {self.config.baudrate} baud")
            return True
        except serial.SerialException as e:
            print(f"❌ Connection failed: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from SAME70-XPLD board."""
        self.running = False
        if self.rx_thread and self.rx_thread.is_alive():
            self.rx_thread.join(timeout=2.0)
        
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.is_connected = False
            print("📡 Disconnected from SAME70-XPLD")
    
    def send_command(self, command: str) -> bool:
        """Send command to SAME70-XPLD board."""
        if not self.is_connected or not self.serial_port:
            print("❌ Not connected to board")
            return False
            
        try:
            # Add newline if not present
            if not command.endswith('\n'):
                command += '\n'
            
            self.serial_port.write(command.encode('utf-8'))
            self.serial_port.flush()
            print(f"📤 Sent: {command.strip()}")
            return True
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False
    
    def send_binary_data(self, data: bytes) -> bool:
        """Send binary data to SAME70-XPLD board."""
        if not self.is_connected or not self.serial_port:
            print("❌ Not connected to board")
            return False
            
        try:
            self.serial_port.write(data)
            self.serial_port.flush()
            print(f"📤 Sent binary data: {len(data)} bytes")
            return True
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False
    
    def set_rx_callback(self, callback: Callable[[bytes], None]):
        """Set callback function for received data."""
        self.rx_callback = callback
    
    def start_rx_thread(self):
        """Start receive thread."""
        self.running = True
        self.rx_thread = threading.Thread(target=self._rx_worker, daemon=True)
        self.rx_thread.start()
    
    def _rx_worker(self):
        """Background thread for receiving data."""
        while self.running and self.is_connected and self.serial_port:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    if data and self.rx_callback:
                        self.rx_callback(data)
                time.sleep(0.01)  # Small delay to prevent CPU overload
            except Exception as e:
                print(f"❌ RX error: {e}")
                break

def default_rx_handler(data: bytes):
    """Default handler for received data."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    try:
        # Try to decode as text
        text = data.decode('utf-8').strip()
        print(f"📥 [{timestamp}] Received: {text}")
    except UnicodeDecodeError:
        # Handle binary data
        hex_data = ' '.join(f"{b:02X}" for b in data)
        print(f"📥 [{timestamp}] Binary: {hex_data}")

if __name__ == "__main__":
    # Example usage
    config = SerialConfig(port="COM3", baudrate=115200)
    comm = SAME70Communicator(config)
    comm.set_rx_callback(default_rx_handler)
    
    if comm.connect():
        try:
            # Send test command
            comm.send_command("TEST")
            
            # Keep alive for testing
            print("Press Ctrl+C to exit...")
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping...")
        finally:
            comm.disconnect()