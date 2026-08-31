# Architecture Design - python-raw-lgap-daemon

본 아키텍처는 반이중(Half-Duplex) RS-485 유선 환경의 제약 조건을 극복하고, 동시성 오류 및 노이즈 유입을 차단하는 **스레드 및 큐 기반 멀티태스킹 아키텍처**입니다.

## 1. 물리 구조 및 하드웨어 토폴로지


```

[ LG 실외기 Main PCB ]
│
│ (CENA / CENB 단자) - RS-485 차동 신호 라인
▼
[ USB-to-RS-485 Isolated Converter ] (전기적 서지 차단)
│
│ (USB 버스 / 가상 시리얼 포트: /dev/ttyUSB0)
▼
[ 라즈베리파이 (Python Daemon) ]

```

## 2. 파이썬 데몬 내부 소프트웨어 컴포넌트 구조


```

+--------------------------------------------------------------------------------+
|                             Raspberry Pi Daemon                                |
|                                                                                |
|  +-----------------------+                         +------------------------+  |
|  |  Local IPC Listener   |                         |  Master Polling Thread |  |
|  |  (Unix Domain Socket) |                         |  (주기적 상태 요청)     |  |
|  +-----------+-----------+                         +-----------+------------+  |
|              |                                                 |               |
|              v Command Push                                    v Trigger       |
|    +---------+---------+                             +---------+---------+     |
|    |  Command Queue    |                             |   Serial Mutex    |     |
|    | (Priority Queue)  |                             |   (Thread Lock)   |     |
|    +---------+---------+                             +---------+---------+     |
|              |                                                 |               |
|              +----------------------->+<-----------------------+               |
|                                       |                                        |
|                                       v                                        |
|                            +----------+----------+                             |
|                            |  Serial I/O Worker  |                             |
|                            |  (pyserial Wrapper) |                             |
|                            +----------+----------+                             |
|                                       | /dev/ttyUSB0                           |
+---------------------------------------|----------------------------------------+
| Raw Binary Frame (16 bytes)
▼
[ USB to RS-485 Dongle ]

```

## 3. 핵심 컴포넌트 역할 설명

### 1) Local IPC Listener (소켓 수신 스레드)
- 외부 CLI 툴이나 타 로컬 프로세스로부터 `{"cmd": "set_temp", "id": 1, "value": 24}` 형태의 JSON 제어 명령을 수신합니다.
- 수신 즉시 명령어를 파싱하여 내부 `Command Queue`에 높은 우선순위로 인입합니다.

### 2) Command Queue (우선순위 큐)
- 폴링 작업과 제어 작업의 충돌을 피하기 위한 버퍼 역할을 합니다.
- 제어 명령 패킷이 들어올 경우 폴링 사이클보다 먼저 처리할 수 있도록 설계합니다.

### 3) Master Polling Thread (폴링 스케줄러)
- `config.py`에 등록된 활성 실내기 ID 목록을 순회하며 주기적으로(예: 3초 간격) "상태 요청(Poll)" 패킷을 준비합니다.
- `Serial Mutex`를 획득하여 시리얼 포트 전유권을 획득한 뒤 송수신을 진행합니다.

### 4) Serial Mutex (상호 배제 락)
- 반이중(Half-Duplex) 통신에서 TX와 RX가 엉키지 않도록 보호하는 핵심 동기화 장치입니다.
- 한 번에 단 하나의 패킷 송수신 트랜잭션(송신 완료 후 즉각 응답 수신 대기 타임아웃 종료까지)만 보장합니다.

### 5) Serial I/O Worker (드라이버 레이어)
- `pyserial`을 Wrapping한 최하단 컴포넌트입니다.
- **물리 예외 처리**: 포트 단절 시 지수 백오프로 재시도하고, 응답 패킷 유입 시 16바이트의 데이터 무결성을 실시간 검증합니다.

## 4. 데이터 흐름 (Data Flow Sequence)

### A. 일반적인 상태 폴링 루프
1. `Polling Thread`가 실내기 #1 상태 조회 요청 생성.
2. `Serial Mutex` Lock 획득.
3. `/dev/ttyUSB0`로 16바이트 Poll 패킷 전송 (TX).
4. 수신 버퍼 대기 (Timeout 150ms 적용).
5. 에어컨으로부터 16바이트 응답 패킷 수신 (RX).
6. 패킷 정합성 및 XOR 체크섬 검증 ➔ 정상이면 데이터 로그 및 내부 상태 갱신.
7. `Serial Mutex` Lock 해제 ➔ 다음 주기가 도래할 때까지 슬립.

### B. 제어 명령 주입 시나리오
1. `Local IPC Listener`를 통해 "온도 22도 설정" 명령 유입 ➔ `Command Queue`로 적재.
2. `Polling Thread`가 다음 폴링을 돌기 전 `Command Queue`를 확인.
3. 대기 중인 제어 명령 존재 시, 일반 폴링 대신 "제어 명령 패킷" 조립.
4. `Serial Mutex` Lock 획득 후 제어 패킷 전송 (TX).
5. 에어컨의 제어 완료 응답(ACK 패킷) 수신 대기 및 검증 (RX).
6. 처리 완료 후 `Serial Mutex` 해제 및 폴링 루프 복귀.