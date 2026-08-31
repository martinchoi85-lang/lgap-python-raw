 # 🚀 프로덕션 실장 전환 체크리스트 (Switch-to-Production)

본 문서는 `MockSerial` 시뮬레이터 모드에서 **실제 RS-485 컨버터 + LG 실외기** 물리 환경으로 전환하는 실장 당일 작업자용 체크리스트입니다.

---

## Phase 1: 소프트웨어 스위칭 (MockSerial → Real Serial)

### 1.1 `main.py` 의존성 주입 전환

`main.py` 65번째 줄의 `use_mock` 플래그를 `False`로 변경합니다:

```diff
- controller = DaemonController(use_mock=True) # 실 환경 배포 시 False 로 전환
+ controller = DaemonController(use_mock=False)
```

이 한 줄 변경으로 `DaemonController.__init__`(22행)의 분기가 작동하여 `serial.Serial` 실물 객체가 자동 주입됩니다:

```python
# main.py:26 - 기존 DI 분기 로직 (수정 불필요)
serial_class = MockSerial if use_mock else __import__('serial').Serial
```

### 1.2 `config.py` 시리얼 포트 경로 확인

라즈베리파이에 USB-to-RS485 컨버터를 연결한 뒤 할당된 장치 파일 경로를 확인합니다:

```bash
# 컨버터 연결 후 장치 파일 확인
ls -la /dev/ttyUSB*
```

`config.py`의 `SERIAL_PORT` 값이 실제 경로와 일치하는지 확인합니다:

```python
# config.py:4
SERIAL_PORT: str = "/dev/ttyUSB0"  # 실제 장치 경로로 변경
```

> ⚠️ **복수 USB 장치 연결 시** `/dev/ttyUSB1` 등으로 밀릴 수 있습니다. `dmesg | grep tty` 명령으로 정확한 경로를 확인하세요.

---

## Phase 2: 리눅스 권한 부여

### 2.1 dialout 그룹 추가 (필수)

리눅스 보안 정책상, 일반 유저는 `/dev/ttyUSB0` 시리얼 장치에 직접 접근할 수 없습니다. 아래 명령으로 유저에게 시리얼 포트 접근 권한을 부여합니다:

```bash
sudo usermod -aG dialout $USER
```

> ⚠️ **반드시 로그아웃 후 재로그인 (또는 재부팅)** 해야 그룹 변경이 적용됩니다. 적용 전 데몬 실행 시 `PermissionError: [Errno 13] Permission denied: '/dev/ttyUSB0'` 오류가 발생합니다.

### 2.2 권한 적용 확인

```bash
# 현재 유저의 그룹 목록에 dialout 포함 여부 확인
groups $USER
# 출력 예: pi adm dialout sudo ...

# 장치 파일 권한 확인
ls -la /dev/ttyUSB0
# 출력 예: crw-rw---- 1 root dialout ... /dev/ttyUSB0
```

---

## Phase 3: systemd 서비스 등록

### 3.1 서비스 파일 배치

```bash
# 1. 서비스 파일을 systemd 시스템 디렉토리로 복사
sudo cp /home/pi/lgap-daemon/deployment/lgap-daemon.service /etc/systemd/system/

# 2. systemd 데몬 리로드 (신규 서비스 파일 인식)
sudo systemctl daemon-reload

# 3. 부팅 시 자동 시작 등록
sudo systemctl enable lgap-daemon

# 4. 서비스 즉시 시작
sudo systemctl start lgap-daemon
```

### 3.2 서비스 상태 확인

```bash
sudo systemctl status lgap-daemon
```

정상 가동 시 출력:

```text
● lgap-daemon.service - LGAP Aircon Control Daemon
     Loaded: loaded (/etc/systemd/system/lgap-daemon.service; enabled)
     Active: active (running) since ...
   Main PID: 12345 (python3)
      Tasks: 4
     Memory: 12.3M
```

### 3.3 서비스 제어 명령 요약

| 동작 | 명령 |
|------|------|
| 시작 | `sudo systemctl start lgap-daemon` |
| 중지 | `sudo systemctl stop lgap-daemon` |
| 재시작 | `sudo systemctl restart lgap-daemon` |
| 상태 확인 | `sudo systemctl status lgap-daemon` |
| 자동 시작 해제 | `sudo systemctl disable lgap-daemon` |

---

## Phase 4: 실시간 로그 모니터링 및 디버깅

### 4.1 실시간 로그 스트리밍

```bash
sudo journalctl -u lgap-daemon -f
```

### 4.2 정상 동작 로그 패턴

실외기 연결 성공 시 아래와 같은 로그가 연속적으로 출력됩니다:

```text
LGAP Daemon 초기화 중...
시리얼 포트 연결 성공: /dev/ttyUSB0
LGAP Engine 스케줄러가 시작되었습니다.
API Server started on port 8080
LGAP Daemon이 정상적으로 시작되었습니다. (SIGINT / SIGTERM 대기 중)
```

### 4.3 이상 징후 및 대응

| 로그 패턴 | 원인 | 대응 |
|-----------|------|------|
| `시리얼 연결 실패 (/dev/ttyUSB0)` | USB 컨버터 미연결 또는 경로 불일치 | `ls /dev/ttyUSB*` 및 `dmesg \| grep tty`로 실제 경로 확인 |
| `PermissionError: Permission denied` | dialout 그룹 미등록 | Phase 2 재수행 후 재부팅 |
| `트랜잭션 타임아웃. 응답 없음.` | 실외기 전원 미투입 또는 CENA/CENB 결선 오류 | 배선 극성(A/B) 교차 확인, 실외기 전원 상태 점검 |
| `유효하지 않은 패킷입니다.` (체크섬 에러 다수) | RS-485 라인 노이즈 또는 보레이트 불일치 | `config.py`의 `BAUDRATE=4800` 확인, 차폐 케이블 교체 검토 |
| `시리얼 연결 유실 감지. 재연결 시도 중...` | USB 컨버터 물리적 분리 | 컨버터 고정 상태 확인, 자동 복구 대기 (엔진이 자동 재시도) |

### 4.4 패킷 Hex 덤프 분석

DEBUG 레벨 로깅 활성화 후 수신된 패킷의 원시 바이트를 분석합니다:

```text
[DEBUG] [1] 상태 폴링 응답 수신: 0001000000000009624d000000000055
```

각 바이트 위치별 의미:

```text
Byte[ 0]:  0x00  → 헤더
Byte[ 1]:  0x01  → 실내기 ID
Byte[ 5]:  0x00  → 운전 모드 (0x00=냉방, 0x04=난방)
Byte[ 6]:  0x00  → 풍량 (0x04=중, 0x08=강)
Byte[ 7]:  0x09  → 설정 온도 raw (0x09 + 15 = 24°C)
Byte[ 8]:  0x62  → 실내 온도 raw ((192 - 98) / 3 = 31.3°C)
Byte[ 9]:  0x4D  → 배관 온도 raw ((192 - 77) / 3 = 38.3°C)
Byte[15]:  0x55  → XOR 체크섬
```

---

## 최종 전환 체크리스트 (서명란)

| # | 작업 항목 | 완료 | 담당자 |
|---|----------|------|--------|
| 1 | `main.py` → `use_mock=False` 변경 | ☐ | |
| 2 | `config.py` → `SERIAL_PORT` 실제 경로 확인 | ☐ | |
| 3 | USB-to-RS485 컨버터 물리 결선 (CENA/CENB) | ☐ | |
| 4 | `sudo usermod -aG dialout $USER` + 재로그인 | ☐ | |
| 5 | `groups $USER`로 dialout 그룹 포함 확인 | ☐ | |
| 6 | `.service` 파일 복사 및 `systemctl enable` | ☐ | |
| 7 | `systemctl start lgap-daemon` 서비스 기동 | ☐ | |
| 8 | `journalctl -u lgap-daemon -f`로 폴링 로그 확인 | ☐ | |
| 9 | `curl http://localhost:8080/states`로 실시간 상태 조회 | ☐ | |
| 10 | 체크섬 에러 없이 10분 이상 안정 동작 확인 | ☐ | |
