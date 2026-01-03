#!/usr/bin/env python3
"""
SAME70-XPLD Multi-Port Real-time Communication Monitor
====================================================

GUI-based tool for monitoring UART communication with multiple SAME70-XPLD boards simultaneously.

Features:
- 6 independent COM port connections
- Individual real-time status monitoring for each port
- End-to-end latency measurement per port
- Packet loss rate calculation per port
- Visual indicators and charts for all ports
- Centralized logging capabilities

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

# cmd_gen 모듈에서 필요한 클래스들을 import
from cmd_gen import CommandGenerator, DataSegment, WaveformType

class ToolTip:
    """Simple tooltip widget for providing helpful hints."""
    
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.tipwindow = None
        
    def enter(self, event=None):
        self.show_tip()
        
    def leave(self, event=None):
        self.hide_tip()
        
    def show_tip(self):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("tahoma", 8, "normal"))
        label.pack(ipadx=1)
        
    def hide_tip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

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

class PortManager:
    """Manages individual COM port communication."""
    
    def __init__(self, port_id: int):
        self.port_id = port_id
        self.serial_port: Optional[serial.Serial] = None
        self.is_connected = False
        self.rx_thread: Optional[threading.Thread] = None
        self.tx_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Data queues
        self.rx_queue = queue.Queue()
        self.tx_queue = queue.Queue()
        self.log_queue = queue.Queue()
        
        # Statistics
        self.stats = CommunicationStats()
        self.pending_packets: Dict[int, PendingPacket] = {}
        self.sequence_counter = 0
        
        # Real-time data for charts
        self.latency_history = deque(maxlen=100)
        self.packet_loss_history = deque(maxlen=100)
        
        # Timeout management
        self.packet_timeout = 5.0  # 5 seconds timeout
        self.last_cleanup_time = time.time()
        
        # Command Generator for sample packets
        self.cmd_generator = CommandGenerator(version=1, app_process_id=port_id)
        self.sample_packet_running = False
        self.debug_mode = False  # Debug mode flag
    
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
            
            # Start communication threads
            self.rx_thread = threading.Thread(target=self._rx_worker, daemon=True)
            self.tx_thread = threading.Thread(target=self._tx_worker, daemon=True)
            self.rx_thread.start()
            self.tx_thread.start()
            
            return True
        except Exception as e:
            self.log_queue.put((time.time(), f"Port {self.port_id} connection failed: {e}", "error"))
            return False
    
    def disconnect(self):
        """Disconnect from port."""
        self.running = False
        self.is_connected = False
        
        if self.rx_thread and self.rx_thread.is_alive():
            self.rx_thread.join(timeout=2.0)
        if self.tx_thread and self.tx_thread.is_alive():
            self.tx_thread.join(timeout=2.0)
        
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
    
    def send_packet(self, data: str):
        """Send packet with sequence number."""
        if not self.is_connected:
            return
        
        packet = {
            'sequence': self.sequence_counter,
            'timestamp': time.time(),
            'data': f"{data}#{self.sequence_counter}"
        }
        
        self.tx_queue.put(packet)
        self.sequence_counter += 1
    
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
                try:
                    packet = self.tx_queue.get(timeout=0.1)
                    if self.serial_port and self.serial_port.is_open:
                        self.serial_port.write((packet['data'] + '\n').encode('utf-8'))
                        self.serial_port.flush()
                        
                        self.pending_packets[packet['sequence']] = PendingPacket(
                            packet['sequence'], packet['timestamp'], packet['data']
                        )
                        
                        self.log_queue.put((time.time(), f"TX: {packet['data']}", "tx"))
                        self.stats.packets_sent += 1
                        
                except queue.Empty:
                    continue
                    
            except Exception as e:
                self.log_queue.put((time.time(), f"TX Error: {e}", "error"))
    
    def process_received_data(self, timestamp: float, data: str):
        """Process received data and update statistics."""
        self.log_queue.put((timestamp, f"RX: {data}", "rx"))
        
        if '#' in data:
            try:
                parts = data.split('#')
                if len(parts) >= 2:
                    sequence = int(parts[-1])
                    
                    if sequence in self.pending_packets:
                        pending = self.pending_packets[sequence]
                        latency = (timestamp - pending.timestamp) * 1000
                        
                        self.stats.packets_received += 1
                        self.stats.update_latency(latency)
                        self.stats.calculate_packet_loss()
                        
                        self.latency_history.append(latency)
                        self.packet_loss_history.append(self.stats.packet_loss_rate)
                        
                        del self.pending_packets[sequence]
                        
            except (ValueError, IndexError):
                pass
        else:
            self.stats.packets_received += 1
    
    def cleanup_timed_out_packets(self):
        """Clean up packets that have timed out."""
        current_time = time.time()
        
        # Only cleanup every 2 seconds to reduce overhead
        if current_time - self.last_cleanup_time < 2.0:
            return
            
        timed_out_sequences = []
        
        for sequence, packet in self.pending_packets.items():
            if current_time - packet.timestamp > self.packet_timeout:
                timed_out_sequences.append(sequence)
        
        # Remove timed-out packets and count as lost
        for sequence in timed_out_sequences:
            del self.pending_packets[sequence]
            self.stats.packets_lost += 1
            self.stats.calculate_packet_loss()
            
        self.last_cleanup_time = current_time
    
    def send_sample_packets(self, waveform_type: WaveformType, num_samples: int, max_packet_size: int):
        """Send sample packets using CommandGenerator."""
        if not self.is_connected:
            return
        
        try:
            # Create data segment
            data_segment = DataSegment(waveform_type=waveform_type, num_samples=num_samples)
            
            # DEBUG: Log waveform generation
            if self.debug_mode:
                waveform_names = {0: "SINE", 1: "TRIANGLE", 2: "SAWTOOTH", 3: "SQUARE", 4: "CUSTOM"}
                self.log_queue.put((
                    time.time(), 
                    f"[DEBUG] Generating {waveform_names.get(waveform_type, 'UNKNOWN')} waveform with {num_samples} samples",
                    "info"
                ))
            
            # Generate packets (may be split into multiple packets)
            packets = self.cmd_generator.generate_packet(data_segment, max_packet_size=max_packet_size)
            
            # DEBUG: Log packet generation info
            if self.debug_mode:
                total_data_size = len(data_segment.to_bytes())
                self.log_queue.put((
                    time.time(),
                    f"[DEBUG] Generated {len(packets)} packet(s), Total data: {total_data_size} bytes, Max packet size: {max_packet_size} bytes",
                    "info"
                ))
            
            # Send all packets
            for idx, packet in enumerate(packets, 1):
                if self.serial_port and self.serial_port.is_open:
                    self.serial_port.write(packet)
                    self.serial_port.flush()
                    self.stats.packets_sent += 1
                    
                    # Log packet transmission
                    if self.debug_mode:
                        # Detailed hex dump in debug mode
                        hex_full = packet.hex().upper()
                        # Format: XX XX XX XX ...
                        hex_formatted = ' '.join([hex_full[i:i+2] for i in range(0, min(len(hex_full), 80), 2)])
                        if len(hex_full) > 80:
                            hex_formatted += "..."
                        self.log_queue.put((
                            time.time(),
                            f"[TX] Sample Packet #{idx}/{len(packets)}: {len(packet)} bytes\n      Hex: {hex_formatted}",
                            "tx"
                        ))
                    else:
                        # Compact format in normal mode
                        hex_preview = packet.hex().upper()[:40] + "..." if len(packet) > 20 else packet.hex().upper()
                        self.log_queue.put((
                            time.time(),
                            f"[TX] Sample Packet #{idx}/{len(packets)}: {len(packet)} bytes [{hex_preview}]",
                            "tx"
                        ))
            
            # Summary log
            self.log_queue.put((
                time.time(),
                f"✓ Sent {len(packets)} sample packet(s) successfully",
                "info"
            ))
            
            return len(packets)
            
        except Exception as e:
            self.log_queue.put((time.time(), f"✗ Sample packet error: {e}", "error"))
            return 0

class MultiPortCommMonitor:
    """Main GUI application for multi-port SAME70-XPLD communication monitoring."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SAME70-XPLD Multi-Port Communication Monitor")
        self.root.geometry("1400x1000")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Port managers (6 slave devices + 1 master device)
        self.port_managers = [PortManager(i) for i in range(7)]
        self.auto_test_threads = {}
        self.sample_packet_threads = {}  # Sample packet sending threads
        self.command_lists = {}  # Store command lists for each port
        
        # GUI setup
        self.setup_gui()
        self.start_gui_update_timer()
        
        # Auto-refresh COM ports and setup periodic refresh
        self.refresh_com_ports()
        self.setup_auto_port_detection()
        
    def setup_gui(self):
        """Setup the main GUI interface."""
        # Create main notebook for different tabs
        main_notebook = ttk.Notebook(self.root, padding="5")
        main_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Port Configuration Tab
        self.setup_port_config_tab(main_notebook)
        
        # Status Monitoring Tab
        self.setup_status_tab(main_notebook)
        
        # Communication Log Tab
        self.setup_log_tab(main_notebook)
        
        # Statistics Charts Tab
        self.setup_charts_tab(main_notebook)
    
    def setup_port_config_tab(self, parent):
        """Setup port configuration tab with 6 COM port settings."""
        config_frame = ttk.Frame(parent, padding="10")
        parent.add(config_frame, text="🔌 Port Configuration")
        
        # Create scrollable frame for ports
        canvas = tk.Canvas(config_frame)
        scrollbar = ttk.Scrollbar(config_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Store GUI elements for each port
        self.port_widgets = {}
        
        # Create configuration widgets for each port (6 slaves + 1 master)
        for i in range(7):
            self.create_port_config_group(scrollable_frame, i)
        
        # Pack scrollable elements
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_port_config_group(self, parent, port_id):
        """Create configuration group for a single port."""
        # Port frame
        is_master = (port_id == 6)
        port_label = f"👑 Master Device (Port {port_id + 1})" if is_master else f"📡 Port {port_id + 1}"
        port_frame = ttk.LabelFrame(parent, text=port_label, padding="10")
        port_frame.pack(fill="x", padx=5, pady=5)
        
        # Configure grid
        port_frame.columnconfigure(1, weight=1)
        
        # Port selection widgets
        widgets = {}
        
        # COM Port with Reload button
        ttk.Label(port_frame, text="COM Port:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        widgets['port_var'] = tk.StringVar()
        widgets['port_combo'] = ttk.Combobox(port_frame, textvariable=widgets['port_var'], width=12)
        widgets['port_combo'].grid(row=0, column=1, sticky="w", padx=(0, 5))
        
        # Reload button for COM ports
        widgets['reload_btn'] = ttk.Button(
            port_frame, 
            text="🔄", 
            width=3,
            command=self.refresh_com_ports
        )
        widgets['reload_btn'].grid(row=0, column=2, sticky="w", padx=(0, 10))
        
        # Add tooltip for reload button
        self.create_tooltip(widgets['reload_btn'], 
                           "Refresh COM port list\n• Detects newly connected USB devices\n• Updates all port dropdown lists\n• Auto-assigns available ports")
        
        # Baudrate
        ttk.Label(port_frame, text="Baudrate:").grid(row=0, column=3, sticky="w", padx=(0, 5))
        widgets['baudrate_var'] = tk.StringVar(value="115200")
        widgets['baudrate_combo'] = ttk.Combobox(
            port_frame, 
            textvariable=widgets['baudrate_var'], 
            width=10,
            values=["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
        )
        widgets['baudrate_combo'].grid(row=0, column=4, sticky="w", padx=(0, 10))
        
        # Connection button
        widgets['connect_btn'] = ttk.Button(
            port_frame, 
            text="🔌 Connect", 
            command=lambda p=port_id: self.toggle_port_connection(p)
        )
        widgets['connect_btn'].grid(row=0, column=5, padx=(0, 10))
        
        # Status indicator
        widgets['status_label'] = ttk.Label(port_frame, text="❌ Disconnected", foreground="red")
        widgets['status_label'].grid(row=0, column=6, sticky="w")
        
        # Test controls
        ttk.Label(port_frame, text="Test Command:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        widgets['cmd_var'] = tk.StringVar(value=f"TEST_P{port_id + 1}")
        widgets['cmd_entry'] = ttk.Entry(port_frame, textvariable=widgets['cmd_var'], width=15)
        widgets['cmd_entry'].grid(row=1, column=1, columnspan=2, sticky="ew", padx=(0, 5), pady=(5, 0))
        widgets['cmd_entry'].bind('<Return>', lambda e, p=port_id: self.send_test_packet(p))
        
        # Load Commands button
        widgets['load_btn'] = ttk.Button(
            port_frame,
            text="📁 Load",
            width=6,
            command=lambda p=port_id: self.load_commands_from_file(p)
        )
        widgets['load_btn'].grid(row=1, column=2, sticky="e", padx=(0, 5), pady=(5, 0))
        
        # Send button
        widgets['send_btn'] = ttk.Button(
            port_frame, 
            text="📤 Send", 
            command=lambda p=port_id: self.send_test_packet(p)
        )
        widgets['send_btn'].grid(row=1, column=3, padx=(0, 10), pady=(5, 0))
        
        # Auto test checkbox
        widgets['auto_test_var'] = tk.BooleanVar()
        widgets['auto_test_cb'] = ttk.Checkbutton(
            port_frame, 
            text="Auto Test", 
            variable=widgets['auto_test_var'],
            command=lambda p=port_id: self.toggle_auto_test(p)
        )
        widgets['auto_test_cb'].grid(row=1, column=4, pady=(5, 0))
        
        # Auto test interval
        ttk.Label(port_frame, text="Interval(s):").grid(row=1, column=5, sticky="w", padx=(5, 5), pady=(5, 0))
        widgets['interval_var'] = tk.StringVar(value="1.0")
        widgets['interval_entry'] = ttk.Entry(port_frame, textvariable=widgets['interval_var'], width=6)
        widgets['interval_entry'].grid(row=1, column=6, sticky="w", pady=(5, 0))
        
        # Sample packet controls (Row 2)
        ttk.Label(port_frame, text="Sample Packets:").grid(row=2, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        
        # Waveform type selection
        widgets['waveform_var'] = tk.StringVar(value="SINE")
        widgets['waveform_combo'] = ttk.Combobox(
            port_frame, 
            textvariable=widgets['waveform_var'], 
            width=10,
            values=["SINE", "TRIANGLE", "SAWTOOTH", "SQUARE"],
            state="readonly"
        )
        widgets['waveform_combo'].grid(row=2, column=1, sticky="w", padx=(0, 5), pady=(5, 0))
        
        # Sample count
        ttk.Label(port_frame, text="Samples:").grid(row=2, column=2, sticky="e", padx=(5, 5), pady=(5, 0))
        widgets['samples_var'] = tk.StringVar(value="512")
        widgets['samples_combo'] = ttk.Combobox(
            port_frame,
            textvariable=widgets['samples_var'],
            width=8,
            values=["128", "256", "512", "1024"],
            state="readonly"
        )
        widgets['samples_combo'].grid(row=2, column=3, sticky="w", padx=(0, 5), pady=(5, 0))
        
        # Packet size
        ttk.Label(port_frame, text="Pkt Size:").grid(row=2, column=4, sticky="e", padx=(5, 5), pady=(5, 0))
        widgets['pkt_size_var'] = tk.StringVar(value="256")
        widgets['pkt_size_combo'] = ttk.Combobox(
            port_frame,
            textvariable=widgets['pkt_size_var'],
            width=8,
            values=["64", "128", "256", "512"],
            state="readonly"
        )
        widgets['pkt_size_combo'].grid(row=2, column=5, sticky="w", padx=(0, 5), pady=(5, 0))
        
        # Sample packet send button
        widgets['sample_btn'] = ttk.Button(
            port_frame,
            text="▶ Start Sample",
            command=lambda p=port_id: self.toggle_sample_packets(p)
        )
        widgets['sample_btn'].grid(row=2, column=6, sticky="ew", pady=(5, 0))
        
        self.port_widgets[port_id] = widgets
    
    def setup_status_tab(self, parent):
        """Setup status monitoring tab with 6 port status displays."""
        status_frame = ttk.Frame(parent, padding="10")
        parent.add(status_frame, text="📊 Real-time Status")
        
        # Create scrollable frame for status displays
        canvas = tk.Canvas(status_frame)
        scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Store status widgets
        self.status_widgets = {}
        
        # Create status displays for each port (6 slaves + 1 master)
        for i in range(7):
            self.create_port_status_group(scrollable_frame, i)
        
        # Pack scrollable elements
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_port_status_group(self, parent, port_id):
        """Create status display group for a single port."""
        # Status frame
        is_master = (port_id == 6)
        status_label = f"📊 Master Device Statistics" if is_master else f"📊 Port {port_id + 1} Statistics"
        status_frame = ttk.LabelFrame(parent, text=status_label, padding="10")
        status_frame.pack(fill="x", padx=5, pady=5)
        
        # Configure grid
        status_frame.columnconfigure(1, weight=1)
        status_frame.columnconfigure(3, weight=1)
        
        widgets = {}
        
        # Connection Status
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky="w")
        widgets['conn_status'] = ttk.Label(status_frame, text="❌ Disconnected", foreground="red")
        widgets['conn_status'].grid(row=0, column=1, sticky="w", padx=(5, 20))
        
        # Packets Sent/Received
        ttk.Label(status_frame, text="Packets:").grid(row=0, column=2, sticky="w")
        widgets['packets'] = ttk.Label(status_frame, text="Sent: 0 | Received: 0")
        widgets['packets'].grid(row=0, column=3, sticky="w", padx=(5, 0))
        
        # Latency Display
        ttk.Label(status_frame, text="Latency:").grid(row=1, column=0, sticky="w")
        widgets['latency'] = ttk.Label(status_frame, text="Avg: -- ms | Min: -- ms | Max: -- ms")
        widgets['latency'].grid(row=1, column=1, columnspan=3, sticky="w", padx=(5, 0))
        
        # Packet Loss Rate
        ttk.Label(status_frame, text="Packet Loss:").grid(row=2, column=0, sticky="w")
        widgets['packet_loss'] = ttk.Label(status_frame, text="0.0% (0 lost)")
        widgets['packet_loss'].grid(row=2, column=1, sticky="w", padx=(5, 0))
        
        # Reset button for this port
        widgets['reset_btn'] = ttk.Button(
            status_frame, 
            text="🔄 Reset Stats", 
            command=lambda p=port_id: self.reset_port_statistics(p)
        )
        widgets['reset_btn'].grid(row=2, column=2, columnspan=2, sticky="e", padx=(0, 0))
        
        self.status_widgets[port_id] = widgets
    
    def setup_log_tab(self, parent):
        """Setup communication log tab."""
        log_frame = ttk.Frame(parent, padding="10")
        parent.add(log_frame, text="📝 Communication Log")
        
        # Log control frame
        control_frame = ttk.Frame(log_frame)
        control_frame.pack(fill="x", pady=(0, 10))
        
        # Port filter
        ttk.Label(control_frame, text="Show Port:").pack(side="left")
        self.log_filter_var = tk.StringVar(value="All")
        filter_values = ["All"] + [f"Port {i+1}" for i in range(6)] + ["Master Device"]
        log_filter = ttk.Combobox(
            control_frame, 
            textvariable=self.log_filter_var, 
            values=filter_values,
            width=15
        )
        log_filter.pack(side="left", padx=(5, 20))
        
        # Debug mode checkbox
        self.debug_mode_var = tk.BooleanVar()
        debug_cb = ttk.Checkbutton(
            control_frame,
            text="🐛 Debug Mode",
            variable=self.debug_mode_var,
            command=self.toggle_debug_mode
        )
        debug_cb.pack(side="left", padx=(0, 20))
        self.create_tooltip(debug_cb, "Enable detailed packet logging\n• Show full hex dumps\n• Display packet generation details\n• Show waveform information")
        
        # Control buttons
        ttk.Button(control_frame, text="🗑️ Clear Log", 
                  command=self.clear_log).pack(side="left", padx=(0, 10))
        ttk.Button(control_frame, text="💾 Save Log", 
                  command=self.save_log).pack(side="left")
        
        # Log display
        self.log_text = scrolledtext.ScrolledText(log_frame, height=25, width=100,
                                                 font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)
        
        # Configure text tags for colored output
        self.log_text.tag_configure("tx", foreground="blue")
        self.log_text.tag_configure("rx", foreground="green") 
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("info", foreground="gray")
    
    def setup_charts_tab(self, parent):
        """Setup statistics charts tab."""
        charts_frame = ttk.Frame(parent, padding="10")
        parent.add(charts_frame, text="📈 Statistics Charts")
        
        # Create charts notebook for different views
        self.charts_notebook = ttk.Notebook(charts_frame)
        self.charts_notebook.pack(fill="both", expand=True)
        
        # Combined latency chart for all ports
        self.setup_combined_latency_chart()
        
        # Combined packet loss chart for all ports
        self.setup_combined_packet_loss_chart()
    
    def setup_combined_latency_chart(self):
        """Setup combined latency chart for all ports."""
        latency_frame = ttk.Frame(self.charts_notebook)
        self.charts_notebook.add(latency_frame, text="Latency Comparison")
        
        self.latency_fig = Figure(figsize=(12, 6), dpi=80)
        self.latency_ax = self.latency_fig.add_subplot(111)
        self.latency_ax.set_title("Latency Comparison (All Ports)")
        self.latency_ax.set_xlabel("Sample Number")
        self.latency_ax.set_ylabel("Latency (ms)")
        self.latency_ax.grid(True, alpha=0.3)
        
        latency_canvas = FigureCanvasTkAgg(self.latency_fig, latency_frame)
        latency_canvas.get_tk_widget().pack(fill="both", expand=True)
        self.latency_canvas = latency_canvas
    
    def setup_combined_packet_loss_chart(self):
        """Setup combined packet loss chart for all ports."""
        packet_loss_frame = ttk.Frame(self.charts_notebook)
        self.charts_notebook.add(packet_loss_frame, text="Packet Loss Comparison")
        
        self.packet_loss_fig = Figure(figsize=(12, 6), dpi=80)
        self.packet_loss_ax = self.packet_loss_fig.add_subplot(111)
        self.packet_loss_ax.set_title("Packet Loss Rate Comparison (All Ports)")
        self.packet_loss_ax.set_xlabel("Sample Number")
        self.packet_loss_ax.set_ylabel("Loss Rate (%)")
        self.packet_loss_ax.grid(True, alpha=0.3)
        
        packet_loss_canvas = FigureCanvasTkAgg(self.packet_loss_fig, packet_loss_frame)
        packet_loss_canvas.get_tk_widget().pack(fill="both", expand=True)
        self.packet_loss_canvas = packet_loss_canvas
    
    def setup_auto_port_detection(self):
        """Setup automatic port detection and monitoring."""
        # Store current ports for comparison
        self.last_known_ports = set()
        
        # Start periodic port monitoring
        self.monitor_ports()
        
    def monitor_ports(self):
        """Monitor for USB device changes and auto-refresh ports."""
        try:
            current_ports = set(port.device for port in serial.tools.list_ports.comports())
            
            # Check if ports have changed
            if current_ports != self.last_known_ports:
                added_ports = current_ports - self.last_known_ports
                removed_ports = self.last_known_ports - current_ports
                
                if added_ports or removed_ports:
                    # Log the changes
                    if hasattr(self, 'log_text'):
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        if added_ports:
                            for port in added_ports:
                                self.log_text.insert(tk.END, f"[{timestamp}] ➕ New USB device detected: {port}\n")
                        if removed_ports:
                            for port in removed_ports:
                                self.log_text.insert(tk.END, f"[{timestamp}] ➖ USB device removed: {port}\n")
                        self.log_text.see(tk.END)
                    
                    # Auto-refresh ports
                    self.refresh_com_ports()
                    
                self.last_known_ports = current_ports
                
        except Exception as e:
            pass  # Silently handle errors in background monitoring
        
        # Schedule next check in 2 seconds
        self.root.after(2000, self.monitor_ports)

    def refresh_com_ports(self):
        """Refresh available COM ports for all port widgets."""
        try:
            # Get detailed port information
            port_info = serial.tools.list_ports.comports()
            ports = []
            port_descriptions = {}
            
            for port in port_info:
                ports.append(port.device)
                # Store description for tooltip or display
                desc = f"{port.device}"
                if port.description and port.description != 'n/a':
                    desc += f" - {port.description}"
                if port.manufacturer and port.manufacturer != 'n/a':
                    desc += f" ({port.manufacturer})"
                port_descriptions[port.device] = desc
            
            # Update all port combo boxes
            current_selections = {}
            for port_id, widgets in self.port_widgets.items():
                # Save current selection
                current_selections[port_id] = widgets['port_var'].get()
                
                # Update combo box values
                widgets['port_combo']['values'] = ports
                
                # If current selection is no longer available, clear it
                if current_selections[port_id] and current_selections[port_id] not in ports:
                    widgets['port_var'].set('')
                    # Update status if port was connected
                    if self.port_managers[port_id].is_connected:
                        widgets['status_label'].config(text="⚠️ Port Lost", foreground="orange")
                        # Attempt to disconnect cleanly
                        self.port_managers[port_id].disconnect()
                        widgets['connect_btn'].configure(text="🔌 Connect")
                
                # Auto-assign ports for empty selections
                if not widgets['port_var'].get() and ports:
                    # Find an unassigned port
                    used_ports = [w['port_var'].get() for w in self.port_widgets.values() 
                                 if w['port_var'].get()]
                    available_ports = [p for p in ports if p not in used_ports]
                    if available_ports:
                        widgets['port_var'].set(available_ports[0])
            
            # Show status message (only for manual refresh)
            if not hasattr(self, '_auto_refresh_in_progress'):
                ports_count = len(ports)
                if hasattr(self, 'log_text'):
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.log_text.insert(tk.END, f"[{timestamp}] 🔄 COM ports refreshed: {ports_count} port(s) found\n")
                    if ports:
                        for port, desc in port_descriptions.items():
                            self.log_text.insert(tk.END, f"[{timestamp}]    📍 {desc}\n")
                    self.log_text.see(tk.END)
                
                # Flash reload buttons to show action completed
                for widgets in self.port_widgets.values():
                    reload_btn = widgets['reload_btn']
                    original_text = reload_btn['text']
                    reload_btn.config(text="✓", foreground="green")
                    self.root.after(500, lambda btn=reload_btn, txt=original_text: 
                                   btn.config(text=txt, foreground="black"))
                               
        except Exception as e:
            if hasattr(self, 'log_text'):
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.log_text.insert(tk.END, f"[{timestamp}] ❌ Error refreshing COM ports: {e}\n")
                self.log_text.see(tk.END)
    
    def toggle_port_connection(self, port_id):
        """Toggle connection for specified port."""
        manager = self.port_managers[port_id]
        widgets = self.port_widgets[port_id]
        
        if not manager.is_connected:
            port = widgets['port_var'].get()
            baudrate = int(widgets['baudrate_var'].get())
            
            if manager.connect(port, baudrate):
                widgets['connect_btn'].configure(text="🔌 Disconnect")
                widgets['status_label'].configure(text="✅ Connected", foreground="green")
                self.status_widgets[port_id]['conn_status'].configure(text="✅ Connected", foreground="green")
                self.log_message(f"Port {port_id + 1}: Connected to {port} at {baudrate} baud", "info")
            else:
                messagebox.showerror("Connection Error", f"Failed to connect Port {port_id + 1}")
        else:
            manager.disconnect()
            widgets['connect_btn'].configure(text="🔌 Connect")
            widgets['status_label'].configure(text="❌ Disconnected", foreground="red")
            self.status_widgets[port_id]['conn_status'].configure(text="❌ Disconnected", foreground="red")
            self.log_message(f"Port {port_id + 1}: Disconnected", "info")
    
    def load_commands_from_file(self, port_id):
        """Load commands from txt file."""
        filename = filedialog.askopenfilename(
            title=f"Load Commands for Port {port_id + 1}",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    commands = [line.strip() for line in f if line.strip()]
                
                if commands:
                    self.command_lists[port_id] = {
                        'commands': commands,
                        'current_index': 0,
                        'filename': filename.split('/')[-1]
                    }
                    
                    # Update command entry to show first command
                    widgets = self.port_widgets[port_id]
                    widgets['cmd_var'].set(commands[0])
                    
                    port_name = "Master Device" if port_id == 6 else f"Port {port_id + 1}"
                    self.log_message(
                        f"{port_name}: Loaded {len(commands)} commands from {self.command_lists[port_id]['filename']}",
                        "info"
                    )
                    messagebox.showinfo(
                        "Commands Loaded",
                        f"Loaded {len(commands)} commands for {port_name}"
                    )
                else:
                    messagebox.showwarning("Empty File", "The selected file is empty.")
                    
            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to load commands: {e}")
    
    def send_test_packet(self, port_id):
        """Send test packet on specified port."""
        manager = self.port_managers[port_id]
        widgets = self.port_widgets[port_id]
        
        if not manager.is_connected:
            port_name = "Master Device" if port_id == 6 else f"Port {port_id + 1}"
            messagebox.showwarning("Not Connected", f"{port_name} is not connected.")
            return
        
        command = widgets['cmd_var'].get()
        if command:
            manager.send_packet(command)
    
    def toggle_auto_test(self, port_id):
        """Toggle automatic test for specified port."""
        widgets = self.port_widgets[port_id]
        manager = self.port_managers[port_id]
        
        if widgets['auto_test_var'].get():
            if manager.is_connected:
                self.start_auto_test(port_id)
            else:
                widgets['auto_test_var'].set(False)
                messagebox.showwarning("Not Connected", f"Port {port_id + 1} is not connected.")
        else:
            self.stop_auto_test(port_id)
    
    def start_auto_test(self, port_id):
        """Start automatic test for specified port."""
        def auto_send():
            widgets = self.port_widgets[port_id]
            manager = self.port_managers[port_id]
            port_name = "Master Device" if port_id == 6 else f"Port {port_id + 1}"
            
            # Check if command list is loaded
            use_command_list = port_id in self.command_lists
            
            while widgets['auto_test_var'].get() and manager.is_connected:
                try:
                    interval = float(widgets['interval_var'].get())
                    if interval < 0.1:  # Minimum interval validation
                        interval = 0.1
                    
                    # Use command list if loaded, otherwise use manual command
                    if use_command_list:
                        cmd_data = self.command_lists[port_id]
                        command = cmd_data['commands'][cmd_data['current_index']]
                        
                        # Update UI to show current command
                        widgets['cmd_var'].set(command)
                        
                        # Send current command
                        if manager.is_connected:
                            manager.send_packet(command)
                        
                        # Move to next command (circular)
                        cmd_data['current_index'] = (cmd_data['current_index'] + 1) % len(cmd_data['commands'])
                    else:
                        # Use manual command from entry
                        self.send_test_packet(port_id)
                    
                    time.sleep(interval)
                except ValueError:
                    self.log_message(f"{port_name}: Invalid interval value, stopping auto test", "error")
                    widgets['auto_test_var'].set(False)
                    break
                except Exception as e:
                    self.log_message(f"{port_name}: Auto test error: {e}", "error")
                    widgets['auto_test_var'].set(False)
                    break
        
        if port_id not in self.auto_test_threads or not self.auto_test_threads[port_id].is_alive():
            auto_thread = threading.Thread(target=auto_send, daemon=True)
            auto_thread.start()
            self.auto_test_threads[port_id] = auto_thread
    
    def stop_auto_test(self, port_id):
        """Stop automatic test for specified port."""
        self.port_widgets[port_id]['auto_test_var'].set(False)
    
    def toggle_sample_packets(self, port_id):
        """Toggle sample packet sending for specified port."""
        manager = self.port_managers[port_id]
        widgets = self.port_widgets[port_id]
        
        if not manager.is_connected:
            port_name = "Master Device" if port_id == 6 else f"Port {port_id + 1}"
            messagebox.showwarning("Not Connected", f"{port_name} is not connected.")
            return
        
        if not manager.sample_packet_running:
            # Start sending sample packets
            manager.sample_packet_running = True
            widgets['sample_btn'].configure(text="⏸ Stop Sample")
            self.start_sample_packets(port_id)
        else:
            # Stop sending sample packets
            manager.sample_packet_running = False
            widgets['sample_btn'].configure(text="▶ Start Sample")
    
    def start_sample_packets(self, port_id):
        """Start continuous sample packet sending."""
        def sample_send_loop():
            widgets = self.port_widgets[port_id]
            manager = self.port_managers[port_id]
            port_name = "Master Device" if port_id == 6 else f"Port {port_id + 1}"
            
            while manager.sample_packet_running and manager.is_connected:
                try:
                    # Get parameters from GUI
                    waveform_str = widgets['waveform_var'].get()
                    num_samples = int(widgets['samples_var'].get())
                    max_packet_size = int(widgets['pkt_size_var'].get())
                    interval = float(widgets['interval_var'].get())
                    
                    # Convert waveform string to enum
                    waveform_map = {
                        "SINE": WaveformType.SINE,
                        "TRIANGLE": WaveformType.TRIANGLE,
                        "SAWTOOTH": WaveformType.SAWTOOTH,
                        "SQUARE": WaveformType.SQUARE
                    }
                    waveform_type = waveform_map.get(waveform_str, WaveformType.SINE)
                    
                    # Send sample packets
                    num_packets = manager.send_sample_packets(waveform_type, num_samples, max_packet_size)
                    
                    if num_packets > 0:
                        self.log_message(
                            f"{port_name}: Sent {num_packets} sample packet(s) [{waveform_str}, {num_samples} samples]",
                            "info"
                        )
                    
                    # Wait for interval
                    time.sleep(interval)
                    
                except ValueError as e:
                    self.log_message(f"{port_name}: Invalid parameter: {e}", "error")
                    manager.sample_packet_running = False
                    widgets['sample_btn'].configure(text="▶ Start Sample")
                    break
                except Exception as e:
                    self.log_message(f"{port_name}: Sample packet error: {e}", "error")
                    manager.sample_packet_running = False
                    widgets['sample_btn'].configure(text="▶ Start Sample")
                    break
        
        if port_id not in self.sample_packet_threads or not self.sample_packet_threads[port_id].is_alive():
            sample_thread = threading.Thread(target=sample_send_loop, daemon=True)
            sample_thread.start()
            self.sample_packet_threads[port_id] = sample_thread
    
    def reset_port_statistics(self, port_id):
        """Reset statistics for specified port."""
        manager = self.port_managers[port_id]
        manager.stats = CommunicationStats()
        manager.pending_packets.clear()
        manager.sequence_counter = 0
        manager.latency_history.clear()
        manager.packet_loss_history.clear()
        self.log_message(f"Port {port_id + 1}: Statistics reset", "info")
    
    def update_gui_elements(self):
        """Update all GUI elements with current statistics."""
        for port_id, manager in enumerate(self.port_managers):
            if port_id in self.status_widgets:
                widgets = self.status_widgets[port_id]
                stats = manager.stats
                
                # Update status labels
                widgets['packets'].configure(
                    text=f"Sent: {stats.packets_sent} | Received: {stats.packets_received}"
                )
                
                if stats.packets_received > 0:
                    widgets['latency'].configure(
                        text=f"Avg: {stats.avg_latency:.1f} ms | "
                             f"Min: {stats.min_latency:.1f} ms | "
                             f"Max: {stats.max_latency:.1f} ms"
                    )
                
                widgets['packet_loss'].configure(
                    text=f"{stats.packet_loss_rate:.1f}% ({stats.packets_lost} lost)"
                )
        
        # Update charts
        self.update_charts()
    
    def update_charts(self):
        """Update real-time charts for all ports."""
        # Only update charts if there's data to show
        has_latency_data = any(len(manager.latency_history) > 1 for manager in self.port_managers)
        has_packet_loss_data = any(len(manager.packet_loss_history) > 1 for manager in self.port_managers)
        
        if not has_latency_data and not has_packet_loss_data:
            return
            
        # Update latency chart
        if has_latency_data:
            self.latency_ax.clear()
            colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown']
            
            for port_id, manager in enumerate(self.port_managers):
                if len(manager.latency_history) > 1:
                    self.latency_ax.plot(
                        list(manager.latency_history), 
                        color=colors[port_id],
                        linewidth=2, 
                        label=f'Port {port_id + 1}',
                        alpha=0.8
                    )
        
            self.latency_ax.set_title("Latency Comparison (All Ports)")
            self.latency_ax.set_xlabel("Sample Number")
            self.latency_ax.set_ylabel("Latency (ms)")
            self.latency_ax.grid(True, alpha=0.3)
            self.latency_ax.legend()
            self.latency_canvas.draw()
        
        # Update packet loss chart
        if has_packet_loss_data:
            self.packet_loss_ax.clear()
            colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown']
            
            for port_id, manager in enumerate(self.port_managers):
                if len(manager.packet_loss_history) > 1:
                    self.packet_loss_ax.plot(
                        list(manager.packet_loss_history), 
                        color=colors[port_id],
                        linewidth=2, 
                        label=f'Port {port_id + 1}',
                        alpha=0.8
                    )
        
            self.packet_loss_ax.set_title("Packet Loss Rate Comparison (All Ports)")
            self.packet_loss_ax.set_xlabel("Sample Number")
            self.packet_loss_ax.set_ylabel("Loss Rate (%)")
            self.packet_loss_ax.grid(True, alpha=0.3)
            self.packet_loss_ax.legend()
            self.packet_loss_canvas.draw()
    
    def start_gui_update_timer(self):
        """Start periodic GUI update timer."""
        def update_loop():
            # Process data for all ports
            for port_id, manager in enumerate(self.port_managers):
                # Process received data
                try:
                    while True:
                        timestamp, data = manager.rx_queue.get_nowait()
                        manager.process_received_data(timestamp, data)
                except queue.Empty:
                    pass
                
                # Process log messages
                try:
                    while True:
                        timestamp, message, tag = manager.log_queue.get_nowait()
                        self.log_message(f"Port {port_id + 1}: {message}", tag)
                except queue.Empty:
                    pass
                
                # Cleanup timed-out packets
                manager.cleanup_timed_out_packets()
            
            # Update GUI elements
            self.update_gui_elements()
            
            # Schedule next update
            self.root.after(100, update_loop)
        
        self.root.after(100, update_loop)
    
    def log_message(self, message: str, tag: str = "info"):
        """Add message to communication log."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Apply filter if needed
        filter_value = self.log_filter_var.get()
        if filter_value != "All" and filter_value not in message:
            return
        
        self.log_text.insert(tk.END, formatted_message, tag)
        self.log_text.see(tk.END)
        
        # Limit log size
        if int(self.log_text.index(tk.END).split('.')[0]) > 1000:
            self.log_text.delete('1.0', '100.0')
    
    def toggle_debug_mode(self):
        """Toggle debug mode for all ports."""
        debug_enabled = self.debug_mode_var.get()
        
        # Update all port managers
        for manager in self.port_managers:
            manager.debug_mode = debug_enabled
        
        # Log the change
        status = "enabled" if debug_enabled else "disabled"
        self.log_message(f"🐛 Debug mode {status}", "info")
    
    def clear_log(self):
        """Clear communication log."""
        self.log_text.delete('1.0', tk.END)
    
    def save_log(self):
        """Save communication log to file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Multi-Port Communication Log"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("SAME70-XPLD Multi-Port Communication Log\n")
                    f.write("=" * 50 + "\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    # Write statistics for all ports
                    for port_id, manager in enumerate(self.port_managers):
                        if manager.stats.packets_sent > 0 or manager.stats.packets_received > 0:
                            f.write(f"Port {port_id + 1} Statistics:\n")
                            f.write(f"  Packets Sent: {manager.stats.packets_sent}\n")
                            f.write(f"  Packets Received: {manager.stats.packets_received}\n")
                            f.write(f"  Packets Lost: {manager.stats.packets_lost}\n")
                            f.write(f"  Packet Loss Rate: {manager.stats.packet_loss_rate:.2f}%\n")
                            f.write(f"  Average Latency: {manager.stats.avg_latency:.2f} ms\n")
                            f.write(f"  Min Latency: {manager.stats.min_latency:.2f} ms\n")
                            f.write(f"  Max Latency: {manager.stats.max_latency:.2f} ms\n")
                            f.write("\n")
                    
                    f.write("Communication Log:\n")
                    f.write("-" * 50 + "\n")
                    log_content = self.log_text.get('1.0', tk.END)
                    f.write(log_content)
                
                messagebox.showinfo("Save Complete", f"Multi-port log saved to {filename}")
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save log: {e}")
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for the given widget."""
        return ToolTip(widget, text)
    
    def on_closing(self):
        """Handle application closing."""
        for manager in self.port_managers:
            if manager.is_connected:
                manager.disconnect()
        self.root.destroy()
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()

if __name__ == "__main__":
    # Create and run the multi-port application
    app = MultiPortCommMonitor()
    app.run()