# Active State - LGAP & V-Net Python Raw Daemon

## 1. 현재 세션 진행 상태
* **목표**: 실선로 현장 검증 피드백 반영 (LGAP 16B 폴링 정상 응답 확인), `core/polling.py` 동기화 및 다기능 통합 웹 관제 UI(온도/모드/풍량 실시간 제어) 고도화.
* **상태**: 완료. LGAP 모드 실동작 확인, `api/ui.py` 및 `api/interface.py`에 프로토콜 메타데이터 및 다기능 제어 UI 반영, 단위 테스트 11종 100% 통과.

## 2. 완료된 작업 (Completed Tasks)
* **현장 동작 확인 및 폴링 코드 동기화 ([core/polling.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/core/polling.py))**:
  * `config.PROTOCOL_MODE = 'LGAP'` (9600 bps, COM6, 16B 폴링 규격)에서 실내기 장치와의 TX/RX 정상 통신 검증 완료
  * 검증된 패킷 주석 및 슬라이딩 윈도우 동기화 코드 반영 완료
* **웹 관제 UI 고도화 ([api/ui.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/api/ui.py), [api/interface.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/api/interface.py))**:
  * 상단 헤더에 현재 프로토콜 모드(`LGAP`/`VNET`), 포트, 보레이트, 데몬 연결 상태 실시간 배지 표시
  * 실내기별 현재 상태(실내온도, 배관온도, 설정온도, 운전모드, 풍량, 온/오프라인) 시각화
  * 희망온도(16~30°C Stepper), 운전 모드(냉방/난방/제습/송풍/자동), 풍량(약/중/강/자동/파워) 통합 제어 패널 구현
  * `/info` 및 다채널 `/control` 엔드포인트 연동
* **단위 테스트 및 검증 ([tests/test_api.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/tests/test_api.py))**:
  * 11종 전체 단위 테스트 100% PASS

## 3. 다음 단계 작업 (Next To-Do / Pending)
* **회사 노트북 현장 검증**:
  * `git pull origin main`으로 최신 코드 동기화
  * `python main.py` 실행 후 브라우저(`http://localhost:8080`)에서 실내기 카드 모니터링 및 온도/모드/풍량 제어 테스트 수행
