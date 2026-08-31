# Active State - LGAP Python Raw Daemon

## 1. 현재 세션 진행 상태
* **목표**: 가상 환경(`MockSerial`) 기반 통합 테스트(E2E) 시나리오 검증 수립 및 라즈베리파이 실장 배포용 `systemd` 서비스 파일 규격과 배포/운영 체크리스트 문서화.
* **상태**: 완료. 가상 시뮬레이션 E2E 테스트 가이드(`tests/README_test.md`), systemd 서비스 설정 파일(`deployment/lgap-daemon.service`), 프로덕션 실장 전환 체크리스트(`deployment/README_production.md`) 생성 완료.

## 2. 완료된 작업 (Completed Tasks)
* **통합 시뮬레이션 테스트 가이드 작성 (`tests/README_test.md`)**:
  * 데몬 구동 검증 (순차 폴링 및 로그 형식 정의)
  * GET /states API 상태 조회 검증 (HTTP 200/404 및 JSON 규격 정의)
  * POST /control 제어 명령 주입 및 Preemption 피드백 루프(API 수신 → 큐 적재 → 엔진 가로채기 → MockSerial 갱신 → 응답 수신) 관측 가이드 수립
  * Graceful Shutdown 종료 시퀀스 검증 및 체크리스트 정리
* **systemd 서비스 등록 파일 생성 (`deployment/lgap-daemon.service`)**:
  * `Description`, `After`, `WorkingDirectory`, `ExecStart` 지정
  * 데몬 크래시 대비 자동 재시작(`Restart=always`, `RestartSec=5`) 설정
  * systemd journal 로그 수집 설정 및 `ProtectSystem=full` 보안 샌드박싱 추가
* **프로덕션 실장 전환 체크리스트 작성 (`deployment/README_production.md`)**:
  * `main.py` 내 `use_mock=False` 스위칭 가이드 및 `config.py` 시리얼 포트 경로 매핑 지침
  * `/dev/ttyUSB0` 장치 권한 에러 해결을 위한 `dialout` 그룹 권한 부여 명령어 명시
  * systemd 등록/제어(enable, start, status, restart) 절차 정리
  * `journalctl -u lgap-daemon -f` 실시간 포트 디버깅 및 바이트 필드 의미/체크섬 오류 해결 가이드 수립

## 3. 다음 단계 작업 (Next To-Do / Pending)
* **실기기 현장 물리 결선**: USB-to-RS485 컨버터를 통한 에어컨 실외기 CENA/CENB 단자 배선 완료
* **포트 권한 설정 및 데몬 가동**: 라즈베리파이에 dialout 그룹 할당 후 `lgap-daemon.service` 구동 및 동작 확인
* **실물 패킷 정합성 검증**: 실제 운전 중 발생하는 패킷 및 체크섬 오류 모니터링을 통한 디코딩 안정화
