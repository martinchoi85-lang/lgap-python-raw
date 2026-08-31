# Roadmap - LGAP Python Raw Daemon

## 마일스톤 1: 프로토콜 분석 및 로컬 시뮬레이션 환경 (완료)
* [x] 8N1 통신 규격 기반 루프백 환경 검증 코드 작성 (`tests/test_serial_loopback.py`)
* [x] XOR 체크섬 연산 및 16바이트 프레임 슬라이딩 윈도우 동기화 구현 (`core/protocol.py`)
* [x] 스레드 락 기반 반이중 폴링 스케줄러 및 명령 Preemption 구현 (`core/polling.py`)
* [x] 실외기 응답 역산 공식이 반영된 모의 시뮬레이터 개발 (`tests/mock_aircon.py`)
* [x] 내장 HTTP 서버 기반의 모니터링/제어 API 서버 구축 (`api/interface.py`)
* [x] 시그널 처리 및 Graceful Shutdown 메커니즘을 지원하는 메인 데몬 구조화 (`main.py`)

## 마일스톤 2: 물리 계층 결선 및 현장 데이터 무결성 검증 (예정)
* [ ] 라즈베리파이 물리 시리얼 포트 결선 및 데이터 신호 세기 확인
* [ ] 실 기기 패킷 정합성 및 `FrameSyncStream` 동기화 윈도우 안정화
* [ ] 에러율 분석 및 물리 단절 시 지수 백오프 자동 복구 프로세스 미세 조정

## 마일스톤 3: 현장 배포 및 운영 서비스 안정화 (진행 중)
* [ ] 실 기기 제어 명령(온도 변경, 가동, 운전 모드) 정상 반응성 검증
* [x] 리눅스 `systemd` 서비스 등록을 위한 설정 파일 정의 및 배포 체크리스트 구축 (`deployment/`)
* [x] 가상 E2E 시나리오 시뮬레이션 및 API 연동 테스트 가이드 완료 (`tests/README_test.md`)
* [ ] 에어컨 상태 장기 모니터링 테스트 및 메모리/CPU 성능 최적화