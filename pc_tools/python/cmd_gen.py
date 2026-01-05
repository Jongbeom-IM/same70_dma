import struct
import binascii
import math
from typing import List, Optional
from enum import IntEnum
import argparse


class PacketType(IntEnum):
    TELEMETRY = 0
    COMMAND = 1

class SecondaryHeaderFlag(IntEnum):
    ABSOLUTE_TIME = 0
    RELATIVE_TIME = 1

class SegmentationFlags(IntEnum):
    UNSEGMENTED = 0b00
    FIRST_SEGMENT = 0b01
    CONTINUING_SEGMENT = 0b10
    LAST_SEGMENT = 0b11


class WaveformType(IntEnum):
    """파형 타입"""
    SINE = 0        # 사인파
    TRIANGLE = 1    # 삼각파
    SAWTOOTH = 2    # 톱니파
    SQUARE = 3      # 사각파
    CUSTOM = 4      # 커스텀 데이터


class DataSegment:
    
    def __init__(self, 
                 waveform_type: WaveformType = WaveformType.CUSTOM,
                 num_samples: int = 256,
                 custom_data: Optional[bytes] = None):

        self.waveform_type = waveform_type
        self.num_samples = num_samples
        self.custom_data = custom_data
    
    def to_bytes(self) -> bytes:
        if self.waveform_type == WaveformType.CUSTOM:
            if self.custom_data is None:
                raise ValueError("CUSTOM 타입은 custom_data가 필요합니다")
            return self.custom_data
        
        # 파형 생성
        if self.waveform_type == WaveformType.SINE:
            data = self._generate_sine_wave()
        elif self.waveform_type == WaveformType.TRIANGLE:
            data = self._generate_triangle_wave()
        elif self.waveform_type == WaveformType.SAWTOOTH:
            data = self._generate_sawtooth_wave()
        elif self.waveform_type == WaveformType.SQUARE:
            data = self._generate_square_wave()
        else:
            raise ValueError(f"알 수 없는 파형 타입: {self.waveform_type}")
        
        # List[int]를 bytes로 변환
        return bytes(data)
    
    def _generate_sine_wave(self, amplitude: int = 127, offset: int = 128) -> List[int]:
        table = []
        for i in range(self.num_samples):
            angle = (2 * math.pi * i) / self.num_samples
            value = int(offset + amplitude * math.sin(angle))
            value = max(0, min(255, value))  # 0~255 범위 제한
            table.append(value)
        return table

    def _generate_triangle_wave(self, amplitude: int = 255) -> List[int]:
        table = []
        half = self.num_samples // 2
        for i in range(self.num_samples):
            if i < half:
                value = int((amplitude * i) / half)
            else:
                value = int(amplitude - (amplitude * (i - half)) / half)
            value = max(0, min(255, value))
            table.append(value)
        return table
    
    def _generate_sawtooth_wave(self, amplitude: int = 255) -> List[int]:
        table = []
        for i in range(self.num_samples):
            value = int((amplitude * i) / self.num_samples)
            value = max(0, min(255, value))
            table.append(value)
        return table
    
    def _generate_square_wave(self, high_value: int = 255, low_value: int = 0) -> List[int]:
        table = []
        half = self.num_samples // 2
        for i in range(self.num_samples):
            if i < half:
                table.append(high_value)
            else:
                table.append(low_value)
        return table

class CommandGenerator:
    def __init__(self, version: int = 0, app_process_id: int = 0):
        self.version = version & 0x07 # 3 bits
        self.app_process_id = app_process_id & 0x7FF # 11 bits
        self.sequence_count = 0
        self.msg_id = 0

    def generate_packet(self,
                        data,
                        max_packet_size: int,
                        packet_type: PacketType = PacketType.COMMAND,
                        sec_hdr_flag: SecondaryHeaderFlag = SecondaryHeaderFlag.ABSOLUTE_TIME,
                        segment_flag: SegmentationFlags = SegmentationFlags.UNSEGMENTED) -> List[bytes]:
        # DataSegment 객체면 bytes로 변환
        if isinstance(data, DataSegment):
            data_bytes = data.to_bytes()
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            # 문자열 등 다른 타입이면 bytes로 변환 시도
            data_bytes = bytes(data) if not isinstance(data, bytes) else data
        
        packets = []
        
        # 패킷 분할 여부 결정
        total_data_len = len(data_bytes)
        offset = 0
        packet_index = 0
        
        while offset < total_data_len:
            # 현재 패킷에 넣을 데이터 크기 결정
            remaining = total_data_len - offset
            chunk_size = min(max_packet_size, remaining)
            chunk = data_bytes[offset:offset + chunk_size]
            
            # 세그먼트 플래그 결정
            if packet_index == 0:
                seg_flag = SegmentationFlags.FIRST_SEGMENT
            elif offset + chunk_size >= total_data_len:
                seg_flag = SegmentationFlags.LAST_SEGMENT
            else:
                seg_flag = SegmentationFlags.CONTINUING_SEGMENT
            
            # 패킷 생성
            packet_length = len(chunk) - 1
            if packet_length < 0:
                packet_length = 0
            
            primary_header = self._build_primary_header(
                packet_type=packet_type,
                sec_hdr_flag=sec_hdr_flag,
                segment_flag=seg_flag,
                packet_length=packet_length
            )
            
            packet = primary_header + chunk
            crc = self._calculate_crc16(packet)
            packet += struct.pack('>H', crc)
            self.sequence_count = (self.sequence_count + 1) & 0x3F
            
            packets.append(packet)
            
            offset += chunk_size
            packet_index += 1

        self.msg_id = (self.msg_id + 1) & 0xFF
        
        return packets
    
    def _build_primary_header(self,
                              packet_type: PacketType,
                              sec_hdr_flag: SecondaryHeaderFlag,
                              segment_flag: SegmentationFlags,
                              packet_length: int) -> bytes:
        """
        Bit layout:
        Byte 0: [Version:3][Type:1][Sec Hdr:1][APID:3 MSB]
        Byte 1: [APID:8 LSB]
        Byte 2: [Seg Flags:2][Sequence Count:6 MSB]
        Byte 3: [Msg ID:8 middle]
        Byte 4: [Packet Length:8 MSB]
        Byte 5: [Packet Length:8 LSB]
        """
        # First 16 bits: Version(3) + Type(1) + SecHdr(1) + APID(11)
        word0 = (self.version << 13) | (packet_type << 12) | (sec_hdr_flag << 11) | self.app_process_id
        
        # Next 16 bits: SegFlags(2) + SequenceCount(14)
        word1 = (segment_flag << 14) | (self.sequence_count << 8) | self.msg_id 
        
        # Last 16 bits: PacketLength(16)
        word2 = packet_length & 0xFFFF
        
        # Pack as big-endian 16-bit words
        header = struct.pack('>HHH', word0, word1, word2)
        
        return header
    
    def _calculate_crc16(self, data: bytes) -> int:
        crc = 0xFFFF
        for byte in data:
            crc ^= (byte << 8)
            for _ in range(8):
                if (crc & 0x8000):
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
                crc &= 0xFFFF # Keep it to 16 bits
        return crc
    
    def reset_sequence_count(self):
        self.sequence_count = 0


# ============================================================================
# 사용 예시
# ============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("CCSDS Command Generator - 파형 생성 테스트")
    print("=" * 70)
    
    
    
    gen = CommandGenerator(version=0, app_process_id=100)

    gen.reset_sequence_count()
    large_sine = DataSegment(waveform_type=WaveformType.SINE, num_samples=512)
    split_packets = gen.generate_packet(large_sine, max_packet_size=256)
    print(f"생성된 패킷 수: {len(split_packets)}")
    for i, pkt in enumerate(split_packets):  # 처음 3개만 출력
        print(f"  패킷 {i+1}: {len(pkt)} bytes, 헥스: {pkt.hex().upper()[:40]}...")
    
    print("\n" + "=" * 70)
    print("테스트 완료!")
    print("=" * 70)
