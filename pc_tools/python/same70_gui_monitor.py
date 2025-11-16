#!/usr/bin/env python3
"""
SAME70-XPLD Real-time Communication Monitor
==========================================

GUI-based tool for monitoring UART communication with SAME70-XPLD board.

Features:
- Real-time COM port configuration
- Live communication status monitoring
- End-to-end latency measurement
- Packet loss rate calculation
- Visual indicators and charts
- Data logging capabilities

Author: Jongbeom-IM
Date: 2025-11-17
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import time
import queue
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json
from dataclasses import dataclass, asdict
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
# import matplotlib.animation as animation  # 사용되지 않는 import 제거

@dataclass
class CommunicationStats:
    """Communication statistics data structure."""
    packets_sent: int = 0
    packets_received: int = 0
    packets_lost: int = 0
    total_latency: float = 0.0
    min_latency: float = float('inf')
    max_latency: float = 0.0
    avg_latency: float = 0.0
    packet_loss_rate: float = 0.0
    
    def update_latency(self, latency: float):
        """Update latency statistics."""
        self.total_latency += latency
        self.min_latency = min(self.min_latency, latency)
        self.max_latency = max(self.max_latency, latency)
        if self.packets_received > 0:
            self.avg_latency = self.total_latency / self.packets_received
    
    def calculate_packet_loss(self):
        """Calculate packet loss rate."""
        if self.packets_sent > 0:
            self.packets_lost = self.packets_sent - self.packets_received
            self.packet_loss_rate = (self.packets_lost / self.packets_sent) * 100

@dataclass
class PendingPacket:
    """Pending packet for latency measurement."""
    sequence: int
    timestamp: float
    data: str

class SAME70CommMonitor:
    """Main GUI application for SAME70-XPLD communication monitoring."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SAME70-XPLD Communication Monitor")
        self.root.geometry("1200x800")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Communication variables
        self.serial_port: Optional[serial.Serial] = None
        self.is_connected = False
        self.rx_thread: Optional[threading.Thread] = None
        self.tx_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Data queues for thread communication
        self.rx_queue = queue.Queue()
        self.tx_queue = queue.Queue()
        self.log_queue = queue.Queue()
        
        # Statistics
        self.stats = CommunicationStats()
        self.pending_packets: Dict[int, PendingPacket] = {}
        self.sequence_counter = 0
        
        # Timeout management for pending packets
        self.packet_timeout = 5.0  # 5 seconds timeout
        
        # Real-time data for charts
        self.latency_history = deque(maxlen=100)
        self.packet_loss_history = deque(maxlen=100)
        self.timestamp_history = deque(maxlen=100)
        
        # GUI setup
        self.setup_gui()
        self.setup_plots()
        self.start_gui_update_timer()
        
        # Auto-refresh COM ports
        self.refresh_com_ports()
        
    def setup_gui(self):
        """Setup the main GUI interface."""
        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for responsive layout
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # 1. Connection Settings Frame
        self.setup_connection_frame(main_frame)
        
        # 2. Status Display Frame  
        self.setup_status_frame(main_frame)
        
        # 3. Control Buttons Frame
        self.setup_control_frame(main_frame)
        
        # 4. Communication Log Frame
        self.setup_log_frame(main_frame)
        
        # 5. Statistics and Charts Frame
        self.setup_charts_frame(main_frame)
    
    def setup_connection_frame(self, parent):
        """Setup connection configuration frame."""
        conn_frame = ttk.LabelFrame(parent, text="📡 Connection Settings", padding="10")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # COM Port selection
        ttk.Label(conn_frame, text="COM Port:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, width=15)
        self.port_combo.grid(row=0, column=1, padx=(0, 10))
        
        # Refresh button
        ttk.Button(conn_frame, text="🔄", width=3, 
                  command=self.refresh_com_ports).grid(row=0, column=2, padx=(0, 20))
        
        # Baudrate selection
        ttk.Label(conn_frame, text="Baudrate:").grid(row=0, column=3, sticky=tk.W, padx=(0, 5))
        self.baudrate_var = tk.StringVar(value="115200")
        baudrate_combo = ttk.Combobox(conn_frame, textvariable=self.baudrate_var, width=10,
                                     values=["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
        baudrate_combo.grid(row=0, column=4, padx=(0, 20))
        
        # Connection button
        self.connect_btn = ttk.Button(conn_frame, text="🔌 Connect", 
                                     command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=5)
    
    def setup_status_frame(self, parent):
        """Setup real-time status display frame."""
        status_frame = ttk.LabelFrame(parent, text="📊 Real-time Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        status_frame.columnconfigure(3, weight=1)
        
        # Connection Status
        ttk.Label(status_frame, text="Connection:").grid(row=0, column=0, sticky=tk.W)
        self.conn_status_label = ttk.Label(status_frame, text="❌ Disconnected", 
                                          foreground="red")
        self.conn_status_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 20))
        
        # Packets Sent/Received
        ttk.Label(status_frame, text="Packets:").grid(row=0, column=2, sticky=tk.W)
        self.packets_label = ttk.Label(status_frame, text="Sent: 0 | Received: 0")
        self.packets_label.grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        # Latency Display
        ttk.Label(status_frame, text="Latency:").grid(row=1, column=0, sticky=tk.W)
        self.latency_label = ttk.Label(status_frame, text="Avg: -- ms | Min: -- ms | Max: -- ms")
        self.latency_label.grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=(5, 0))
        
        # Packet Loss Rate
        ttk.Label(status_frame, text="Packet Loss:").grid(row=2, column=0, sticky=tk.W)
        self.packet_loss_label = ttk.Label(status_frame, text="0.0% (0 lost)")
        self.packet_loss_label.grid(row=2, column=1, sticky=tk.W, padx=(5, 0))
        
        # Data Rate
        ttk.Label(status_frame, text="Data Rate:").grid(row=2, column=2, sticky=tk.W)
        self.data_rate_label = ttk.Label(status_frame, text="-- bytes/s")
        self.data_rate_label.grid(row=2, column=3, sticky=tk.W, padx=(5, 0))
        
        # Data rate tracking variables
        self.last_data_time = time.time()
        self.bytes_received = 0
    
    def setup_control_frame(self, parent):
        """Setup control buttons frame."""
        control_frame = ttk.LabelFrame(parent, text="🎮 Controls", padding="10")
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Test commands frame
        test_frame = ttk.Frame(control_frame)
        test_frame.pack(fill=tk.X)
        
        # Command entry
        ttk.Label(test_frame, text="Send Command:").pack(side=tk.LEFT)
        self.cmd_var = tk.StringVar(value="TEST")
        cmd_entry = ttk.Entry(test_frame, textvariable=self.cmd_var, width=20)
        cmd_entry.pack(side=tk.LEFT, padx=(5, 5))
        cmd_entry.bind('<Return>', lambda e: self.send_test_packet())
        
        # Send button
        ttk.Button(test_frame, text="📤 Send", 
                  command=self.send_test_packet).pack(side=tk.LEFT, padx=(0, 20))
        
        # Auto-test controls
        self.auto_test_var = tk.BooleanVar()
        ttk.Checkbutton(test_frame, text="Auto Test", 
                       variable=self.auto_test_var,
                       command=self.toggle_auto_test).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(test_frame, text="Interval (s):").pack(side=tk.LEFT)
        self.interval_var = tk.StringVar(value="1.0")
        interval_entry = ttk.Entry(test_frame, textvariable=self.interval_var, width=8)
        interval_entry.pack(side=tk.LEFT, padx=(5, 20))
        
        # Control buttons
        ttk.Button(test_frame, text="📈 Reset Stats", 
                  command=self.reset_statistics).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(test_frame, text="💾 Save Log", 
                  command=self.save_log).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(test_frame, text="🗑️ Clear Log", 
                  command=self.clear_log).pack(side=tk.LEFT)
    
    def setup_log_frame(self, parent):
        """Setup communication log frame.""" 
        log_frame = ttk.LabelFrame(parent, text="📝 Communication Log", padding="10")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Create scrolled text widget
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=60,
                                                 font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure text tags for colored output
        self.log_text.tag_configure("tx", foreground="blue")
        self.log_text.tag_configure("rx", foreground="green") 
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("info", foreground="gray")
    
    def setup_charts_frame(self, parent):
        """Setup statistics charts frame."""
        charts_frame = ttk.LabelFrame(parent, text="📈 Statistics Charts", padding="10")
        charts_frame.grid(row=3, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        charts_frame.columnconfigure(0, weight=1)
        charts_frame.rowconfigure(0, weight=1)
        
        # Create notebook for multiple charts
        self.chart_notebook = ttk.Notebook(charts_frame)
        self.chart_notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def setup_plots(self):
        """Setup matplotlib plots."""
        # Latency chart
        self.latency_fig = Figure(figsize=(6, 3), dpi=80)
        self.latency_ax = self.latency_fig.add_subplot(111)
        self.latency_ax.set_title("Latency (ms)")
        self.latency_ax.set_xlabel("Time")
        self.latency_ax.set_ylabel("Latency (ms)")
        self.latency_ax.grid(True, alpha=0.3)
        
        latency_frame = ttk.Frame(self.chart_notebook)
        latency_canvas = FigureCanvasTkAgg(self.latency_fig, latency_frame)
        latency_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.chart_notebook.add(latency_frame, text="Latency")
        
        # Packet Loss chart
        self.packet_loss_fig = Figure(figsize=(6, 3), dpi=80)
        self.packet_loss_ax = self.packet_loss_fig.add_subplot(111)
        self.packet_loss_ax.set_title("Packet Loss Rate (%)")
        self.packet_loss_ax.set_xlabel("Time")
        self.packet_loss_ax.set_ylabel("Loss Rate (%)")
        self.packet_loss_ax.grid(True, alpha=0.3)
        
        packet_loss_frame = ttk.Frame(self.chart_notebook)
        packet_loss_canvas = FigureCanvasTkAgg(self.packet_loss_fig, packet_loss_frame)
        packet_loss_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.chart_notebook.add(packet_loss_frame, text="Packet Loss")
        
        # Store canvases for updates
        self.latency_canvas = latency_canvas
        self.packet_loss_canvas = packet_loss_canvas
    
    def refresh_com_ports(self):
        """Refresh available COM ports."""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports and not self.port_var.get():
            self.port_var.set(ports[0])
    
    def toggle_connection(self):
        """Toggle connection to SAME70-XPLD board."""
        if not self.is_connected:
            self.connect_to_board()
        else:
            self.disconnect_from_board()
    
    def connect_to_board(self):
        """Connect to SAME70-XPLD board."""
        try:
            port = self.port_var.get()
            baudrate = int(self.baudrate_var.get())
            
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
            
            # Start communication threads
            self.rx_thread = threading.Thread(target=self._rx_worker, daemon=True)
            self.tx_thread = threading.Thread(target=self._tx_worker, daemon=True)
            self.rx_thread.start()
            self.tx_thread.start()
            
            # Update UI
            self.connect_btn.configure(text="🔌 Disconnect")
            self.conn_status_label.configure(text="✅ Connected", foreground="green")
            self.log_message(f"Connected to {port} at {baudrate} baud", "info")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            self.log_message(f"Connection failed: {e}", "error")
    
    def disconnect_from_board(self):
        """Disconnect from SAME70-XPLD board."""
        self.running = False
        self.is_connected = False
        
        # Wait for threads to finish
        if self.rx_thread and self.rx_thread.is_alive():
            self.rx_thread.join(timeout=2.0)
        if self.tx_thread and self.tx_thread.is_alive():
            self.tx_thread.join(timeout=2.0)
        
        # Close serial port
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        
        # Update UI
        self.connect_btn.configure(text="🔌 Connect")
        self.conn_status_label.configure(text="❌ Disconnected", foreground="red")
        self.log_message("Disconnected from board", "info")
    
    def _rx_worker(self):
        """Background thread for receiving data."""
        while self.running and self.is_connected and self.serial_port:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.readline().decode('utf-8').strip()
                    if data:
                        self.rx_queue.put((time.time(), data))
                time.sleep(0.01)
            except Exception as e:
                self.log_queue.put((time.time(), f"RX Error: {e}", "error"))
                break
    
    def _tx_worker(self):
        """Background thread for sending data.""" 
        while self.running:
            try:
                # Check for packets to send
                try:
                    packet = self.tx_queue.get(timeout=0.1)
                    if self.serial_port and self.serial_port.is_open:
                        self.serial_port.write((packet['data'] + '\n').encode('utf-8'))
                        self.serial_port.flush()
                        
                        # Store pending packet for latency measurement
                        self.pending_packets[packet['sequence']] = PendingPacket(
                            packet['sequence'], packet['timestamp'], packet['data']
                        )
                        
                        self.log_queue.put((time.time(), f"TX: {packet['data']}", "tx"))
                        self.stats.packets_sent += 1
                        
                except queue.Empty:
                    continue
                    
            except Exception as e:
                self.log_queue.put((time.time(), f"TX Error: {e}", "error"))
    
    def send_test_packet(self):
        """Send a test packet with sequence number."""
        if not self.is_connected:
            messagebox.showwarning("Not Connected", "Please connect to the board first.")
            return
        
        command = self.cmd_var.get()
        if not command:
            return
        
        # Create packet with sequence number for latency measurement
        packet = {
            'sequence': self.sequence_counter,
            'timestamp': time.time(),
            'data': f"{command}#{self.sequence_counter}"  # Add sequence to command
        }
        
        self.tx_queue.put(packet)
        self.sequence_counter += 1
    
    def toggle_auto_test(self):
        """Toggle automatic test packet sending."""
        if self.auto_test_var.get():
            self.start_auto_test()
        else:
            self.stop_auto_test()
    
    def start_auto_test(self):
        """Start automatic test packet sending."""
        def auto_send():
            while self.auto_test_var.get() and self.is_connected:
                try:
                    interval = float(self.interval_var.get())
                    if interval < 0.1:  # Minimum interval validation
                        interval = 0.1
                    self.send_test_packet()
                    time.sleep(interval)
                except ValueError:
                    self.log_queue.put((time.time(), "Invalid interval value, stopping auto test", "error"))
                    self.auto_test_var.set(False)
                    break
                except Exception as e:
                    self.log_queue.put((time.time(), f"Auto test error: {e}", "error"))
                    break
        
        auto_thread = threading.Thread(target=auto_send, daemon=True)
        auto_thread.start()
    
    def stop_auto_test(self):
        """Stop automatic test packet sending.""" 
        self.auto_test_var.set(False)
    
    def process_received_data(self, timestamp: float, data: str):
        """Process received data and update statistics."""
        self.log_message(f"RX: {data}", "rx")
        
        # Update data rate statistics
        self.bytes_received += len(data)
        
        # Check if this is a response to a sent packet (contains sequence number)
        if '#' in data:
            try:
                parts = data.split('#')
                if len(parts) >= 2:
                    sequence = int(parts[-1])
                    
                    # Find matching pending packet
                    if sequence in self.pending_packets:
                        pending = self.pending_packets[sequence]
                        latency = (timestamp - pending.timestamp) * 1000  # Convert to ms
                        
                        # Update statistics
                        self.stats.packets_received += 1
                        self.stats.update_latency(latency)
                        self.stats.calculate_packet_loss()
                        
                        # Add to history for charts
                        self.latency_history.append(latency)
                        self.packet_loss_history.append(self.stats.packet_loss_rate)
                        self.timestamp_history.append(datetime.now())
                        
                        # Remove from pending
                        del self.pending_packets[sequence]
                        
            except (ValueError, IndexError):
                pass  # Not a sequenced response
        else:
            # Regular data (not a response to our test)
            self.stats.packets_received += 1
    
    def update_gui_elements(self):
        """Update GUI elements with current statistics."""
        # Update status labels
        self.packets_label.configure(
            text=f"Sent: {self.stats.packets_sent} | Received: {self.stats.packets_received}"
        )
        
        if self.stats.packets_received > 0:
            self.latency_label.configure(
                text=f"Avg: {self.stats.avg_latency:.1f} ms | "
                     f"Min: {self.stats.min_latency:.1f} ms | "
                     f"Max: {self.stats.max_latency:.1f} ms"
            )
        
        self.packet_loss_label.configure(
            text=f"{self.stats.packet_loss_rate:.1f}% ({self.stats.packets_lost} lost)"
        )
        
        # Update data rate (calculate every second)
        current_time = time.time()
        if current_time - self.last_data_time >= 1.0:
            data_rate = self.bytes_received / (current_time - self.last_data_time)
            self.data_rate_label.configure(text=f"{data_rate:.1f} bytes/s")
            self.bytes_received = 0
            self.last_data_time = current_time
        
        # Update charts
        self.update_charts()
    
    def update_charts(self):
        """Update real-time charts."""
        if len(self.latency_history) > 1:
            # Update latency chart
            self.latency_ax.clear()
            self.latency_ax.plot(list(self.latency_history), 'b-', linewidth=2)
            self.latency_ax.set_title("Latency (ms)")
            self.latency_ax.set_ylabel("Latency (ms)")
            self.latency_ax.grid(True, alpha=0.3)
            self.latency_canvas.draw()
            
            # Update packet loss chart
            self.packet_loss_ax.clear()
            self.packet_loss_ax.plot(list(self.packet_loss_history), 'r-', linewidth=2)
            self.packet_loss_ax.set_title("Packet Loss Rate (%)")
            self.packet_loss_ax.set_ylabel("Loss Rate (%)")
            self.packet_loss_ax.grid(True, alpha=0.3)
            self.packet_loss_canvas.draw()
    
    def start_gui_update_timer(self):
        """Start periodic GUI update timer."""
        def update_loop():
            # Process received data
            try:
                while True:
                    timestamp, data = self.rx_queue.get_nowait()
                    self.process_received_data(timestamp, data)
            except queue.Empty:
                pass
            
            # Process log messages
            try:
                while True:
                    timestamp, message, tag = self.log_queue.get_nowait()
                    self.log_message(message, tag)
            except queue.Empty:
                pass
            
            # Clean up timed-out packets
            self.cleanup_timed_out_packets()
            
            # Update GUI elements
            self.update_gui_elements()
            
            # Schedule next update
            self.root.after(100, update_loop)  # Update every 100ms
        
        # Start the update loop
        self.root.after(100, update_loop)
    
    def log_message(self, message: str, tag: str = "info"):
        """Add message to communication log."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, formatted_message, tag)
        self.log_text.see(tk.END)
        
        # Limit log size
        if int(self.log_text.index(tk.END).split('.')[0]) > 1000:
            self.log_text.delete('1.0', '100.0')
    
    def reset_statistics(self):
        """Reset all communication statistics."""
        self.stats = CommunicationStats()
        self.pending_packets.clear()
        self.sequence_counter = 0
        self.latency_history.clear()
        self.packet_loss_history.clear()
        self.timestamp_history.clear()
        self.log_message("Statistics reset", "info")
    
    def cleanup_timed_out_packets(self):
        """Clean up packets that have timed out."""
        current_time = time.time()
        timed_out_sequences = []
        
        for sequence, packet in self.pending_packets.items():
            if current_time - packet.timestamp > self.packet_timeout:
                timed_out_sequences.append(sequence)
        
        # Remove timed-out packets and count as lost
        for sequence in timed_out_sequences:
            del self.pending_packets[sequence]
            self.stats.packets_lost += 1
            self.stats.calculate_packet_loss()
    
    def clear_log(self):
        """Clear communication log."""
        self.log_text.delete('1.0', tk.END)
    
    def save_log(self):
        """Save communication log to file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Communication Log"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    # Write statistics summary
                    f.write("SAME70-XPLD Communication Log\n")
                    f.write("=" * 40 + "\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Statistics:\n")
                    f.write(f"  Packets Sent: {self.stats.packets_sent}\n")
                    f.write(f"  Packets Received: {self.stats.packets_received}\n")
                    f.write(f"  Packets Lost: {self.stats.packets_lost}\n")
                    f.write(f"  Packet Loss Rate: {self.stats.packet_loss_rate:.2f}%\n")
                    f.write(f"  Average Latency: {self.stats.avg_latency:.2f} ms\n")
                    f.write(f"  Min Latency: {self.stats.min_latency:.2f} ms\n")
                    f.write(f"  Max Latency: {self.stats.max_latency:.2f} ms\n")
                    f.write("\nCommunication Log:\n")
                    f.write("-" * 40 + "\n")
                    
                    # Write log content
                    log_content = self.log_text.get('1.0', tk.END)
                    f.write(log_content)
                
                messagebox.showinfo("Save Complete", f"Log saved to {filename}")
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save log: {e}")
    
    def on_closing(self):
        """Handle application closing."""
        if self.is_connected:
            self.disconnect_from_board()
        self.root.destroy()
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()

if __name__ == "__main__":
    # Create and run the application
    app = SAME70CommMonitor()
    app.run()