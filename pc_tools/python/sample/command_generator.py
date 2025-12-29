#!/usr/bin/env python3
"""
CCSDS-like Command Generator for SAME70
==========================================

Generates commands with the following packet structure:
- Version (3 bits)
- Type (1 bit)
- Sec hdr flag (1 bit)
- Application process ID (11 bits)
- Segment flags (2 bits)
- Source sequence count (14 bits)
- Packet length (16 bits)
- Source data (variable bytes)
- CRC (16 bits)

Author: Jongbeom-IM
Date: 2025-12-29
"""

import struct
import binascii
from typing import List, Optional
from enum import IntEnum


class PacketType(IntEnum):
    """Packet type enumeration."""
    TELEMETRY = 0
    COMMAND = 1


class SecondaryHeaderFlag(IntEnum):
    """Secondary header presence flag."""
    NOT_PRESENT = 0
    PRESENT = 1


class SegmentationFlag(IntEnum):
    """Packet segmentation flags."""
    CONTINUATION = 0b00
    FIRST = 0b01
    LAST = 0b10
    UNSEGMENTED = 0b11


class CommandGenerator:
    """Generate CCSDS-like command packets."""
    
    def __init__(self, version: int = 0, app_process_id: int = 0):
        """
        Initialize command generator.
        
        Args:
            version: Packet version (0-7, 3 bits)
            app_process_id: Application process ID (0-2047, 11 bits)
        """
        self.version = version & 0x07  # 3 bits
        self.app_process_id = app_process_id & 0x7FF  # 11 bits
        self.sequence_count = 0
    
    def generate_packet(self,
                       data: bytes,
                       packet_type: PacketType = PacketType.COMMAND,
                       sec_hdr_flag: SecondaryHeaderFlag = SecondaryHeaderFlag.NOT_PRESENT,
                       segment_flag: SegmentationFlag = SegmentationFlag.UNSEGMENTED) -> bytes:
        """
        Generate a complete packet with header, data, and CRC.
        
        Args:
            data: Source data payload (variable length)
            packet_type: Telemetry (0) or Command (1)
            sec_hdr_flag: Secondary header present flag
            segment_flag: Packet segmentation flags
            
        Returns:
            Complete packet as bytes
        """
        # Calculate packet length (data length - 1, as per CCSDS standard)
        packet_length = len(data) - 1
        if packet_length < 0:
            packet_length = 0
        
        # Build primary header (6 bytes / 48 bits)
        primary_header = self._build_primary_header(
            packet_type=packet_type,
            sec_hdr_flag=sec_hdr_flag,
            segment_flag=segment_flag,
            packet_length=packet_length
        )
        
        # Combine header and data
        packet = primary_header + data
        
        # Calculate and append CRC-16
        crc = self._calculate_crc16(packet)
        packet += struct.pack('>H', crc)  # Big-endian 16-bit CRC
        
        # Increment sequence count
        self.sequence_count = (self.sequence_count + 1) & 0x3FFF  # 14 bits
        
        return packet
    
    def _build_primary_header(self,
                             packet_type: PacketType,
                             sec_hdr_flag: SecondaryHeaderFlag,
                             segment_flag: SegmentationFlag,
                             packet_length: int) -> bytes:
        """
        Build 6-byte primary header.
        
        Bit layout:
        Byte 0: [Version:3][Type:1][Sec Hdr:1][APID:3 MSB]
        Byte 1: [APID:8 LSB]
        Byte 2: [Seg Flags:2][Sequence Count:6 MSB]
        Byte 3: [Sequence Count:8 middle]
        Byte 4: [Packet Length:8 MSB]
        Byte 5: [Packet Length:8 LSB]
        """
        # First 16 bits: Version(3) + Type(1) + SecHdr(1) + APID(11)
        word0 = (self.version << 13) | (packet_type << 12) | (sec_hdr_flag << 11) | self.app_process_id
        
        # Next 16 bits: SegFlags(2) + SequenceCount(14)
        word1 = (segment_flag << 14) | self.sequence_count
        
        # Last 16 bits: PacketLength(16)
        word2 = packet_length & 0xFFFF
        
        # Pack as big-endian 16-bit words
        header = struct.pack('>HHH', word0, word1, word2)
        
        return header
    
    def _calculate_crc16(self, data: bytes) -> int:
        """
        Calculate CRC-16-CCITT (polynomial 0x1021).
        
        Args:
            data: Data to calculate CRC for
            
        Returns:
            16-bit CRC value
        """
        crc = 0xFFFF
        
        for byte in data:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                crc &= 0xFFFF
        
        return crc
    
    def reset_sequence_count(self):
        """Reset sequence counter to 0."""
        self.sequence_count = 0
    
    def format_packet_hex(self, packet: bytes, bytes_per_line: int = 16) -> str:
        """
        Format packet as hexadecimal string for display.
        
        Args:
            packet: Packet bytes
            bytes_per_line: Number of bytes per line
            
        Returns:
            Formatted hex string
        """
        lines = []
        for i in range(0, len(packet), bytes_per_line):
            chunk = packet[i:i + bytes_per_line]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            lines.append(f'{i:04X}: {hex_str:<48} | {ascii_str}')
        return '\n'.join(lines)
    
    def decode_packet_header(self, packet: bytes) -> dict:
        """
        Decode and display packet header information.
        
        Args:
            packet: Packet bytes (at least 8 bytes: 6 header + 2 CRC)
            
        Returns:
            Dictionary with decoded header fields
        """
        if len(packet) < 8:
            raise ValueError("Packet too short (minimum 8 bytes)")
        
        # Unpack header
        word0, word1, word2 = struct.unpack('>HHH', packet[0:6])
        
        # Extract fields
        version = (word0 >> 13) & 0x07
        packet_type = (word0 >> 12) & 0x01
        sec_hdr_flag = (word0 >> 11) & 0x01
        apid = word0 & 0x7FF
        
        segment_flags = (word1 >> 14) & 0x03
        sequence_count = word1 & 0x3FFF
        
        packet_length = word2
        
        # Extract CRC
        data_end = 6 + packet_length + 1  # header + data length + 1
        if len(packet) >= data_end + 2:
            crc = struct.unpack('>H', packet[data_end:data_end + 2])[0]
        else:
            crc = None
        
        return {
            'version': version,
            'type': 'Command' if packet_type == 1 else 'Telemetry',
            'sec_hdr_flag': 'Present' if sec_hdr_flag == 1 else 'Not Present',
            'apid': apid,
            'segment_flags': segment_flags,
            'sequence_count': sequence_count,
            'packet_length': packet_length,
            'data_length': packet_length + 1,
            'crc': f'0x{crc:04X}' if crc is not None else 'N/A'
        }


def generate_test_commands(output_file: str = 'commands.txt'):
    """
    Generate test commands and save to file.
    
    Args:
        output_file: Output file path
    """
    generator = CommandGenerator(version=0, app_process_id=0x100)
    
    commands = []
    
    # Example 1: Simple LED toggle command
    data = b'LED_TOGGLE'
    packet = generator.generate_packet(data, packet_type=PacketType.COMMAND)
    commands.append(packet.hex().upper())
    
    # Example 2: Sensor read command
    data = b'SENSOR_READ_1'
    packet = generator.generate_packet(data, packet_type=PacketType.COMMAND)
    commands.append(packet.hex().upper())
    
    # Example 3: Temperature get
    data = b'TEMP_GET'
    packet = generator.generate_packet(data, packet_type=PacketType.COMMAND)
    commands.append(packet.hex().upper())
    
    # Example 4: Status check
    data = b'STATUS_CHECK'
    packet = generator.generate_packet(data, packet_type=PacketType.COMMAND)
    commands.append(packet.hex().upper())
    
    # Example 5: System reset
    data = b'SYS_RESET'
    packet = generator.generate_packet(data, packet_type=PacketType.COMMAND)
    commands.append(packet.hex().upper())
    
    # Save to file
    with open(output_file, 'w') as f:
        for cmd in commands:
            f.write(cmd + '\n')
    
    print(f"Generated {len(commands)} commands")
    print(f"Saved to: {output_file}")
    
    # Display first command details
    print(f"\nFirst command details:")
    first_packet = bytes.fromhex(commands[0])
    print(generator.format_packet_hex(first_packet))
    print("\nDecoded header:")
    header_info = generator.decode_packet_header(first_packet)
    for key, value in header_info.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    print("=" * 60)
    print("CCSDS-like Command Generator")
    print("=" * 60)
    
    # Create generator
    gen = CommandGenerator(version=0, app_process_id=0x7FF)
    
    # Generate sample packet
    sample_data = b"HELLO SAME70"
    packet = gen.generate_packet(sample_data)
    
    print("\n📦 Generated Packet:")
    print(gen.format_packet_hex(packet))
    
    print("\n📋 Decoded Header:")
    header = gen.decode_packet_header(packet)
    for key, value in header.items():
        print(f"  {key:20s}: {value}")
    
    print("\n" + "=" * 60)
    
    # Generate test command file
    print("\n🔨 Generating test commands...")
    generate_test_commands('sample/commands.txt')
    
    print("\n✅ Command generator ready!")
    print("\nUsage example:")
    print("  gen = CommandGenerator(version=0, app_process_id=0x100)")
    print("  packet = gen.generate_packet(b'YOUR_COMMAND')")
    print("  print(packet.hex())")
