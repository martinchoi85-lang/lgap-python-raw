import threading
import queue
import time
import serial
import logging
import typing

import config
from core.protocol import FrameSyncStream, PACKET_SIZE, parse_packet
from core.state import StateManager

class LgapEngine:
    def __init__(self, state_manager: typing.Optional[StateManager] = None, serial_class: typing.Any = serial.Serial) -> None:
        self.serial_lock: threading.Lock = threading.Lock()
        self.command_queue: queue.Queue[typing.Dict[str, typing.Any]] = queue.Queue()
        self.serial_conn: typing.Any = None
        self._running: bool = False
        self._poll_index: int = 0
        self.state_manager: typing.Optional[StateManager] = state_manager
        self.serial_class: typing.Any = serial_class
        
    def connect_serial(self) -> bool:
        """시리얼 포트 연결 및 초기화"""
        try:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
                
            self.serial_conn = self.serial_class(
                port=config.SERIAL_PORT,
                baudrate=config.BAUDRATE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=config.RX_TIMEOUT
            )
            logging.info(f"시리얼 포트 연결 성공: {config.SERIAL_PORT}")
            return True
        except Exception as e:
            logging.error(f"시리얼 연결 실패 ({config.SERIAL_PORT}): {e}")
            self.serial_conn = None
            return False

    def _execute_transaction(self, tx_packet: bytes) -> typing.Optional[bytes]:
        if not self.serial_conn or not self.serial_conn.is_open:
            logging.error("시리얼 포트가 열려있지 않아 트랜잭션을 실행할 수 없습니다.")
            return None

        with self.serial_lock:
            try:
                logging.info(f"[POLL TX] {tx_packet.hex(' ')}")
                self.serial_conn.write(tx_packet)
                self.serial_conn.flush()
                time.sleep(0.05)
                
                sync_stream = FrameSyncStream(header_pattern=b'\x00') 
                start_time = time.time()
                while (time.time() - start_time) <= config.RX_TIMEOUT:
                    if self.serial_conn.in_waiting > 0:
                        raw_data = self.serial_conn.read(self.serial_conn.in_waiting)
                        valid_frames = sync_stream.feed(raw_data)
                        
                        if valid_frames:
                            rx_frame = valid_frames[0]
                            logging.info(f"[POLL RX] {rx_frame.hex(' ')}")
                            return rx_frame
                            
                    time.sleep(0.01)
                    
                logging.warning(f"트랜잭션 타임아웃. 응답 없음. (TX: {tx_packet.hex(' ')})")
                return None
                
            except Exception as e:
                logging.error(f"트랜잭션 도중 시리얼 오류 발생: {e} | TX: {tx_packet.hex(' ')}")
                self.serial_conn.close()
                return None

    def start_engine(self) -> None:
        self._running = True
        engine_thread = threading.Thread(target=self._engine_loop, daemon=True)
        engine_thread.start()
        logging.info("LGAP Engine 스케줄러가 시작되었습니다.")

    def stop_engine(self) -> None:
        self._running = False
        if self.serial_conn and getattr(self.serial_conn, 'is_open', False):
            self.serial_conn.close()
        logging.info("LGAP Engine 스케줄러가 중지되었습니다.")

    def _build_poll_packet(self, unit_id: int) -> bytes:
        return bytes([0x00, unit_id] + [0x00] * 14)

    def _build_control_packet(self, command: typing.Dict[str, typing.Any]) -> bytes:
        unit_id = command.get("id", 0)
        target_temp = command.get("target_temp", 24)
        return bytes([0x00, unit_id, 0xFF, 0x00, 0x00, 0x00, 0x00, (target_temp - 15) & 0x0F] + [0x00] * 8)

    def _engine_loop(self) -> None:
        while self._running:
            if not self.serial_conn or not self.serial_conn.is_open:
                logging.warning("시리얼 연결 유실 감지. 재연결 시도 중...")
                if not self.connect_serial():
                    time.sleep(2.0)
                    continue

            if not self.command_queue.empty():
                try:
                    command = self.command_queue.get_nowait()
                    tx_packet = self._build_control_packet(command)
                    logging.info(f"[CONTROL TX] 제어 명령 우선 전송: {command}")
                    
                    response = self._execute_transaction(tx_packet)
                    if response:
                        logging.info(f"[CONTROL RX] 제어 완료 응답 수신: {response.hex(' ')}")
                        # 응답 성공 시 상태 갱신
                        if self.state_manager:
                            try:
                                parsed = parse_packet(response)
                                self.state_manager.update_state(command.get("id", 0), parsed)
                            except ValueError as e:
                                logging.error(f"제어 응답 파싱 실패: {e}")
                except queue.Empty:
                    pass
            else:
                if not config.TARGET_INDOOR_UNITS:
                    time.sleep(config.POLL_INTERVAL)
                    continue
                    
                target_id = config.TARGET_INDOOR_UNITS[self._poll_index]
                tx_packet = self._build_poll_packet(target_id)
                self._poll_index = (self._poll_index + 1) % len(config.TARGET_INDOOR_UNITS)
                
                response = self._execute_transaction(tx_packet)
                if response:
                    if self.state_manager:
                        try:
                            parsed = parse_packet(response)
                            self.state_manager.update_state(target_id, parsed)
                            logging.info(f"[STATE] Unit {target_id} -> Target: {parsed['target_temp']}°C, Room: {parsed['room_temp']}°C, Pipe: {parsed['pipe_temp']}°C")
                        except ValueError as e:
                            logging.error(f"폴링 응답 파싱 실패: {e}")
            
            time.sleep(config.POLL_INTERVAL)
