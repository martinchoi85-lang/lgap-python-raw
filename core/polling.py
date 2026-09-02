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
    build_control_packet,
    VNetProtocol
)
from core.state import StateManager

class LgapEngine:
    def __init__(self, state_manager: typing.Optional[StateManager] = None, serial_class: typing.Any = serial.Serial) -> None:
        self.serial_lock: threading.Lock = threading.Lock()
        self.command_queue: queue.Queue[typing.Dict[str, typing.Any]] = queue.Queue()
        self.serial_conn: typing.Any = None
        self._running: bool = False
        self._poll_index: int = 0
        self._vnet_seq: int = 0x68  # V-Net 시퀀스 카운터
        self.state_manager: typing.Optional[StateManager] = state_manager
        self.serial_class: typing.Any = serial_class
        
    def connect_serial(self) -> bool:
        """시리얼 포트 연결 및 초기화 (Half-Duplex 8N1)"""
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
            logging.info(f"시리얼 포트 연결 성공: {config.SERIAL_PORT} @ {config.BAUDRATE} bps (모드: {config.PROTOCOL_MODE})")
            return True
        except Exception as e:
            logging.error(f"시리얼 연결 실패 ({config.SERIAL_PORT}): {e}")
            self.serial_conn = None
            return False

    def _execute_transaction(self, tx_packet: bytes) -> typing.Optional[bytes]:
        """Half-Duplex Mutex Lock 보호 하에서 TX 송신 및 RX 응답 수신 트랜잭션 수행"""
        if not self.serial_conn or not self.serial_conn.is_open:
            logging.error("시리얼 포트가 열려있지 않아 트랜잭션을 실행할 수 없습니다.")
            return None

        with self.serial_lock:
            try:
                logging.info(f"[TX {len(tx_packet):02d}B] {tx_packet.hex(' ')}")
                self.serial_conn.write(tx_packet)
                self.serial_conn.flush()
                time.sleep(0.04)  # Half-duplex 트랜시버 전환 마진
                
                # 수신 대기 및 슬라이딩 윈도우 프레이밍
                sync_stream = FrameSyncStream() 
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
                            logging.info(f"[VALID RX {len(rx_frame):02d}B] 정상 프레임 수신: {rx_frame.hex(' ')}")
                            return rx_frame
                            
                    time.sleep(0.01)
                
                if total_raw_bytes:
                    logging.info(f"[TRANSACTION RAW] 수신 완료 ({len(total_raw_bytes)}B): {bytes(total_raw_bytes).hex(' ')}")
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
        logging.info(f"LGAP/V-Net Engine 스케줄러가 시작되었습니다. (모드: {config.PROTOCOL_MODE})")

    def stop_engine(self) -> None:
        self._running = False
        if self.serial_conn and getattr(self.serial_conn, 'is_open', False):
            self.serial_conn.close()
        logging.info("LGAP/V-Net Engine 스케줄러가 중지되었습니다.")

    def _engine_loop(self) -> None:
        mode = getattr(config, 'PROTOCOL_MODE', 'VNET').upper()
        
        while self._running:
            if not self.serial_conn or not self.serial_conn.is_open:
                logging.warning("시리얼 연결 유실 감지. 재연결 시도 중...")
                if not self.connect_serial():
                    time.sleep(2.0)
                    continue

            # 1. 외부 제어 명령 큐 우선 처리 (Preemption)
            if not self.command_queue.empty():
                try:
                    command = self.command_queue.get_nowait()
                    tx_packet = build_control_packet(command)

                    logging.info(f"[CONTROL TX] 제어 명령 전송: {command} (Hex: {tx_packet.hex(' ')})")
                    response = self._execute_transaction(tx_packet)
                    if response:
                        logging.info(f"[CONTROL RX] 제어 완료 응답: {response.hex(' ')}")
                        if self.state_manager:
                            try:
                                parsed = parse_packet(response) if (len(response) == PACKET_SIZE and validate_packet(response)) else VNetProtocol.parse_frame(response)
                                target_id = parsed.get("unit_id", command.get("id", 0))
                                self.state_manager.update_state(target_id, parsed)
                            except Exception as e:
                                logging.error(f"제어 응답 파싱 실패: {e}")
                except queue.Empty:
                    pass

            # 2. 주기적 상태 폴링 루프
            else:
                if mode == "AUTO_SNIFF":
                    # 패시브 감청 모드 (TX 송신 없이 수신 버퍼 캡처)
                    with self.serial_lock:
                        if self.serial_conn.in_waiting > 0:
                            raw = self.serial_conn.read(self.serial_conn.in_waiting)
                            logging.info(f"[SNIFF RX] {len(raw)}B: {raw.hex(' ')}")
                    time.sleep(0.1)
                    continue

                # [검증된 8바이트 폴링 패킷: 00 00 A0 00 00 00 08 FD]
                poll_hex = getattr(config, 'POLL_TX_HEX', '00 00 A0 00 00 00 08 FD')
                tx_packet = bytes.fromhex(poll_hex)
                
                response = self._execute_transaction(tx_packet)
                if response and self.state_manager:
                    try:
                        parsed = VNetProtocol.parse_frame(response)
                        actual_unit = parsed.get("unit_id", 3)
                        self.state_manager.update_state(actual_unit, parsed)
                        logging.info(f"[STATE] Unit #{actual_unit} -> Target: {parsed['target_temp']}°C, Room: {parsed['room_temp']}°C, Pipe: {parsed['pipe_temp']}°C, Mode: {parsed['mode']}")
                    except Exception as e:
                        logging.debug(f"응답 데이터 파싱 실패: {e}")
            
            time.sleep(config.POLL_INTERVAL)
