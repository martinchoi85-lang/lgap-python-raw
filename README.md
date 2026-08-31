# python-raw-lgap-daemon

라즈베리파이에서 USB-to-RS485 유선 인터페이스를 통해 LG 시스템 에어컨(LGAP 프로토콜)을 직접 제어하고 모니터링하는 경량 백그라운드 파이썬 데몬 서비스입니다.

## 1. 개요 및 하드웨어 연결 구성
무선 솔루션의 네트워크 단절 불안정성을 탈피하고, 신뢰도가 높은 산업용 유선 RS-485 통신을 활용하여 에어컨 상태 순차 폴링 및 타이트한 제어 피드백 루프를 달성합니다.


```

[ Raspberry Pi ] === (USB) === [ USB to RS-485 Isolated Converter ] === (유선 A/B 선) === [ LG 실외기 PCB ]

```

## 2. 주요 기능
- **Raw LGAP 파서**: ESPHome 도움 없이 순수 파이썬 바이너리 슬라이싱 및 XOR 0x55 체크섬 계산기 자체 구동.
- **반이중 폴링 스케줄러**: 데이터 충돌을 원천 차단하는 스레드 동기화 기반 락 엔진 탑재.
- **자동 포트 재결합**: 물리적 라인 단절 및 USB 동글 재연결 감지 시 자동 세션 복구 및 포트 재오픈.
- **경량 로컬 제어 인터페이스**: 백그라운드로 도는 데몬에 간편하게 JSON 제어 명령을 전달할 수 있는 Unix Domain Socket 인터페이스 탑재.

## 3. 디렉토리 구조 및 파일 매핑
```text
lgap-daemon/
├── config.py             # 실내기 ID 리스트, 시리얼 포트명, 폴링 간격 등 Hard-coded 설정
├── daemon.py             # 프로그램 진입점 (메인 루프 가동 및 스레드 오케스트레이션)
├── core/
│   ├── __init__.py
│   ├── protocol.py       # LGAP 패킷 구조 정의, 체크섬 계산 및 바이너리 직렬화/역직렬화
│   ├── polling.py        # 순차적 폴링 스케줄링 및 Priority Queue 명령 주입 로직
│   └── serial_worker.py  # pyserial Wrapper (안전한 포트 자동 복구 및 Mutex 송수신 적용)
├── utils/
│   ├── __init__.py
│   └── logger.py         # 패킷 추적용 포맷팅이 적용된 표준 logging 셋업
├── tests/
│   └── test_protocol.py  # 실제 패킷 Hex 덤프를 가정한 pytest 단위 테스트 코드
├── requirements.txt      # pyserial 등 극소화된 라이브러리 의존성 파일
└── lgap-daemon.service   # systemd 백그라운드 서비스 등록을 위한 설정 파일


## 빠른 시작 가이드 (Quick Start)

### 4.1 가상환경 구축 및 필수 라이브러리 설치

```bash
# 프로젝트 폴더 생성 및 진입
cd lgap-daemon

# 파이썬 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 의존성 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt

```

### 4.2 단위 테스트 수행 (프로토콜 무결성 검증)

실제 장비 연결 전, LGAP 바이너리 파서와 체크섬 엔진이 정확히 계산되는지 로컬 mock 테스트를 수행합니다.

```bash
pytest tests/

```

### 4.3 백그라운드 데몬 서비스 등록 (`systemd`)

시스템 전원이 켜지면 자동으로 백그라운드에서 데몬이 무중단 기동되도록 등록합니다.

```bash
# 서비스 파일을 systemd 시스템 디렉토리로 복사
sudo cp lgap-daemon.service /etc/systemd/system/

# 데몬 리로드 및 서비스 활성화/시작
sudo systemctl daemon-reload
sudo systemctl enable lgap-daemon
sudo systemctl start lgap-daemon

# 서비스 가동 상태 및 패킷 로그 확인
sudo journalctl -u lgap-daemon -f

```