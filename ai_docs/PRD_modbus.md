# Product Requirements Document (PRD) - Python Raw Modbus Daemon

> **개발 및 운영 워크플로우 (Development & Deployment Workflow)**
> - **코드 개발 및 수정**: 미니PC (Antigravity IDE 환경)에서 개발 후 GitHub로 Push
> - **실제 구동 및 현장 테스트**: 회사 노트북 (사내 보안 정책상 Antigravity 미사용)에서 GitHub Pull 후 Python venv 환경에서 실제 구동/테스트 수행

---

## 1. 개요 (Overview)
- **프로젝트명**: `modbus-python-raw`
- **목적**: RS-485 유선 시리얼 버스를 통해 산업용 표준 Modbus RTU 프로토콜을 사용하는 센서 및 제어 기기(온습도 센서, 전력량계, 밸브/인버터 등)의 데이터를 주기적으로 수집(Monitoring)하고 제어(Control)하는 경량 파이썬 단독 데몬 엔진 개발.
- **배경**: 무선 통신의 신호 불안정성과 중간 게이트웨이 종속성을 배제하고, 직접 RS-485 유선 직결 통신으로 데이터 수집 신뢰성을 극대화하며, `lgap-python-raw`의 검증된 고안정성 아키텍처(시리얼 락, 백그라운드 폴링, Thread-Safe 상태 관리, REST/Web UI)를 계승함.

---

## 2. 사용자 및 하드웨어 환경 정의
- **개발/실행 환경**: Python 3.10+ (Windows / Linux)
- **물리 인터페이스**: USB to RS-485 Isolated Converter (2가닥 A/B 차동 신호 유선 연결)
- **통신 설정 (물리 계층)**:
  - Baudrate: 9600 bps (기본값, 장비 설정에 따라 4800 / 19200 / 38400 가변)
  - Data bits: 8, Parity: None, Stop bits: 1 (8N1)
  - 통신 모드: 반이중(Half-Duplex)

---

## 3. 핵심 기능 요구사항 (Functional Requirements)

### F-1. Modbus RTU 프로토콜 통신 드라이버
- **권장 라이브러리**: `minimalmodbus` (단일 파이썬 파일 기반의 극경량/고안정 라이브러리) 또는 `pyserial`.
- **지원 기능**:
  - **Read Holding Registers (Function Code 0x03)**: 상태값 및 측정치 읽기
  - **Read Input Registers (Function Code 0x04)**: 센서 아날로그 입력값 읽기
  - **Write Single Register (Function Code 0x06)** / **Write Multiple Registers (Function Code 0x10)**: 제어 명령 쓰기
  - **Read/Write Coils (Function Code 0x01, 0x05)**: ON/OFF 릴레이 제어 (장비 사양에 따름)
- **데이터 변환(Scaling)**: 정수형 레지스터를 소수점(부동소수점 Float), Signed/Unsigned, 비트마스크로 변환 처리.

### F-2. 반이중(Half-Duplex) 시리얼 동시성 제어 및 폴링 엔진
- **시리얼 락(Mutex Lock)**: 시리얼 포트에 접근하는 모든 Read/Write는 `threading.Lock` 소유 하에서만 순차 실행.
- **주기적 폴링**: 등록된 Modbus 슬레이브 장비(Slave ID 1, 2, ...)들의 레지스터를 `config.py`에 정의된 주기(예: 1.0초)로 순차 조회.
- **우선순위 제어 명령 주입 (Preemption)**: 외부 제어 요청 발생 시, 현재 폴링 루프를 대기시키고 제어 레지스터 쓰기를 최우선 실행한 뒤 응답 확인.

### F-3. Thread-Safe 상태 관리자 (`StateManager`)
- 수집된 슬레이브 장비별 최신 레지스터 값(온도, 습도, 전력, 전압, 상태 등), 통신 성공 여부(`is_online`), 최종 갱신 타임스탬프를 스레드 안전하게 메모리에 캐싱.

### F-4. 경량 로컬 인터페이스 (REST API & 내장 Web UI)
- **API 서버 (`port=8081` 또는 8080)**:
  - `GET /states`: 전체 슬레이브 장비의 현재 상태 JSON 반환
  - `POST /control`: 슬레이브 ID, 레지스터 주소, 제어 값을 받아 즉시 쓰기 큐에 삽입
- **내장 Web UI (`GET /`)**:
  - 외부 CDN 없이 순수 Vanilla HTML/CSS/JS로 렌더링되는 실시간 모니터링/제어 대시보드 제공 (1초 자동 갱신).

---

## 4. 소프트웨어 아키텍처 및 디렉토리 구조

```
modbus-python-raw/
├── config.py             # Modbus 통신 설정 (포트, Baudrate, Slave ID 리스트, Register Map)
├── main.py               # 데몬 컨트롤러 및 Graceful Shutdown
├── app_logger.py         # 표준 로거
├── core/
│   ├── modbus_driver.py  # minimalmodbus 기반 Modbus RTU Read/Write 인터페이스
│   ├── polling.py        # ModbusEngine (시리얼 락, 백그라운드 폴링, 명령 큐)
│   └── state.py          # StateManager (Thread-Safe 상태 저장소)
├── api/
│   ├── interface.py      # Python 표준 http.server 기반 REST API 서버
│   └── ui.py             # Modbus 관제용 단일 페이지 독립 Web UI
└── tests/
    ├── mock_modbus.py    # 실제 하드웨어 없이 테스트할 수 있는 가상 Modbus 슬레이브 시뮬레이터
    ├── test_driver.py    # Modbus 드라이버 단위 테스트
    └── test_api.py       # REST API 및 Web UI 연동 단위 테스트
```

---

## 5. 단계별 구현 계획 (Implementation Phases)
1. **Phase 1: 환경 설정 및 가상 시뮬레이터 구축**
   - `minimalmodbus` 의존성 추가 (`requirements.txt`)
   - `tests/mock_modbus.py` 가상 슬레이브 시뮬레이터 작성
2. **Phase 2: Modbus 드라이버 및 폴링 엔진 구현**
   - `core/modbus_driver.py` 및 `core/polling.py` 작성
   - 단위 테스트(`tests/test_driver.py`)로 레지스터 읽기/쓰기 및 락 검증
3. **Phase 3: REST API & Web UI 연동**
   - Modbus 장비 특성에 맞춘 `api/ui.py` 대시보드 커스터마이징 (센서 그래프/카드, 릴레이 스위치 등)
4. **Phase 4: 현장 배포 가이드 작성**
   - `setup_env.bat`, `COMPANY_LAPTOP_SETUP.md` 작성
