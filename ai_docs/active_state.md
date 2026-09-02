# Active State - LGAP & V-Net Python Raw Daemon

## 1. 현재 세션 진행 상태
* **목표**: LG Multi V CEN A/B 버스 대응을 위한 V-Net 프로토콜 엔진 확장 및 실시간 버스 스니퍼 진단 도구 구축.
* **상태**: 완료. 9600 bps 기본 보레이트 전환, `VNetProtocol` 클래스 및 23/36바이트 가변 프레임 동기화 스트림 구현, `tools/bus_sniffer.py` CLI 진단 도구 생성, `core/polling.py` V-Net 모드 지원 완료, 단위 테스트 10종 100% 통과.

## 2. 완료된 작업 (Completed Tasks)
* **`config.py` V-Net 프로토콜 확장**:
  * 기본 통신 속도 `BAUDRATE = 9600` 변경
  * 프로토콜 모드 `PROTOCOL_MODE = "VNET"` ("VNET" | "LGAP" | "AUTO_SNIFF") 도입
  * 마스터 주소(`VNET_CENTRAL_ADDR = 0x00`) 및 타깃 실내기 리스트(`VNET_TARGET_UNITS = [4, 5]`) 추가
* **원시 패킷 수집 및 진단 도구 생성 ([tools/bus_sniffer.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/tools/bus_sniffer.py))**:
  * CEN 버스 실시간 감청 CLI 도구 작성 (`python tools/bus_sniffer.py --scan` 또는 `--baud 9600`)
  * 실시간 헥스 덤프(`[RX 36B] 41 E0 ...`) 및 V-Net 프레임(0xC1, 0x41, 0xE1) 자동 분해 출력 탑재
* **V-Net 프로토콜 엔진 구축 ([core/protocol.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/core/protocol.py))**:
  * 기존 16바이트 LGAP와 호환성을 유지하면서 `VNetProtocol` 신규 클래스 구현
  * 23바이트 실내기 상태 조회(`build_poll_frame`) 및 제어(`build_control_frame`) 패킷 생성기 탑재
  * 36바이트 응답 패킷 역직렬화(`parse_frame`) 구현
  * `FrameSyncStream`을 개선하여 0x41, 0xC1, 0xE1 가변 프레임과 16바이트 고정 프레임을 동적으로 동기화 분리
* **폴링 엔진 및 트랜잭션 업데이트 ([core/polling.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/core/polling.py))**:
  * `PROTOCOL_MODE == "VNET"` 모드에서 V-Net 폴링 및 롤링 시퀀스 카운터 자동 관리 연동
  * Half-Duplex Lock 하에서 원시 트랜잭션 로깅 최적화
* **단위 테스트 검증 ([tests/test_vnet.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/tests/test_vnet.py))**:
  * V-Net 패킷 생성, 파싱, 멀티 프레임 스트림 분리 단위 테스트 10종 통과 완료

## 3. 다음 단계 작업 (Next To-Do / Pending)
* **회사 노트북 현장 검증**:
  * `git pull origin main`으로 최신 V-Net 코드 및 스니퍼 동기화
  * 1단계: `python tools/bus_sniffer.py --baud 9600` 실행하여 실시간 CEN 버스 트래픽 감청
  * 2단계: `python main.py` 실행하여 V-Net 실시간 폴링 및 대시보드(`http://localhost:8080`) 확인
