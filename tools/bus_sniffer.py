import os
import sys

# 프로젝트 루트 디렉토리를 sys.path에 추가 (상위 모듈 임포트 보장)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import time
import argparse
import logging
import typing
import serial

import config

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("BusSniffer")

class BusSniffer:
    """
    RS-485 CEN 통신 버스 상의 원시 바이너리 트래픽을 실시간으로 캡처하고
    V-Net (0xC1, 0x41, 0xE1) 프레임을 분해하는 진단 도구입니다.
    """
    def __init__(self, port: str = config.SERIAL_PORT, baudrate: int = 9600) -> None:
        self.port: str = port
        self.baudrate: int = baudrate
        self.serial_conn: typing.Optional[serial.Serial] = None
        self._running: bool = False

    def open(self) -> bool:
        try:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1
            )
            logger.info(f"스니퍼 포트 오픈 성공: {self.port} @ {self.baudrate} bps (8N1)")
            return True
        except Exception as e:
            logger.error(f"포트 오픈 실패 ({self.port} @ {self.baudrate}): {e}")
            return False

    def close(self) -> None:
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info("스니퍼 포트를 닫았습니다.")

    def analyze_vnet_frame(self, frame: bytes) -> None:
        """
        0xC1, 0x41, 0xE1 등 V-Net 패킷 구조를 분해하여 분석 정보를 로깅합니다.
        """
        if len(frame) < 4:
            return
            
        header = frame[0]
        header_desc = {
            0xC1: "마스터 제어/질문 (V-Net Master TX)",
            0x41: "실내기 응답 (V-Net Slave RX)",
            0xE1: "실외기 주기 통신 (V-Net Outdoor Announce)",
            0xC0: "V-Net 브로드캐스트"
        }.get(header, f"알 수 없는 헤더 (0x{header:02X})")
        
        target_unit = frame[3] if len(frame) > 3 else 0
        cmd_type = frame[6] if len(frame) > 6 else 0
        
        logger.info(f"  └─ [V-Net 파싱] 헤더: {header_desc} | 대상 Unit ID: #{target_unit} | 명령 코드: 0x{cmd_type:02X} | 총 길이: {len(frame)}B")

    def sniff_stream(self, duration_sec: typing.Optional[float] = None) -> None:
        """
        포트로부터 수신되는 바이트 스트림을 실시간 캡처하여 헥스 덤프합니다.
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            logger.error("시리얼 포트가 열려있지 않습니다.")
            return

        self._running = True
        logger.info(f"[{self.port} @ {self.baudrate} bps] 실시간 버스 패킷 감청(Sniffing) 시작... (종료: Ctrl+C)")
        
        start_time = time.time()
        rx_buffer = bytearray()
        last_rx_time = time.time()

        try:
            while self._running:
                if duration_sec and (time.time() - start_time) > duration_sec:
                    break

                in_waiting = self.serial_conn.in_waiting
                if in_waiting > 0:
                    chunk = self.serial_conn.read(in_waiting)
                    rx_buffer.extend(chunk)
                    last_rx_time = time.time()
                    time.sleep(0.02)
                    continue

                # 패킷 프레임 종료 판별 (20ms 이상 무응답 시 한 덩어리의 패킷으로 간주)
                if len(rx_buffer) > 0 and (time.time() - last_rx_time) > 0.05:
                    raw_bytes = bytes(rx_buffer)
                    hex_dump = raw_bytes.hex(' ').upper()
                    logger.info(f"[RX {len(raw_bytes):02d}B] {hex_dump}")
                    
                    # 0xC1, 0x41, 0xE1 등 V-Net 패킷인 경우 분해
                    if raw_bytes[0] in (0xC1, 0x41, 0xE1, 0xC0):
                        self.analyze_vnet_frame(raw_bytes)
                        
                    rx_buffer.clear()

                time.sleep(0.01)

        except KeyboardInterrupt:
            logger.info("사용자에 의해 스니핑이 중지되었습니다.")
        finally:
            self._running = False

    def scan_baudrates(self, baudrates: typing.List[int] = [9600, 4800, 19200], scan_time_sec: float = 5.0) -> None:
        """
        다양한 통신 속도를 순차적으로 스캔하여 데이터가 유입되는 속도를 탐색합니다.
        """
        logger.info(f"=== 통신 속도 자동 스캔 시작 ({baudrates}) ===")
        for baud in baudrates:
            self.baudrate = baud
            logger.info(f"--> [{baud} bps] 수신 신호 대기 중 ({scan_time_sec}초)...")
            if not self.open():
                continue
                
            self.sniff_stream(duration_sec=scan_time_sec)
            self.close()
            time.sleep(0.5)

def main() -> None:
    parser = argparse.ArgumentParser(description="LG V-Net RS-485 Bus Sniffer & Diagnostic Tool")
    parser.add_argument("-p", "--port", type=str, default=config.SERIAL_PORT, help="시리얼 포트 (예: COM6, /dev/ttyUSB0)")
    parser.add_argument("-b", "--baud", type=int, default=config.BAUDRATE, help="통신 보레이트 (기본: 9600)")
    parser.add_argument("--scan", action="store_true", help="9600 / 4800 / 19200 bps 순차 자동 스캔")
    
    args = parser.parse_args()
    sniffer = BusSniffer(port=args.port, baudrate=args.baud)
    
    if args.scan:
        sniffer.scan_baudrates()
    else:
        if sniffer.open():
            sniffer.sniff_stream()
            sniffer.close()

if __name__ == "__main__":
    main()
