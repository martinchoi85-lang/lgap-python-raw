import typing

# 가상 에어컨 Mock 모드 여부 (실제 하드웨어 연결 시 반드시 False)
USE_MOCK: bool = False

# 시리얼 포트 경로 (Windows: "COM6", Linux: "/dev/ttyUSB0")
SERIAL_PORT: str = "COM6"

# 통신 보레이트 (LG V-Net: 9600 bps, 구형 LGAP: 4800 bps)
BAUDRATE: int = 9600

# 프로토콜 동작 모드 ("VNET" | "LGAP" | "AUTO_SNIFF")
PROTOCOL_MODE: str = "LGAP"

# V-Net 마스터(중앙제어기) 고유 주소 (기본값: 0x00)
VNET_CENTRAL_ADDR: int = 0x00

# V-Net 모니터링 및 제어 대상 실내기 주소 리스트 (예: 4번, 5번 실내기)
VNET_TARGET_UNITS: typing.List[int] = [4, 5]

# 구형 LGAP 모니터링 대상 실내기 리스트 (PROTOCOL_MODE == 'LGAP' 시 사용)
TARGET_INDOOR_UNITS: typing.List[int] = [1, 2, 3, 4]

# 실내기 장치별 순차 폴링 간격 (초 단위)
POLL_INTERVAL: float = 1.0

# 에어컨 응답 대기 제한 시간 (초 단위, 9600bps 기준 0.3~0.5s 권장)
RX_TIMEOUT: float = 0.5

# 구형 LGAP 폴링 헤더 (기본: 0x00)
POLL_HEADER: int = 0x00
