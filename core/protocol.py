import typing
import struct

# 통신 설정 상수
BAUD_RATE = 4800
PACKET_SIZE = 16

# 운전 모드 상수
MODE_COOL = 0x00
MODE_DRY = 0x01
MODE_FAN = 0x02
MODE_AUTO = 0x03
MODE_HEAT = 0x04

# 풍량 상태 상수
FAN_SPEED_LOW = 0x01
FAN_SPEED_AUTO_NATURAL = 0x02
FAN_SPEED_MEDIUM = 0x04
FAN_SPEED_HIGH = 0x08
FAN_SPEED_POWER = 0x10

def calculate_checksum(packet: bytes) -> int:
    """
    16바이트 패킷의 0~14 인덱스 합을 256으로 나눈 뒤 0x55와 XOR 연산합니다.
    8비트 정수 오버플로우를 방지하기 위해 각 바이트와 최종 결과에 & 0xFF를 적용합니다.
    """
    if len(packet) < 15:
        raise ValueError("패킷 길이가 충분하지 않습니다.")
    
    payload_sum = sum(b & 0xFF for b in packet[:15]) % 256
    checksum = (payload_sum ^ 0x55) & 0xFF
    return checksum

def validate_packet(packet: bytes) -> bool:
    """
    바이너리가 16바이트인지 검증하고 체크섬을 확인합니다.
    """
    if len(packet) != PACKET_SIZE:
        return False
    
    expected_checksum = calculate_checksum(packet)
    actual_checksum = packet[15] & 0xFF
    
    return expected_checksum == actual_checksum

def parse_packet(packet: bytes) -> typing.Dict[str, typing.Any]:
    """
    유효성이 검증된 16바이트 패킷을 역직렬화하여 상태 데이터를 추출합니다.
    """
    if not validate_packet(packet):
        raise ValueError("유효하지 않은 패킷입니다.")
    
    # 설정 온도 (RX Byte 7)
    target_temp_raw = packet[7] & 0xFF
    target_temp = (target_temp_raw & 0x0F) + 15
    if target_temp < 16 or target_temp > 30:
        target_temp = max(16, min(30, target_temp)) # Guard Clause
        
    # 실내 온도 (RX Byte 8)
    room_temp_raw = packet[8] & 0xFF
    room_temp = round((192 - room_temp_raw) / 3.0, 1)
    
    # 배관 온도 (RX Byte 9) - 통상 9~10 활용
    pipe_temp_raw = packet[9] & 0xFF
    pipe_temp = round((192 - pipe_temp_raw) / 3.0, 1)
    
    # 임의 바이트 추출 (문서에 4.1~4.3 정의되어 있으나 위치 미기재 시 일반화 처리)
    mode_raw = packet[5] & 0xFF
    fan_raw = packet[6] & 0xFF
    
    return {
        "target_temp": target_temp,
        "room_temp": room_temp,
        "pipe_temp": pipe_temp,
        "mode": mode_raw,
        "fan_speed": fan_raw
    }

class FrameSyncStream:
    """
    스트림에서 바이트 밀림 현상 방지를 위한 슬라이딩 윈도우 기반 동기화 버퍼
    """
    def __init__(self, header_pattern: bytes):
        self.header_pattern = header_pattern
        self.buffer = bytearray()
        
    def feed(self, data: bytes) -> typing.List[bytes]:
        """
        스트림 데이터를 받아 16바이트 프레임으로 분리하여 반환합니다.
        """
        self.buffer.extend(data)
        valid_frames = []
        
        while len(self.buffer) >= PACKET_SIZE:
            # 헤더 탐색
            header_idx = self.buffer.find(self.header_pattern)
            
            if header_idx == -1:
                # 헤더가 없으면 헤더 길이보다 작은 남은 데이터만 유지하고 드롭
                self.buffer = self.buffer[-(len(self.header_pattern) - 1):] if len(self.header_pattern) > 1 else bytearray()
                break
                
            if header_idx > 0:
                # 헤더 이전 쓰레기 데이터 드롭
                self.buffer = self.buffer[header_idx:]
                
            if len(self.buffer) >= PACKET_SIZE:
                frame = bytes(self.buffer[:PACKET_SIZE])
                if validate_packet(frame):
                    valid_frames.append(frame)
                    self.buffer = self.buffer[PACKET_SIZE:]
                else:
                    # 유효하지 않으면 헤더 패턴 이후부터 다시 탐색
                    self.buffer = self.buffer[1:]
            else:
                # 패킷 크기가 다 차지 않았으므로 다음 데이터 대기
                break
                
        return valid_frames

def build_poll_packet(unit_id: int, header: int = 0x00) -> bytes:
    """
    실내기 상태 조회를 위한 16바이트 폴링 패킷을 생성하고 체크섬을 계산합니다.
    """
    packet = bytearray(PACKET_SIZE)
    packet[0] = header & 0xFF
    packet[1] = unit_id & 0xFF
    packet[15] = calculate_checksum(packet)
    return bytes(packet)

def build_control_packet(command: typing.Dict[str, typing.Any]) -> bytes:
    """
    실내기 제어를 위한 16바이트 패킷을 생성하고 체크섬을 계산합니다.
    """
    unit_id = command.get("id", 0)
    target_temp = command.get("target_temp", 24)
    clamped_temp = max(16, min(30, int(target_temp)))
    
    packet = bytearray(PACKET_SIZE)
    packet[0] = 0x00
    packet[1] = unit_id & 0xFF
    packet[2] = 0xFF  # 제어 실행 플래그
    packet[7] = (clamped_temp - 15) & 0x0F
    
    if "mode" in command and isinstance(command["mode"], int):
        packet[5] = command["mode"] & 0xFF
    if "fan_speed" in command and isinstance(command["fan_speed"], int):
        packet[6] = command["fan_speed"] & 0xFF
        
    packet[15] = calculate_checksum(packet)
    return bytes(packet)

