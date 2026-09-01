# Active State - LGAP Python Raw Daemon

## 1. 현재 세션 진행 상태
* **목표**: 송신 패킷 체크섬 자동 계산 패치, 독립형 단일 페이지 Web UI 구현 및 연동, Modbus 신규 프로젝트 전환 가이드 및 PRD 작성.
* **상태**: 완료. 16바이트 TX 패킷 XOR 체크섬 자동 주입, `api/ui.py` 독립 대시보드 구축 및 REST API 연동 완료, 전체 단위 테스트(프로토콜 3종, API/UI 3종) 100% 통과, 신규 `modbus-python-raw` 프로젝트 PRD([ai_docs/PRD_modbus.md](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/ai_docs/PRD_modbus.md)) 작성 완료.

## 2. 완료된 작업 (Completed Tasks)
* **송신 체크섬 자동 계산 패치 ([core/protocol.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/core/protocol.py), [core/polling.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/core/polling.py))**:
  * `build_poll_packet(unit_id)` 및 `build_control_packet(command)` 함수 구현을 통해 16번째 바이트에 XOR 0x55 체크섬 자동 주입
  * 가상 에어컨([tests/mock_aircon.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/tests/mock_aircon.py))에 체크섬 검증 로직 추가 및 프로토콜 단위 테스트([tests/test_protocol.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/tests/test_protocol.py)) 검증 완료
* **독립형 관제 Web UI 구현 ([api/ui.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/api/ui.py), [api/interface.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/api/interface.py))**:
  * 백엔드 서비스 로직과 완전히 분리된 단일 페이지 Vanilla Web UI 템플릿 작성 (외부 CDN 의존성 0%)
  * 1초 자동 갱신 실시간 카드 뷰, 희망 온도 증감 조절 및 즉시 제어 버튼, 토스트 알림 탑재
  * `GET /` 라우트 연동 및 API E2E 단위 테스트([tests/test_api.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/tests/test_api.py)) 통과
* **문서 정합성 및 배포 설정 보완**:
  * [COMPANY_LAPTOP_SETUP.md](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/COMPANY_LAPTOP_SETUP.md)의 `main.py` 인스턴스화 명칭 정정
  * [main.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/main.py)에 실 환경 전환 주석 보강
* **Modbus 프로젝트 전용 PRD 수립 ([ai_docs/PRD_modbus.md](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/ai_docs/PRD_modbus.md))**:
  * `modbus-python-raw` 신규 앱 개발을 위한 아키텍처, 요구사항, 템플릿 가이드라인 작성

## 3. 다음 단계 작업 (Next To-Do / Pending)
* **회사 노트북 현장 실기기 테스트**:
  * `git pull origin main`으로 최신 코드(체크섬 패치 및 Web UI) 동기화
  * 실외기 단자대 결선 ➔ COM 포트 확인(`config.py`) ➔ `main.py`의 `use_mock=False` 전환 후 `python main.py` 실행
  * 웹 브라우저(`http://localhost:8080`) 접속하여 실시간 온도 확인 및 온도 제어 실증
