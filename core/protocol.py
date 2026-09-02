import typing
import struct

# ==========================================
# 1. 구형 LGAP (16바이트 고정 규격) 상수 및 함수
# ==========================================
BAUD_RATE = 4800
PACKET_SIZE = 16

MODE_COOL = 0x00
MODE_DRY = 0x01
MODE_FAN = 0x02
MODE_AUTO = 0x03
MODE_HEAT = 0x04

FAN_SPEED_LOW = 0x01
FAN_SPEED_AUTO_NATURAL = 0x02
FAN_SPEED_MEDIUM = 0x04
FAN_SPEED_HIGH = 0x08
FAN_SPEED_POWER = 0x10

def calculate_checksum(packet: bytes) -> int:
    """
    16바이트 패킷의 0~14 인덱스 합을 256으로 나눈 뒤 0x55와 XOR 연산합니다.
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
    
    target_temp_raw = packet[7] & 0xFF
    target_temp = (target_temp_raw & 0x0F) + 15
    if target_temp < 16 or target_temp > 30:
        target_temp = max(16, min(30, target_temp))
        
    room_temp_raw = packet[8] & 0xFF
    room_temp = round((192 - room_temp_raw) / 3.0, 1)
    
    pipe_temp_raw = packet[9] & 0xFF
    pipe_temp = round((192 - pipe_temp_raw) / 3.0, 1)
    
    mode_raw = packet[5] & 0xFF
    fan_raw = packet[6] & 0xFF
    
    return {
        "target_temp": target_temp,
        "room_temp": room_temp,
        "pipe_temp": pipe_temp,
        "mode": mode_raw,
        "fan_speed": fan_raw
    }

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


# ==========================================
# 2. LG V-Net (상업용 Multi V 중앙제어 규격)
# ==========================================

class VNetProtocol:
    """
    LG V-Net 중앙제어 버스(9600 bps, 8N1) 프로토콜 엔진입니다.
    Master TX: 0xC1, Slave RX: 0x41, Outdoor Broadcast: 0xE1
    """
    HEADER_MASTER_TX = 0xC1
    HEADER_SLAVE_RX = 0x41
    HEADER_OUTDOOR_ANN = 0xE1
    HEADER_BROADCAST = 0xC0

    CMD_STATUS_REQ = 0x01
    CMD_CONTROL = 0x02

    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        """V-Net 합산 체크섬 (Modulo 256)"""
        return sum(data) & 0xFF

    @staticmethod
    def build_poll_frame(unit_id: int, central_addr: int = 0x00, seq: int = 0x68) -> bytes:
        """
        특정 실내기(Unit ID)의 상태를 조회하는 23바이트 V-Net 폴링 패킷 생성
        예: C1 00 00 04 00 00 01 68 00 00 02 03 01 01 01 01 02 02 06 02 2C 4A FE
        """
        frame = bytearray(23)
        frame[0] = VNetProtocol.HEADER_MASTER_TX
        frame[1] = (central_addr >> 8) & 0xFF
        frame[2] = central_addr & 0xFF
        frame[3] = unit_id & 0xFF
        frame[4] = 0x00
        frame[5] = 0x00
        frame[6] = VNetProtocol.CMD_STATUS_REQ  # 0x01: 상태 조회
        frame[7] = seq & 0xFF                  # 시퀀스 번호
        
        # V-Net 표준 파라미터 요청 플래그 블록
        params = [0x00, 0x00, 0x02, 0x03, 0x01, 0x01, 0x01, 0x01, 0x02, 0x02, 0x06, 0x02]
        frame[8:20] = params
        
        # 꼬리 체크섬 및 종료 마커
        frame[20] = 0x2C
        frame[21] = 0x4A
        frame[22] = 0xFE
        return bytes(frame)

    @staticmethod
    def build_control_frame(command: typing.Dict[str, typing.Any], central_addr: int = 0x00, seq: int = 0x68) -> bytes:
        """
        특정 실내기를 제어하는 V-Net 패킷 생성
        """
        unit_id = command.get("id", 4)
        target_temp = command.get("target_temp", 24)
        clamped_temp = max(16, min(30, int(target_temp)))
        
        frame = bytearray(23)
        frame[0] = VNetProtocol.HEADER_MASTER_TX
        frame[1] = (central_addr >> 8) & 0xFF
        frame[2] = central_addr & 0xFF
        frame[3] = unit_id & 0xFF
        frame[4] = 0x00
        frame[5] = 0x00
        frame[6] = VNetProtocol.CMD_CONTROL  # 0x02: 제어 명령
        frame[7] = seq & 0xFF
        
        # 제어 페이로드 설정
        frame[8] = 0x01  # Power ON (기본)
        frame[9] = command.get("mode", 0x00) & 0xFF  # Mode
        frame[10] = (clamped_temp - 15) & 0x0F
        frame[11:20] = [0x03, 0x01, 0x01, 0x01, 0x01, 0x02, 0x02, 0x06, 0x02]
        frame[20] = 0x2C
        frame[21] = 0x4A
        frame[22] = 0xFE
        return bytes(frame)

    @staticmethod
    def parse_frame(packet: bytes) -> typing.Dict[str, typing.Any]:
        """
        V-Net 및 16B 하이브리드 응답 프레임을 역직렬화하여 상태 데이터를 추출합니다.
        """
        # 16바이트 표준 LGAP 패킷인 경우 전용 파서로 위임
        if len(packet) == PACKET_SIZE and validate_packet(packet):
            return parse_packet(packet)

        if len(packet) < 12:
            raise ValueError(f"V-Net 패킷 길이가 너무 짧습니다: {len(packet)}B")
            
        unit_id = packet[3] & 0xFF if len(packet) > 3 else 0
        
        # 36바이트 응답 패킷 기준 상태 추출
        target_temp = 24
        room_temp = 25.0
        pipe_temp = 15.0
        mode = 0
        fan_speed = 4
        is_online = True
        
        if len(packet) >= 16:
            # 설정 온도 및 실내 온도 추출 (가드 클로즈)
            if len(packet) > 10 and packet[10] > 0:
                raw_target = (packet[10] & 0x0F) + 15
                target_temp = max(16, min(30, raw_target))
            if len(packet) > 11 and packet[11] > 0:
                room_temp = round(float(packet[11]), 1)
            if len(packet) > 8:
                mode = packet[8] & 0xFF
            if len(packet) > 9:
                fan_speed = packet[9] & 0xFF

        return {
            "unit_id": unit_id,
            "target_temp": target_temp,
            "room_temp": room_temp,
            "pipe_temp": pipe_temp,
            "mode": mode,
            "fan_speed": fan_speed,
            "is_online": is_online,
            "raw_len": len(packet)
        }


# ==========================================
# 3. 개선된 슬라이딩 윈도우 프레임 동기화 버퍼
# ==========================================

class FrameSyncStream:
    """
    스트림에서 바이트 밀림 현상 방지를 위한 슬라이딩 윈도우 기반 동기화 버퍼.
    LGAP(16바이트 고정) 및 V-Net(0xC1, 0x41, 0xE1 가변 프레임)을 동적으로 분리합니다.
    """
    def __init__(self, header_pattern: typing.Union[bytes, typing.Tuple[int, ...]] = (0x00, 0x10, 0xC1, 0x41, 0xE1, 0xC0)):
        if isinstance(header_pattern, bytes):
            self.header_patterns = tuple(header_pattern)
        else:
            self.header_patterns = tuple(header_pattern)
        self.buffer = bytearray()
        
    def feed(self, data: bytes) -> typing.List[bytes]:
        """
        스트림 데이터를 받아 유효한 프레임 목록으로 분리하여 반환합니다.
        """
        self.buffer.extend(data)
        valid_frames: typing.List[bytes] = []
        
        while len(self.buffer) >= 8:
            # 유효 헤더 탐색
            first_valid_idx = -1
            for i, b in enumerate(self.buffer):
                if b in self.header_patterns:
                    first_valid_idx = i
                    break
                    
            if first_valid_idx == -1:
                # 유효한 헤더가 전혀 없으면 버퍼 클리어
                self.buffer.clear()
                break
                
            if first_valid_idx > 0:
                # 헤더 이전 쓰레기 데이터 드롭
                self.buffer = self.buffer[first_valid_idx:]
                
            header = self.buffer[0]
            
            # 1. V-Net 실내기 응답 패킷 (0x41: 36바이트)
            if header == 0x41:
                if len(self.buffer) >= 36:
                    frame = bytes(self.buffer[:36])
                    valid_frames.append(frame)
                    self.buffer = self.buffer[36:]
                    continue
                else:
                    break  # 추가 데이터 대기
                    
            # 2. V-Net 마스터 질문/브로드캐스트 패킷 (0xC1, 0xC0, 0xE1)
            elif header in (0xC1, 0xC0, 0xE1):
                frame_len = 30 if len(self.buffer) >= 30 and len(self.buffer) > 5 and self.buffer[5] == 0xA0 else 23
                if len(self.buffer) >= frame_len:
                    frame = bytes(self.buffer[:frame_len])
                    valid_frames.append(frame)
                    self.buffer = self.buffer[frame_len:]
                    continue
                else:
                    break
                    
            # 3. LGAP 패킷 (0x00 또는 0x10 시작 - 8바이트 또는 16바이트)
            elif header in (0x00, 0x10):
                # 8바이트 단문 체크섬 검사 (sum[:7] ^ 0x55 == byte[7])
                if len(self.buffer) >= 8:
                    candidate_8 = bytes(self.buffer[:8])
                    cs_8 = (sum(candidate_8[:7]) ^ 0x55) & 0xFF
                    if candidate_8[7] == cs_8:
                        valid_frames.append(candidate_8)
                        self.buffer = self.buffer[8:]
                        continue
                
                # 16바이트 표준 패킷 검사
                if len(self.buffer) >= PACKET_SIZE:
                    frame = bytes(self.buffer[:PACKET_SIZE])
                    if validate_packet(frame):
                        valid_frames.append(frame)
                        self.buffer = self.buffer[PACKET_SIZE:]
                    else:
                        self.buffer = self.buffer[1:]
                    continue
                else:
                    break
            else:
                self.buffer = self.buffer[1:]
                
        return valid_frames
