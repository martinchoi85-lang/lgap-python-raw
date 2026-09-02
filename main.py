import sys
import time
import signal
import logging
import typing

import config
from core.state import StateManager
from core.polling import LgapEngine
from tests.mock_aircon import MockSerial
from api.interface import ApiInterfaceServer

# 표준 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("LGAP-Daemon")

class DaemonController:
    def __init__(self, use_mock: typing.Optional[bool] = None) -> None:
        self.state_manager = StateManager()
        
        # Mock 여부 결정 (CLI/인자 우선, 없으면 config.USE_MOCK 사용)
        is_mock = use_mock if use_mock is not None else getattr(config, 'USE_MOCK', False)
        
        if is_mock:
            logger.warning("=" * 60)
            logger.warning("[WARNING] 현재 가상 에어컨 MockSerial 모드로 동작 중입니다!")
            logger.warning("실제 RS-485 하드웨어 통신을 하려면 use_mock=False 또는 config.USE_MOCK=False 로 설정하세요.")
            logger.warning("=" * 60)
            serial_class = MockSerial
        else:
            logger.info("=" * 60)
            logger.info(f"[REAL HARDWARE] 실제 물리 시리얼 연결 모드 ({config.SERIAL_PORT} @ {config.BAUDRATE} bps, 모드: {config.PROTOCOL_MODE})")
            logger.info("=" * 60)
            serial_class = __import__('serial').Serial
            
        self.engine = LgapEngine(state_manager=self.state_manager, serial_class=serial_class)
        self.api_server = ApiInterfaceServer(state_manager=self.state_manager, engine=self.engine, port=8080)
        self._shutdown_requested = False

    def start(self) -> None:
        logger.info("LGAP Daemon 초기화 중...")
        
        # 1. 시리얼/가상엔진 연결
        if not self.engine.connect_serial():
            logger.error("시리얼 포트 연결 실패. 엔진을 시작할 수 없습니다.")
            sys.exit(1)
            
        # 2. 엔진 스레드 가동
        self.engine.start_engine()
        
        # 3. API 서버 가동
        self.api_server.start()
        
        logger.info("LGAP Daemon이 정상적으로 시작되었습니다. (SIGINT / SIGTERM 대기 중)")
        
        # 메인 스레드는 시그널 대기
        while not self._shutdown_requested:
            time.sleep(1.0)
            
        self._cleanup()

    def request_shutdown(self, signum: int, frame: typing.Any) -> None:
        logger.info(f"종료 시그널 수신 ({signum}). Graceful Shutdown 진행 중...")
        self._shutdown_requested = True

    def _cleanup(self) -> None:
        logger.info("정리(Cleanup) 시퀀스 시작...")
        self.api_server.stop()
        self.engine.stop_engine()
        logger.info("LGAP Daemon 종료 완료.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LGAP & V-Net Real Serial Daemon")
    parser.add_argument("--mock", action="store_true", help="가상 에어컨 MockSerial 모드로 실행")
    parser.add_argument("--port", type=str, default=None, help="시리얼 포트 직접 지정 (예: COM6, /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=None, help="보레이트 직접 지정 (예: 9600, 4800)")
    parser.add_argument("--mode", type=str, choices=["LGAP", "VNET", "AUTO_SNIFF"], default=None, help="프로토콜 모드")
    args = parser.parse_args()

    if args.port:
        config.SERIAL_PORT = args.port
    if args.baud:
        config.BAUDRATE = args.baud
    if args.mode:
        config.PROTOCOL_MODE = args.mode

    use_mock_flag = True if args.mock else getattr(config, 'USE_MOCK', False)
    controller = DaemonController(use_mock=use_mock_flag) 
    
    # 시그널 핸들러 등록 (Graceful Shutdown)
    signal.signal(signal.SIGINT, controller.request_shutdown)
    signal.signal(signal.SIGTERM, controller.request_shutdown)
    
    controller.start()
