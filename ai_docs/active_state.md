# Active State - LGAP & V-Net Python Raw Daemon

## 1. 현재 세션 진행 상태
* **목표**: LG Multi V CEN A/B 버스 대응을 위한 V-Net 프로토콜 확장, 8바이트 단문 패킷 송신 테스트, 실시간 버스 스니퍼 CLI 도구 구축 및 오류 패치.
* **상태**: 완료. `tools/bus_sniffer.py` 임포트 경로 오류 해결, 8바이트 단문 패킷(`00 00 A0 00 00 00 08 FD`) 송신 지원 및 8B/16B/23B/36B 멀티 프레임 동기화 스트림 탑재 완료.

## 2. 완료된 작업 (Completed Tasks)
* **스니퍼 도구 임포트 버그 수정 ([tools/bus_sniffer.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/tools/bus_sniffer.py))**:
  * `sys.path`에 프로젝트 루트 경로를 자동 추가하여 서브디렉토리 직접 실행 시 `config` 모듈 임포트 실패 문제 해결
* **8바이트 단문 패킷 송수신 지원 ([core/protocol.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/core/protocol.py), [core/polling.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/core/polling.py))**:
  * `00 00 A0 00 00 00 08 FD` (체크섬 `0xFD` 검증 완료) 폴링 송신 적용
  * `FrameSyncStream`에서 8바이트 단문 프레임 및 16바이트, 23/36바이트 가변 프레임을 동적으로 동기화 분리
* **V-Net 프로토콜 엔진 및 버스 스니퍼 도구 구축**:
  * 9600 bps 기본 보레이트 설정 및 `VNetProtocol` 클래스 탑재
  * `tools/bus_sniffer.py` CLI 도구 작성
* **단위 테스트 검증 ([tests/test_vnet.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/tests/test_vnet.py))**:
  * 단위 테스트 10종 100% 통과 완료

## 3. 다음 단계 작업 (Next To-Do / Pending)
* **회사 노트북 현장 검증**:
  * `git pull origin main`으로 최신 코드 동기화
  * 1단계 (선로 스니핑): `python tools/bus_sniffer.py --baud 9600` (또는 `--scan`)
  * 2단계 (데몬 실행): `python main.py` 실행하여 실시간 응답 및 대시보드(`http://localhost:8080`) 확인
