import typing

# 시리얼 포트 경로 (예: 라즈베리파이 USB-to-RS485)
SERIAL_PORT: str = "/dev/ttyUSB0"

# 통신 보레이트 (LGAP 물리 계층 규격: 4800 bps)
BAUDRATE: int = 4800

# 실내기 장치별 순차 폴링 사이의 미세 대기 시간 (초 단위)
POLL_INTERVAL: float = 1.0

# 에어컨 응답 대기 제한 시간 (150ms)
RX_TIMEOUT: float = 0.15

# 모니터링 및 제어 대상이 되는 실내기 고유 ID 리스트
TARGET_INDOOR_UNITS: typing.List[int] = [1, 2, 3, 4]
