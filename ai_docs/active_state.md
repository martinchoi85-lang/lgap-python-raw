# Active State - LGAP & V-Net Python Raw Daemon

## 1. 현재 세션 진행 상태
* **목표**: 실제 하드웨어 통신 성공 패킷(`10 03 A0 30 ... 6E`) 분석 및 파서 바이트 오프셋 일치화, 실내온도/배관온도/희망온도 정확한 실시간 디코딩 반영.
* **상태**: 완료. 실제 기기 응답 16B 패킷 수신 및 XOR 체크섬(`0x6E`) 100% 정합성 검증 완료. `0x10` 헤더 동기화 및 16B LGAP 파서 연동 완료.

## 2. 완료된 작업 (Completed Tasks)
* **실제 하드웨어 응답 패킷 분석 및 디코딩 공식 검증**:
  * TX: `00 00 A0 00 00 00 08 FD`
  * RX: `10 03 A0 30 00 00 11 46 6D A7 9A 16 01 18 24 6E`
  * Byte 8 (`0x6D` = 109): `(192 - 109) / 3.0` = **27.7°C** (실제 에어컨 화면 27°C와 100% 일치)
  * Byte 9 (`0xA7` = 167): `(192 - 167) / 3.0` = **8.3°C** (냉방 배관 온도)
  * Byte 5 (`0x00`): **냉방 모드 (Cool)**
  * Byte 7 (`0x46`): **희망온도 21°C**
  * Byte 15 (`0x6E`): **XOR 체크섬 일치 (`sum[:15] % 256 ^ 0x55 == 0x6E`)**
* **프로토콜 파서 및 동기화 스트림 패치 ([core/protocol.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/core/protocol.py))**:
  * `FrameSyncStream`에 `0x10` 헤더 패턴 추가
  * `VNetProtocol.parse_frame()`에 16바이트 패킷 유입 시 `parse_packet()`으로 자동 위임 처리
* **단위 테스트 검증 ([tests/test_protocol.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/tests/test_protocol.py), [tests/test_api.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/tests/test_api.py))**:
  * 11종 전체 테스트 통과 (100% PASS)

## 3. 다음 단계 작업 (Next To-Do / Pending)
* **현장 데몬 실행 및 UI 모니터링**:
  * `python main.py --mode VNET --baud 9600` 실행
  * 웹 대시보드(`http://localhost:8080`)에서 실내온도 27°C 및 배관온도, 모드가 정상 출력되는지 확인
  * 웹 대시보드에서 희망온도/모드 변경 제어 송신 테스트
