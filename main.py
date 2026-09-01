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
    def __init__(self, use_mock: bool = True) -> None:
        self.state_manager = StateManager()
        
        # 의존성 주입: 하드웨어 결선 전이므로 MockSerial 사용
        serial_class = MockSerial if use_mock else __import__('serial').Serial
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
    ##################################
    ### 실 환경 배포 시 False 로 전환 ###
    ##################################
    controller = DaemonController(use_mock=True) 
    
    # 시그널 핸들러 등록 (Graceful Shutdown)
    signal.signal(signal.SIGINT, controller.request_shutdown)
    signal.signal(signal.SIGTERM, controller.request_shutdown)
    
    controller.start()
