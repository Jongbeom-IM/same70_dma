#!/usr/bin/env python3
"""
SAME70-XPLD Simple Communication Monitor
========================================

Simplified monitoring tool with port configuration and communication logging only.
Receives and displays all incoming packets without any filtering.

Features:
- Port configuration (COM port selection, baudrate)
- Real-time communication logging
- Receives all packets (no filtering)
- Hex display for binary data
- Log export functionality

Author: Jongbeom-IM
Date: 2026-01-12
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import serial
import serial.tools.list_ports
import threading
import time
from datetime import datetime
from typing import Optional

class SimpleMonitor:
    """Simple SAME70 Communication Monitor with logging."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("SAME70 Simple Monitor")
        self.root.geometry("900x700")
        
        # Serial port connection
        self.serial_port: Optional[serial.Serial] = None
        self.is_connected = False
        self.rx_thread: Optional[threading.Thread] = None
        self.running = False
        
        # RX buffer for packet assembly
        self.rx_buffer = bytearray()
        
        # Setup GUI
        self._setup_gui()
        
        # Refresh COM port list on startup
        self._refresh_ports()
    
    def _setup_gui(self):
        """Setup the GUI layout."""
        # Port Configuration Frame
        config_frame = ttk.LabelFrame(self.root, text="Port Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # COM Port Selection
        ttk.Label(config_frame, text="COM Port:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.port_combo = ttk.Combobox(config_frame, width=15, state='readonly')
        self.port_combo.grid(row=0, column=1, padx=5, pady=5)
        
        refresh_btn = ttk.Button(config_frame, text="🔄 Refresh", command=self._refresh_ports)
        refresh_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Baudrate Selection
        ttk.Label(config_frame, text="Baudrate:").grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        self.baudrate_combo = ttk.Combobox(config_frame, width=10, state='readonly')
        self.baudrate_combo['values'] = ['9600', '19200', '38400', '57600', '115200', '230400', '460800', '921600']
        self.baudrate_combo.current(4)  # Default 115200
        self.baudrate_combo.grid(row=0, column=4, padx=5, pady=5)
        
        # Connect/Disconnect Button
        self.connect_btn = ttk.Button(config_frame, text="Connect", command=self._toggle_connection)
        self.connect_btn.grid(row=0, column=5, padx=10, pady=5)
        
        # Status Label
        self.status_label = ttk.Label(config_frame, text="Status: Disconnected", foreground="red")
        self.status_label.grid(row=0, column=6, padx=10, pady=5)
        
        # Communication Log Frame
        log_frame = ttk.LabelFrame(self.root, text="Communication Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Log Display
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            wrap=tk.WORD, 
            width=80, 
            height=30,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Tag colors for different log types
        self.log_text.tag_config("rx", foreground="blue")
        self.log_text.tag_config("tx", foreground="green")
        self.log_text.tag_config("info", foreground="black")
        self.log_text.tag_config("warning", foreground="orange")
        self.log_text.tag_config("error", foreground="red")
        
        # Control Buttons Frame
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        clear_btn = ttk.Button(control_frame, text="Clear Log", command=self._clear_log)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = ttk.Button(control_frame, text="Export Log", command=self._export_log)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_cb = ttk.Checkbutton(
            control_frame, 
            text="Auto-scroll", 
            variable=self.auto_scroll_var
        )
        auto_scroll_cb.pack(side=tk.LEFT, padx=5)
        
        # Hex display checkbox
        self.hex_display_var = tk.BooleanVar(value=True)
        hex_display_cb = ttk.Checkbutton(
            control_frame, 
            text="Hex Display", 
            variable=self.hex_display_var
        )
        hex_display_cb.pack(side=tk.LEFT, padx=5)
        
        # Packet count label
        self.packet_count_label = ttk.Label(control_frame, text="Packets: 0")
        self.packet_count_label.pack(side=tk.RIGHT, padx=10)
        
        self.packet_count = 0
    
    def _refresh_ports(self):
        """Refresh available COM ports."""
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        
        if port_list:
            self.port_combo['values'] = port_list
            self.port_combo.current(0)
            self._log_message(f"Found {len(port_list)} COM port(s)", "info")
        else:
            self.port_combo['values'] = []
            self._log_message("No COM ports found", "warning")
    
    def _toggle_connection(self):
        """Toggle connection state."""
        if self.is_connected:
            self._disconnect()
        else:
            self._connect()
    
    def _connect(self):
        """Connect to selected COM port."""
        if not self.port_combo.get():
            messagebox.showerror("Error", "Please select a COM port")
            return
        
        try:
            port = self.port_combo.get()
            baudrate = int(self.baudrate_combo.get())
            
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=1.0,
                bytesize=8,
                parity='N',
                stopbits=1
            )
            
            self.is_connected = True
            self.running = True
            
            # Start RX thread
            self.rx_thread = threading.Thread(target=self._rx_worker, daemon=True)
            self.rx_thread.start()
            
            # Update GUI
            self.connect_btn.config(text="Disconnect")
            self.status_label.config(text="Status: Connected", foreground="green")
            self.port_combo.config(state='disabled')
            self.baudrate_combo.config(state='disabled')
            
            self._log_message(f"Connected to {port} at {baudrate} baud", "info")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            self._log_message(f"Connection failed: {e}", "error")
    
    def _disconnect(self):
        """Disconnect from COM port."""
        self.running = False
        self.is_connected = False
        
        if self.rx_thread and self.rx_thread.is_alive():
            self.rx_thread.join(timeout=2.0)
        
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        
        # Update GUI
        self.connect_btn.config(text="Connect")
        self.status_label.config(text="Status: Disconnected", foreground="red")
        self.port_combo.config(state='readonly')
        self.baudrate_combo.config(state='readonly')
        
        # Clear buffer
        self.rx_buffer.clear()
        
        self._log_message("Disconnected", "info")
    
    def _rx_worker(self):
        """Background thread for receiving all data."""
        while self.running and self.is_connected and self.serial_port:
            try:
                if self.serial_port.in_waiting > 0:
                    # Read all available bytes
                    raw_data = self.serial_port.read(self.serial_port.in_waiting)
                    
                    # Add to buffer
                    self.rx_buffer.extend(raw_data)
                    
                    # Process buffer to extract packets
                    self._process_rx_buffer()
                    
                time.sleep(0.01)
            except Exception as e:
                self._log_message(f"RX Error: {e}", "error")
                break
    
    def _process_rx_buffer(self):
        """Process RX buffer and extract all packets."""
        while True:
            # Find packet start marker (30 0X where X = 0~5)
            start_idx = self._find_packet_start(self.rx_buffer)
            
            if start_idx == -1:
                # No packet start found
                if len(self.rx_buffer) > 0:
                    # Display any data in buffer if not a valid packet start
                    if len(self.rx_buffer) > 4096:
                        # Buffer too large, clear it
                        self.rx_buffer.clear()
                break
            
            # Remove any data before packet start
            if start_idx > 0:
                self.rx_buffer = self.rx_buffer[start_idx:]
            
            # Parse packet length from header
            expected_length = self._parse_packet_length(self.rx_buffer, 0)
            
            if expected_length is None:
                # Not enough data for header yet
                break
            
            # Check if we have the complete packet
            if len(self.rx_buffer) < expected_length:
                # Wait for more data
                break
            
            # Extract complete packet
            complete_packet = self.rx_buffer[:expected_length]
            self.rx_buffer = self.rx_buffer[expected_length:]
            
            # Display the packet
            self._display_packet(complete_packet)
            self.packet_count += 1
            
            # Update packet count
            self.root.after(0, self._update_packet_count)
    
    def _find_packet_start(self, buffer, start_pos=0):
        """Find packet start marker (30 0X where X = 0~5)."""
        for i in range(start_pos, len(buffer) - 1):
            if buffer[i] == 0x30 and 0x00 <= buffer[i + 1] <= 0x05:
                return i
        return -1
    
    def _parse_packet_length(self, buffer, start_idx) -> Optional[int]:
        """Parse packet length from header.
        
        Header structure (6 bytes):
        Byte 0-1: Version/Type/SecHdr/APID
        Byte 2-3: SegFlags/SeqCount/MsgID
        Byte 4-5: Packet Length (data length - 1)
        Total packet size = 6 (header) + packet_length + 1 (data) + 2 (CRC)
        """
        if len(buffer) < start_idx + 6:
            return None  # Not enough data for header
        
        # Read packet length from bytes 4-5 (big-endian)
        packet_length = (buffer[start_idx + 4] << 8) | buffer[start_idx + 5]
        
        # Total packet size = header(6) + data(packet_length+1) + CRC(2)
        total_size = 6 + packet_length + 1 + 2
        
        return total_size
    
    def _display_packet(self, packet: bytearray):
        """Display received packet in log."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if self.hex_display_var.get():
            # Display as hex
            hex_str = packet.hex().upper()
            formatted_hex = ' '.join([hex_str[i:i+2] for i in range(0, len(hex_str), 2)])
            message = f"[{timestamp}] RX ({len(packet)} bytes): {formatted_hex}\n"
        else:
            # Display as raw bytes
            message = f"[{timestamp}] RX ({len(packet)} bytes): {packet}\n"
        
        self._log_message(message, "rx", newline=False)
    
    def _log_message(self, message: str, tag: str = "info", newline: bool = True):
        """Log message to the text widget."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if newline and not message.endswith('\n'):
            message += '\n'
        
        # Add timestamp if not already present
        if not message.startswith('['):
            message = f"[{timestamp}] {message}"
        
        # Update GUI from main thread
        def update_text():
            self.log_text.insert(tk.END, message, tag)
            if self.auto_scroll_var.get():
                self.log_text.see(tk.END)
        
        self.root.after(0, update_text)
    
    def _update_packet_count(self):
        """Update packet count label."""
        self.packet_count_label.config(text=f"Packets: {self.packet_count}")
    
    def _clear_log(self):
        """Clear the log display."""
        self.log_text.delete(1.0, tk.END)
        self.packet_count = 0
        self._update_packet_count()
        self._log_message("Log cleared", "info")
    
    def _export_log(self):
        """Export log to file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"same70_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filename:
            try:
                log_content = self.log_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                self._log_message(f"Log exported to {filename}", "info")
                messagebox.showinfo("Export Success", f"Log saved to:\n{filename}")
            except Exception as e:
                self._log_message(f"Export failed: {e}", "error")
                messagebox.showerror("Export Error", f"Failed to save log:\n{e}")
    
    def on_closing(self):
        """Handle window closing event."""
        if self.is_connected:
            self._disconnect()
        self.root.destroy()

def main():
    """Main entry point."""
    root = tk.Tk()
    app = SimpleMonitor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
