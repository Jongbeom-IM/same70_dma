#!/usr/bin/env python3
"""
SAME70-XPLD Multi-Port Raw Data Monitor
========================================

Multi-port monitoring tool with raw data logging (no packet parsing).
Receives and displays all incoming raw bytes without any filtering or parsing.

Features:
- 6 independent COM port connections
- Port configuration (COM port selection, baudrate)
- Real-time communication logging for all ports
- Receives ALL raw bytes (no packet parsing)
- Hex display for binary data
- Log export functionality
- Per-port filtering in log view

Author: Jongbeom-IM
Date: 2026-01-12
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import serial
import serial.tools.list_ports
import threading
import time
import queue
from datetime import datetime
from typing import Optional, Dict

class PortManager:
    """Manages individual COM port communication with raw data logging."""
    
    def __init__(self, port_id: int):
        self.port_id = port_id
        self.serial_port: Optional[serial.Serial] = None
        self.is_connected = False
        self.rx_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Data queue for logging
        self.log_queue = queue.Queue()
        
        # Packet counter
        self.byte_count = 0
    
    def connect(self, port: str, baudrate: int) -> bool:
        """Connect to specified port."""
        try:
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
            
            return True
        except Exception as e:
            self.log_queue.put((time.time(), f"Port {self.port_id + 1} connection failed: {e}", "error"))
            return False
    
    def disconnect(self):
        """Disconnect from port."""
        self.running = False
        self.is_connected = False
        
        if self.rx_thread and self.rx_thread.is_alive():
            self.rx_thread.join(timeout=2.0)
        
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
    
    def _rx_worker(self):
        """Background thread for receiving all raw data."""
        while self.running and self.is_connected and self.serial_port:
            try:
                if self.serial_port.in_waiting > 0:
                    # Read all available bytes
                    raw_data = self.serial_port.read(self.serial_port.in_waiting)
                    
                    if raw_data:
                        self.byte_count += len(raw_data)
                        
                        # Try to decode as text
                        try:
                            text_data = raw_data.decode('utf-8', errors='replace')
                        except:
                            text_data = None
                        
                        # Convert to hex string
                        hex_str = raw_data.hex().upper()
                        formatted_hex = ' '.join([hex_str[i:i+2] for i in range(0, len(hex_str), 2)])
                        
                        # Put in log queue with both text and hex
                        self.log_queue.put((time.time(), text_data, formatted_hex, "rx", len(raw_data)))
                    
                time.sleep(0.01)
            except Exception as e:
                self.log_queue.put((time.time(), None, f"RX Error: {e}", "error"))
                break

class MultiPortRawMonitor:
    """Main application for multi-port raw data monitoring."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("SAME70 Multi-Port Raw Data Monitor")
        self.root.geometry("1400x900")
        
        # Port managers (6 ports)
        self.port_managers: Dict[int, PortManager] = {}
        for i in range(6):
            self.port_managers[i] = PortManager(i)
        
        # Port widgets storage
        self.port_widgets: Dict[int, dict] = {}
        
        # Log filtering
        self.port_filter_vars = {}
        
        # Setup GUI
        self._setup_gui()
        
        # Refresh COM ports
        self._refresh_ports()
        
        # Start log update timer
        self._update_logs()
    
    def _setup_gui(self):
        """Setup the GUI layout."""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Port configurations
        left_panel = ttk.Frame(main_container, width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        
        # Ports configuration frame
        ports_frame = ttk.LabelFrame(left_panel, text="Port Configurations", padding=10)
        ports_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable canvas for ports
        canvas = tk.Canvas(ports_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(ports_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create port configuration widgets
        for i in range(6):
            self._create_port_widget(scrollable_frame, i)
        
        # Global refresh button
        refresh_all_btn = ttk.Button(left_panel, text="🔄 Refresh All Ports", command=self._refresh_ports)
        refresh_all_btn.pack(fill=tk.X, pady=5)
        
        # Right panel - Communication log
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Log frame
        log_frame = ttk.LabelFrame(right_panel, text="Communication Log (All Ports)", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Filter frame
        filter_frame = ttk.Frame(log_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(filter_frame, text="Show Ports:").pack(side=tk.LEFT, padx=5)
        
        for i in range(6):
            var = tk.BooleanVar(value=True)
            self.port_filter_vars[i] = var
            cb = ttk.Checkbutton(filter_frame, text=f"P{i+1}", variable=var)
            cb.pack(side=tk.LEFT, padx=2)
        
        # Select/Deselect all
        ttk.Button(filter_frame, text="All", command=self._select_all_filters).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="None", command=self._deselect_all_filters).pack(side=tk.LEFT, padx=2)
        
        # Log display
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=100,
            height=40,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Tag colors for different ports
        colors = ["blue", "green", "red", "purple", "orange", "brown"]
        for i in range(6):
            self.log_text.tag_config(f"port{i}", foreground=colors[i])
        
        self.log_text.tag_config("info", foreground="black")
        self.log_text.tag_config("warning", foreground="orange")
        self.log_text.tag_config("error", foreground="red")
        
        # Control buttons
        control_frame = ttk.Frame(right_panel)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="Clear Log", command=self._clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Export Log", command=self._export_log).pack(side=tk.LEFT, padx=5)
        
        # Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Auto-scroll", variable=self.auto_scroll_var).pack(side=tk.LEFT, padx=5)
        
        # Display mode selection
        ttk.Label(control_frame, text="Display:").pack(side=tk.LEFT, padx=(10, 2))
        self.display_mode_var = tk.StringVar(value="text")
        ttk.Radiobutton(control_frame, text="Text", variable=self.display_mode_var, value="text").pack(side=tk.LEFT)
        ttk.Radiobutton(control_frame, text="Hex", variable=self.display_mode_var, value="hex").pack(side=tk.LEFT)
        ttk.Radiobutton(control_frame, text="Both", variable=self.display_mode_var, value="both").pack(side=tk.LEFT)
        
        # Total byte count
        self.total_bytes_label = ttk.Label(control_frame, text="Total: 0 bytes")
        self.total_bytes_label.pack(side=tk.RIGHT, padx=10)
    
    def _create_port_widget(self, parent, port_id):
        """Create configuration widgets for a single port."""
        frame = ttk.LabelFrame(parent, text=f"Port {port_id + 1}", padding=5)
        frame.pack(fill=tk.X, pady=5)
        
        # Port selection
        port_frame = ttk.Frame(frame)
        port_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(port_frame, text="COM:", width=6).pack(side=tk.LEFT)
        port_var = tk.StringVar()
        port_combo = ttk.Combobox(port_frame, textvariable=port_var, width=12, state='readonly')
        port_combo.pack(side=tk.LEFT, padx=2)
        
        # Baudrate selection
        ttk.Label(port_frame, text="Baud:", width=5).pack(side=tk.LEFT, padx=(5, 0))
        baudrate_var = tk.StringVar(value='115200')
        baudrate_combo = ttk.Combobox(port_frame, textvariable=baudrate_var, width=8, state='readonly')
        baudrate_combo['values'] = ['9600', '19200', '38400', '57600', '115200', '230400', '460800', '921600']
        baudrate_combo.pack(side=tk.LEFT, padx=2)
        
        # Connect button and status
        conn_frame = ttk.Frame(frame)
        conn_frame.pack(fill=tk.X, pady=2)
        
        connect_btn = ttk.Button(conn_frame, text="Connect", command=lambda: self._toggle_connection(port_id))
        connect_btn.pack(side=tk.LEFT)
        
        status_label = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        status_label.pack(side=tk.LEFT, padx=10)
        
        # Byte counter
        byte_label = ttk.Label(conn_frame, text="0 bytes", foreground="gray")
        byte_label.pack(side=tk.RIGHT)
        
        # Store widgets
        self.port_widgets[port_id] = {
            'frame': frame,
            'port_var': port_var,
            'port_combo': port_combo,
            'baudrate_var': baudrate_var,
            'baudrate_combo': baudrate_combo,
            'connect_btn': connect_btn,
            'status_label': status_label,
            'byte_label': byte_label
        }
    
    def _refresh_ports(self):
        """Refresh available COM ports for all port widgets."""
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        
        for port_id, widgets in self.port_widgets.items():
            current = widgets['port_var'].get()
            widgets['port_combo']['values'] = port_list
            
            # Keep current selection if still valid
            if current and current in port_list:
                widgets['port_var'].set(current)
            elif port_list and not current:
                # Auto-assign first available port if none selected
                widgets['port_var'].set(port_list[0] if port_id < len(port_list) else '')
        
        self._log_message(f"Found {len(port_list)} COM port(s)", "info")
    
    def _toggle_connection(self, port_id):
        """Toggle connection for specified port."""
        manager = self.port_managers[port_id]
        widgets = self.port_widgets[port_id]
        
        if not manager.is_connected:
            port = widgets['port_var'].get()
            baudrate = int(widgets['baudrate_var'].get())
            
            if not port:
                messagebox.showerror("Error", f"Please select a COM port for Port {port_id + 1}")
                return
            
            if manager.connect(port, baudrate):
                widgets['connect_btn'].config(text="Disconnect")
                widgets['status_label'].config(text="Connected", foreground="green")
                widgets['port_combo'].config(state='disabled')
                widgets['baudrate_combo'].config(state='disabled')
                self._log_message(f"Port {port_id + 1}: Connected to {port} at {baudrate} baud", "info")
            else:
                messagebox.showerror("Connection Error", f"Failed to connect Port {port_id + 1}")
        else:
            manager.disconnect()
            widgets['connect_btn'].config(text="Connect")
            widgets['status_label'].config(text="Disconnected", foreground="red")
            widgets['port_combo'].config(state='readonly')
            widgets['baudrate_combo'].config(state='readonly')
            self._log_message(f"Port {port_id + 1}: Disconnected", "info")
    
    def _update_logs(self):
        """Update logs from all port queues."""
        for port_id, manager in self.port_managers.items():
            # Process log queue
            while not manager.log_queue.empty():
                try:
                    queue_item = manager.log_queue.get_nowait()
                    timestamp = queue_item[0]
                    
                    # Check if this port is filtered
                    if not self.port_filter_vars[port_id].get():
                        continue
                    
                    # Format message
                    time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S.%f")[:-3]
                    
                    if len(queue_item) >= 4 and queue_item[3] == "rx":
                        # RX data with text and hex
                        text_data = queue_item[1]
                        hex_data = queue_item[2]
                        byte_count = queue_item[4] if len(queue_item) > 4 else 0
                        
                        display_mode = self.display_mode_var.get()
                        
                        if display_mode == "text" and text_data:
                            log_entry = f"[{time_str}] [P{port_id + 1}] RX ({byte_count} bytes): {text_data}"
                        elif display_mode == "hex":
                            log_entry = f"[{time_str}] [P{port_id + 1}] RX ({byte_count} bytes): {hex_data}\n"
                        else:  # both
                            if text_data:
                                log_entry = f"[{time_str}] [P{port_id + 1}] RX ({byte_count} bytes):\n  Text: {text_data}  Hex: {hex_data}\n"
                            else:
                                log_entry = f"[{time_str}] [P{port_id + 1}] RX ({byte_count} bytes): {hex_data}\n"
                        
                        self.log_text.insert(tk.END, log_entry, f"port{port_id}")
                    else:
                        # Error or info message
                        message = queue_item[2] if len(queue_item) > 2 else queue_item[1]
                        msg_type = queue_item[3] if len(queue_item) > 3 else "info"
                        log_entry = f"[{time_str}] [P{port_id + 1}] {message}\n"
                        self.log_text.insert(tk.END, log_entry, msg_type)
                    
                    # Update byte counter
                    widgets = self.port_widgets[port_id]
                    widgets['byte_label'].config(text=f"{manager.byte_count} bytes")
                    
                except queue.Empty:
                    break
        
        # Update total byte count
        total_bytes = sum(m.byte_count for m in self.port_managers.values())
        self.total_bytes_label.config(text=f"Total: {total_bytes} bytes")
        
        # Auto-scroll
        if self.auto_scroll_var.get():
            self.log_text.see(tk.END)
        
        # Schedule next update
        self.root.after(50, self._update_logs)
    
    def _log_message(self, message: str, msg_type: str = "info"):
        """Log a system message."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry, msg_type)
        if self.auto_scroll_var.get():
            self.log_text.see(tk.END)
    
    def _select_all_filters(self):
        """Select all port filters."""
        for var in self.port_filter_vars.values():
            var.set(True)
    
    def _deselect_all_filters(self):
        """Deselect all port filters."""
        for var in self.port_filter_vars.values():
            var.set(False)
    
    def _clear_log(self):
        """Clear the log display."""
        self.log_text.delete(1.0, tk.END)
        self._log_message("Log cleared", "info")
    
    def _export_log(self):
        """Export log to file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"multiport_raw_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
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
        for manager in self.port_managers.values():
            if manager.is_connected:
                manager.disconnect()
        self.root.destroy()

def main():
    """Main entry point."""
    root = tk.Tk()
    app = MultiPortRawMonitor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
