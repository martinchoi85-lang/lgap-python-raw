import typing
import queue

class MockSerial:
    """실제 하드웨어 없이 시리얼 포트를 흉내내는 가상 에어컨 시뮬레이터"""
    def __init__(self, port: str, baudrate: int, **kwargs: typing.Any) -> None:
        self.port: str = port
        self.baudrate: int = baudrate
        self.is_open: bool = True
        self._rx_buffer: queue.Queue[bytes] = queue.Queue()
        self._in_waiting: int = 0
        
        # 가상 에어컨 상태 (id 1, 2, 3, 4 초기화)
        self.mock_states: typing.Dict[int, typing.Dict[str, typing.Any]] = {
            1: {"target": 24, "room": 26.0, "pipe": 15.0, "mode": 0x00, "fan": 0x04},
            2: {"target": 22, "room": 22.0, "pipe": 10.0, "mode": 0x00, "fan": 0x08},
            3: {"target": 26, "room": 25.5, "pipe": 18.0, "mode": 0x03, "fan": 0x02},
            4: {"target": 18, "room": 20.0, "pipe": 8.0, "mode": 0x00, "fan": 0x10},
        }

    def close(self) -> None:
        self.is_open = False

    def flush(self) -> None:
        pass

    @property
    def in_waiting(self) -> int:
        return self._in_waiting

    def write(self, data: bytes) -> int:
        if not self.is_open:
            raise Exception("Port is closed")
            
        if len(data) >= 2:
            unit_id = data[1]
            if unit_id in self.mock_states:
                # 제어 명령 수신 시 가상 상태 갱신 (간이 시뮬레이션)
                # 데이터 7번째 바이트에 타겟 온도가 있다고 가정하고 업데이트
                if len(data) >= 16 and data[2] == 0xFF: 
                    target_temp_raw = data[7] & 0x0F
                    self.mock_states[unit_id]["target"] = target_temp_raw + 15
                    
                response = self._generate_response(unit_id)
                self._rx_buffer.put(response)
                self._in_waiting += len(response)
                
        return len(data)

    def read(self, size: int = 1) -> bytes:
        if not self.is_open:
            raise Exception("Port is closed")
            
        result = bytearray()
        while size > 0 and not self._rx_buffer.empty():
            chunk = self._rx_buffer.get_nowait()
            if len(chunk) <= size:
                result.extend(chunk)
                size -= len(chunk)
                self._in_waiting -= len(chunk)
            else:
                result.extend(chunk[:size])
                remain = chunk[size:]
                self._rx_buffer.put(remain)
                self._in_waiting -= size
                size = 0
                
        return bytes(result)

    def _generate_response(self, unit_id: int) -> bytes:
        state = self.mock_states[unit_id]
        
        packet = bytearray(16)
        packet[0] = 0x00  # 헤더
        packet[1] = unit_id & 0xFF
        packet[5] = state["mode"] & 0xFF
        packet[6] = state["fan"] & 0xFF
        
        # 설정 온도 역산
        packet[7] = (state["target"] - 15) & 0x0F
        
        # 실내 온도 및 배관 온도 역산
        packet[8] = int(192 - (state["room"] * 3)) & 0xFF
        packet[9] = int(192 - (state["pipe"] * 3)) & 0xFF
        
        # 체크섬 생성
        payload_sum = sum(packet[:15]) % 256
        packet[15] = (payload_sum ^ 0x55) & 0xFF
        
        return bytes(packet)
