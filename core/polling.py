import threading
import queue
import time
import serial
import logging
import typing

import config
from core.protocol import (
    FrameSyncStream,
    PACKET_SIZE,
    parse_packet,
    build_poll_packet,
    build_control_packet
)
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
                logging.info(f"[TX] {tx_packet.hex(' ')}")
                self.serial_conn.write(tx_packet)
                self.serial_conn.flush()
                time.sleep(0.05)
                
                # 수신 대기
                sync_stream = FrameSyncStream(header_pattern=bytes([getattr(config, 'POLL_HEADER', 0x00)])) 
                start_time = time.time()
                total_raw_bytes = bytearray()
                
                while (time.time() - start_time) <= config.RX_TIMEOUT:
                    in_waiting = self.serial_conn.in_waiting
                    if in_waiting > 0:
                        raw_data = self.serial_conn.read(in_waiting)
                        total_raw_bytes.extend(raw_data)
                        logging.info(f"[RAW RX] {len(raw_data)}바이트 수신됨 (누적 {len(total_raw_bytes)}B): {raw_data.hex(' ')}")
                        
                        valid_frames = sync_stream.feed(raw_data)
                        if valid_frames:
                            rx_frame = valid_frames[0]
                            logging.info(f"[VALID RX] 정상 16바이트 패킷 파싱 성공: {rx_frame.hex(' ')}")
                            return rx_frame
                            
                    time.sleep(0.01)
                
                if total_raw_bytes:
                    logging.info(f"[TRANSACTION SUCCESS] 총 {len(total_raw_bytes)}바이트 응답 수신 완료: {bytes(total_raw_bytes).hex(' ')}")
                    return bytes(total_raw_bytes)
                else:
                    logging.warning(f"트랜잭션 타임아웃. 시리얼 수신 데이터 0바이트 (TX: {tx_packet.hex(' ')})")
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
                    tx_packet = build_control_packet(command)
                    logging.info(f"[CONTROL TX] 제어 명령 우선 전송: {command} (Hex: {tx_packet.hex(' ')})")
                    
                    response = self._execute_transaction(tx_packet)
                    if response:
                        logging.info(f"[CONTROL RX] 제어 완료 응답 수신: {response.hex(' ')}")
                        if self.state_manager:
                            try:
                                parsed = parse_packet(response)
                                self.state_manager.update_state(command.get("id", 0), parsed)
                            except ValueError as e:
                                logging.error(f"제어 응답 파싱 실패: {e}")
                except queue.Empty:
                    pass
            else:
                # [현장 실측 스니퍼 패킷 순차 테스트 풀]
                field_packets = [
                    ("[0/5] 마스터 초기화 브로드캐스트", bytes.fromhex("C1 00 00 00 00 A0 01 C8 04 04 A6 E0 05 05 E6 E8 88 48 44 05 05 84 80 80 E8 05 A6 80 8A 0D")),
                    ("[1/5] 4번 실내기 폴링 (Seq 68)", bytes.fromhex("C1 00 00 04 00 00 01 68 00 00 02 03 01 01 01 01 02 02 06 02 2C 4A FE")),
                    ("[2/5] 5번 실내기 폴링 (Seq 6A)", bytes.fromhex("C1 00 00 05 00 00 01 6A 00 00 02 03 01 01 01 01 02 02 06 02 8E 8B F1")),
                    ("[3/5] 전체 어나운스 리프레시", bytes.fromhex("C1 00 00 00 00 80 01 ED 04 04 A7 E0 05 05 E6 E8 88 48 04 A2 A9 80 24 04 04 A7 E8 05 E0 8D F6")),
                    ("[4/5] 4번 실내기 폴링 (Seq 69)", bytes.fromhex("C1 00 00 04 00 00 01 69 00 00 02 03 01 01 01 01 02 02 06 02 00 CB FB")),
                    ("[5/5] 5번 실내기 폴링 (Seq 6A-2)", bytes.fromhex("C1 00 00 05 00 00 01 6A 00 00 02 03 01 01 01 01 02 02 06 02 00 28 FA")),
                ]

                pkt_desc, tx_packet = field_packets[self._poll_index % len(field_packets)]
                self._poll_index = (self._poll_index + 1) % len(field_packets)
                
                logging.info(f"==> {pkt_desc} 송신 시작...")
                response = self._execute_transaction(tx_packet)
                if response:
                    logging.info(f"[SUCCESS] {pkt_desc} 응답 수신 성공! (총 {len(response)}바이트): {response.hex(' ')}")
            
            time.sleep(config.POLL_INTERVAL)

