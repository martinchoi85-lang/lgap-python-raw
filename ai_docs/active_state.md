# Active State - LGAP & V-Net Python Raw Daemon

## 1. 현재 세션 진행 상태
* **목표**: 상태 조회 폴링 TX 패킷을 검증된 8바이트 단문(`00 00 A0 00 00 00 08 FD`)으로 완전히 단일화하여 분기 혼선 방지, 제어 패킷 16B 표준 프레임(`packet[2]=0xFF`) 적용.
* **상태**: 완료. 분기별 서로 다른 패킷 송출 로직 제거, [core/polling.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/core/polling.py)에서 무조건 `00 00 A0 00 00 00 08 FD` 송출하도록 고정.

## 2. 완료된 작업 (Completed Tasks)
* **폴링 TX 패킷 단일화 ([core/polling.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/core/polling.py), [config.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/config.py))**:
  * `mode` 조건에 따라 16B 폴링(`00 01 00 ... 54`)으로 분기되던 레거시 코드 전면 제거
  * 데몬 실행 시 무조건 실제 하드웨어가 응답하는 `00 00 A0 00 00 00 08 FD` (또는 `config.POLL_TX_HEX`)만 송신하도록 단일화
  * 기본 보레이트 `9600 bps`, 기본 모드 `VNET` 고정
* **16B 제어 패킷 전송 로직 유지**:
  * 제어 시 16B LGAP 제어 프레임(`00 <id> FF ...`) 송출
  * 수신 패킷의 실제 ID(Unit #3)를 `StateManager`에 정확히 바인딩
* **단위 테스트 검증 ([tests/test_protocol.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/tests/test_protocol.py), [tests/test_api.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/tests/test_api.py))**:
  * 11종 전체 단위 테스트 100% 통과

## 3. 다음 단계 작업 (Next To-Do / Pending)
* **현장 데몬 실행 및 제어 검증**:
  * `git pull origin main` 후 `python main.py` 실행 (옵션 없이 `py main.py`만 쳐도 `00 00 A0 00 00 00 08 FD` @ 9600bps로 즉시 동작)
  * 웹 대시보드(`http://localhost:8080`)에서 실내기 #3 온도/모드 제어 송신 확인
