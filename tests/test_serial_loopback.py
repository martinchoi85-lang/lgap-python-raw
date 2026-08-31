import serial
import threading
import time
import typing
import sys

class SerialLoopbackTester:
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 4800) -> None:
        self.port: str = port
        self.baudrate: int = baudrate
        self.lock: threading.Lock = threading.Lock()
        self.serial_conn: typing.Optional[serial.Serial] = None

    def open_port(self) -> bool:
        """
        시리얼 포트를 설정(8N1)과 함께 오픈합니다.
        """
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0
            )
            print(f"[INFO] 시리얼 포트 연결 성공: {self.port} ({self.baudrate} bps, 8N1)")
            return True
        except serial.SerialException as e:
            print(f"[ERROR] 시리얼 포트 열기 실패: {e}")
            return False

    def close_port(self) -> None:
        """
        열려있는 시리얼 포트를 안전하게 닫습니다.
        """
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("[INFO] 시리얼 포트를 닫았습니다.")

    def test_loopback(self, test_data: bytes) -> bool:
        """
        주어진 데이터를 송신하고 루프백을 통해 동일한 데이터를 수신하는지 검증합니다.
        반이중 통신의 동시성 충돌 방지를 위해 Lock을 적용합니다.
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            print("[ERROR] 포트가 열려있지 않아 송수신을 할 수 없습니다.")
            return False

        with self.lock:
            try:
                # 1. 데이터 송신
                self.serial_conn.write(test_data)
                
                # 2. 송신 완료 대기 (Flush 버퍼)
                self.serial_conn.flush()
                
                # 3. 하드웨어 타이밍 마진 (반이중 통신 송수신 전환 딜레이 시뮬레이션)
                time.sleep(0.05) 
                
                # 4. 데이터 수신 (루프백 환경이므로 송신한 만큼 수신을 기대함)
                bytes_to_read: int = max(self.serial_conn.in_waiting, len(test_data))
                received_data: bytes = self.serial_conn.read(bytes_to_read)
                
                print(f"[TX] 송신 데이터: {test_data.hex().upper()}")
                print(f"[RX] 수신 데이터: {received_data.hex().upper()}")
                
                if test_data == received_data:
                    print("[SUCCESS] 루프백 테스트 정상 통과!")
                    return True
                else:
                    print("[FAIL] 송수신 데이터 불일치. 연결 상태를 확인하세요.")
                    return False
                    
            except serial.SerialException as e:
                print(f"[ERROR] 루프백 통신 진행 중 물리적 오류 발생: {e}")
                return False

if __name__ == "__main__":
    # 실행 시 간단히 인자를 받거나 기본값을 사용
    target_port = "/dev/ttyUSB0"
    if len(sys.argv) > 1:
        target_port = sys.argv[1]
    else:
        user_input = input(f"테스트할 포트 경로를 입력하세요 (기본값: {target_port}): ").strip()
        if user_input:
            target_port = user_input
            
    tester = SerialLoopbackTester(port=target_port)
    
    if tester.open_port():
        # 임의의 16바이트 더미 패킷 생성
        dummy_packet = bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 
                              0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00])
        tester.test_loopback(dummy_packet)
        tester.close_port()
