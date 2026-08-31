---
trigger: model_decision
description: 본 프로젝트의 코드를 생성, 수정 및 리팩토링할 때 예외 없이 100% 준수해야 하는 강제 규칙 가이드
---

# AI Code Generation Guidelines for python-raw-lgap-daemon

## 1. 기본 스타일 규칙
- **언어 사양**: Python 3.10 이상 문법을 준수합니다.
- **타입 힌팅**: 모든 함수의 매개변수와 반환값에는 엄격한 타입 힌팅을 적용합니다. (예: `def calculate_checksum(data: bytes) -> int:`)
- **외부 종속성 배제**: 특수한 사유가 없는 한 외부 라이브러리는 `pyserial`로 한정하며, 가급적 파이썬 표준 라이브러리(`threading`, `queue`, `socket`, `logging` 등)만을 사용하여 가볍고 순수한 코드를 지향합니다.

## 2. LGAP 시리얼 통신 특화 가이드

### 2.1 패킷 16바이트 정합성 및 프레이밍
- RS-485 버스는 언제나 불특정 바이트 노이즈가 유입될 수 있습니다. 단순 `read(16)`를 수행할 경우 프레임 싱크가 뒤틀릴 우려가 있습니다.
- **동기화 알고리즘 규칙**: 
  - 버퍼에서 바이트 단위로 읽어 들이면서, LGAP 패킷의 고유 시작 바이트 패턴(Header, 일반적으로 문헌상 정의된 특정 헤더 바이트)을 감지합니다.
  - 헤더 감지 시점부터 정확히 16바이트를 수집하여 1개의 패킷 프레임을 완성합니다.
  - 16바이트 프레임 완성 직후 즉각 XOR 체크섬을 수행하고, 유효하지 않은 패킷은 즉시 폐기하고 다음 헤더를 찾도록 설계합니다.

### 2.2 XOR 체크섬 검증 로직
- 패킷은 정확히 16바이트의 고정 길이입니다.
- **수식 규칙**:
  ```python
  # packet은 16바이트 크기의 bytes 타입 객체
  payload_sum = sum(packet[0:15]) % 256
  checksum = payload_sum ^ 0x55
  is_valid = (checksum == packet[15])

```

* 위 수학적 체크섬 룰을 유틸리티 모듈에 구조화하여, 송수신 전 필수 검증 단계로 태깅해야 합니다.

### 2.3 반이중(Half-Duplex) 락(Lock) 무조건 준수

* 시리얼 객체(`serial.Serial`)에 직접 접근하여 `write`와 `read`를 처리하는 구역은 오직 하나의 스레드 락(`threading.Lock`) 소유 하에서만 순차적으로 접근해야 합니다.
* **패턴**:
```python
with self.serial_lock:
    self.serial.write(tx_packet)
    # 반이중 충돌을 피하기 위해 즉각 송신 버퍼를 플러시(Flush)한 후 리드를 준비합니다.
    self.serial.flush() 
    rx_packet = self.serial.read(16)

```

## 3. 방어적 예외 처리 (Robust Exception Handling)

* **`serial.SerialException` 분리**: 포트 연결 해제 등 하드웨어 예외는 반드시 로깅하고, 데몬을 완전히 죽이지 않고 포트 클로즈 후 지수 백오프 기반 재시도 메커니즘(`while not reconnected: sleep(backoff)...`)을 보장합니다.
* **`print()` 금지**: 디버깅 용도를 포함하여 소스 코드 전체에 단순 `print` 사용을 절대 금지합니다. 모든 메타정보 및 패킷 흐름은 프로젝트 루트 디렉토리에 있는 `app_logger.py`를 사용하여 체계적으로 출력해야 합니다.
* 패킷 송수신 로그 출력 시 가독성을 위해 Hex 포맷(`packet.hex()`)으로 일목요연하게 찍히도록 일관되게 구조화합니다.