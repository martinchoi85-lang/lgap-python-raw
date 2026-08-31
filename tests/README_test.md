# 🧪 LGAP 데몬 통합 런타임 시뮬레이션 테스트 가이드

본 문서는 **물리 하드웨어 없이** `MockSerial` 가상 시뮬레이터 기반으로 데몬의 E2E 정상 동작을 검증하는 절차를 정의합니다.

---

## 0. 사전 준비

```bash
# 프로젝트 루트 디렉토리로 이동
cd /path/to/lgap-python-raw

# 가상환경 활성화 (이미 구축된 경우)
source venv/bin/activate   # Linux/macOS
# 또는
.\venv\Scripts\activate    # Windows

# 의존성 확인
pip install -r requirements.txt
```

> **참고**: `main.py` 65번째 줄에서 `use_mock=True`가 기본값으로 설정되어 있으므로, 별도 수정 없이 가상 모드로 구동됩니다.

---

## 1. 시나리오 A: 데몬 구동 및 순차 폴링 검증

### 1.1 실행

```bash
python main.py
```

### 1.2 정상 동작 판정 기준

터미널에 아래 패턴의 로그가 **연속적으로** 출력되면 정상입니다:

```text
2026-07-15 10:00:01 [INFO] LGAP-Daemon - LGAP Daemon 초기화 중...
2026-07-15 10:00:01 [INFO] root - 시리얼 포트 연결 성공: /dev/ttyUSB0
2026-07-15 10:00:01 [INFO] root - LGAP Engine 스케줄러가 시작되었습니다.
2026-07-15 10:00:01 [INFO] root - API Server started on port 8080
2026-07-15 10:00:01 [INFO] LGAP-Daemon - LGAP Daemon이 정상적으로 시작되었습니다. (SIGINT / SIGTERM 대기 중)
```

### 1.3 폴링 순환 확인

`config.py`의 `TARGET_INDOOR_UNITS = [1, 2, 3, 4]` 정의에 따라, 엔진이 약 `POLL_INTERVAL`(1초) 간격으로 ID 1 → 2 → 3 → 4 → 1 ... 순서대로 순차 폴링합니다.

폴링 응답 로그를 확인하려면 로그 레벨을 `DEBUG`로 변경합니다:

```python
# main.py 14행: level=logging.INFO → level=logging.DEBUG 로 임시 변경
logging.basicConfig(
    level=logging.DEBUG,
    ...
)
```

변경 후 재실행하면 아래와 같은 디버그 로그가 출력됩니다:

```text
2026-07-15 10:00:02 [DEBUG] root - [1] 상태 폴링 응답 수신: 0001000000000009624d000000000055
2026-07-15 10:00:03 [DEBUG] root - [2] 상태 폴링 응답 수신: 0002000000000807be4b000000000055
2026-07-15 10:00:04 [DEBUG] root - [3] 상태 폴링 응답 수신: 00030000000302074b3a000000000055
2026-07-15 10:00:05 [DEBUG] root - [4] 상태 폴링 응답 수신: 000400000000100003c4000000000055
```

### 1.4 검증 체크리스트

| # | 항목 | 판정 |
|---|------|------|
| 1 | `시리얼 포트 연결 성공` 로그 출력 | ✅ / ❌ |
| 2 | `LGAP Engine 스케줄러가 시작되었습니다` 로그 출력 | ✅ / ❌ |
| 3 | `API Server started on port 8080` 로그 출력 | ✅ / ❌ |
| 4 | 폴링 로그가 ID 1→2→3→4 순서로 반복 출력됨 | ✅ / ❌ |
| 5 | 예외(Exception) 또는 Traceback 없음 | ✅ / ❌ |

---

## 2. 시나리오 B: GET /states API 상태 조회 검증

데몬이 구동된 상태에서 **별도의 터미널**을 열고 아래 명령을 실행합니다.

### 2.1 curl 요청

```bash
curl -s -X GET http://localhost:8080/states | python -m json.tool
```

### 2.2 기대 응답 형식

```json
{
    "1": {
        "target_temp": 24,
        "room_temp": 26.0,
        "pipe_temp": 15.0,
        "op_mode": 0,
        "fan_speed": 4,
        "is_online": true,
        "last_updated": 1752559200.123
    },
    "2": {
        "target_temp": 22,
        "room_temp": 22.0,
        "pipe_temp": 10.7,
        "op_mode": 0,
        "fan_speed": 8,
        "is_online": true,
        "last_updated": 1752559201.456
    },
    "3": { "..." },
    "4": { "..." }
}
```

### 2.3 검증 체크리스트

| # | 항목 | 판정 |
|---|------|------|
| 1 | HTTP 200 응답 수신 | ✅ / ❌ |
| 2 | JSON 파싱 에러 없음 | ✅ / ❌ |
| 3 | 실내기 키(`"1"`, `"2"`, `"3"`, `"4"`)가 모두 존재 | ✅ / ❌ |
| 4 | `target_temp` 값이 16~30 범위 내 | ✅ / ❌ |
| 5 | `room_temp`, `pipe_temp`가 합리적인 실수 값 | ✅ / ❌ |
| 6 | `is_online`이 `true` | ✅ / ❌ |
| 7 | `last_updated`가 유닉스 타임스탬프 형식 | ✅ / ❌ |

> **존재하지 않는 경로 테스트**: `curl -s http://localhost:8080/invalid` 실행 시 `{"error": "Not Found"}` 응답과 함께 HTTP 404가 반환되어야 합니다.

---

## 3. 시나리오 C: POST /control 제어 명령 주입 및 Preemption 피드백 루프 검증

### 3.1 제어 명령 전송

```bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"id": 2, "target_temp": 24}' \
  http://localhost:8080/control | python -m json.tool
```

### 3.2 기대 API 응답

```json
{
    "status": "Command enqueued",
    "command": {
        "id": 2,
        "target_temp": 24
    }
}
```

### 3.3 데몬 터미널 관측 로그 (전체 피드백 루프)

```text
# 1단계: API 서버가 명령을 수신하여 command_queue에 적재
(curl 요청 수신 → 200 응답 반환)

# 2단계: 엔진 루프가 큐에서 명령을 꺼내 Preemption 발동
2026-07-15 10:00:10 [INFO] root - 제어 명령 우선 전송 (Preempt): {'id': 2, 'target_temp': 24}

# 3단계: MockSerial이 제어 패킷을 수신하여 가상 상태를 target=24로 갱신하고 응답 패킷 반환
2026-07-15 10:00:10 [INFO] root - 제어 완료 응답 수신: 000200000000080942...

# 4단계: 이후 폴링 사이클에서 ID 2의 target_temp가 24로 갱신된 상태 확인
```

### 3.4 갱신 결과 재검증

제어 명령 전송 후 약 5초 대기한 뒤 다시 상태를 조회합니다:

```bash
curl -s -X GET http://localhost:8080/states | python -m json.tool
```

ID `"2"`의 `target_temp`가 기존 값(22)에서 **24**로 변경되었는지 확인합니다.

### 3.5 가드 클로즈 (Guard Clause) 검증

유효 범위를 벗어나는 온도 값을 전송하여 API 서버의 방어 로직을 확인합니다:

```bash
# 온도 범위 초과 (31도)
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"id": 1, "target_temp": 31}' \
  http://localhost:8080/control | python -m json.tool
```

기대 응답:

```json
{
    "error": "target_temp must be between 16 and 30"
}
```

### 3.6 검증 체크리스트

| # | 항목 | 판정 |
|---|------|------|
| 1 | POST 요청 시 HTTP 200 + `Command enqueued` 응답 | ✅ / ❌ |
| 2 | `제어 명령 우선 전송 (Preempt)` 로그 출력 | ✅ / ❌ |
| 3 | `제어 완료 응답 수신` 로그 출력 (hex 패킷 포함) | ✅ / ❌ |
| 4 | GET /states 재조회 시 `target_temp`가 갱신됨 | ✅ / ❌ |
| 5 | 범위 초과 온도 전송 시 HTTP 400 에러 반환 | ✅ / ❌ |
| 6 | Preemption 후 정상 폴링 루프 복귀 | ✅ / ❌ |

---

## 4. 종료 (Graceful Shutdown) 검증

```bash
# 데몬 실행 중인 터미널에서 Ctrl+C 입력
```

기대 종료 로그:

```text
2026-07-15 10:05:00 [INFO] LGAP-Daemon - 종료 시그널 수신 (2). Graceful Shutdown 진행 중...
2026-07-15 10:05:00 [INFO] LGAP-Daemon - 정리(Cleanup) 시퀀스 시작...
2026-07-15 10:05:00 [INFO] root - API Server stopped
2026-07-15 10:05:00 [INFO] root - LGAP Engine 스케줄러가 중지되었습니다.
2026-07-15 10:05:00 [INFO] LGAP-Daemon - LGAP Daemon 종료 완료.
```

| # | 항목 | 판정 |
|---|------|------|
| 1 | `Graceful Shutdown 진행 중` 로그 출력 | ✅ / ❌ |
| 2 | API 서버 정상 종료 | ✅ / ❌ |
| 3 | Engine 스케줄러 정상 종료 | ✅ / ❌ |
| 4 | 프로세스가 좀비 없이 완전 종료됨 | ✅ / ❌ |
