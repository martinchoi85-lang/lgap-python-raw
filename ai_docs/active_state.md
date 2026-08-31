# Active State - LGAP Python Raw Daemon

## 1. 현재 세션 진행 상태
* **목표**: 가상 환경(`MockSerial`) 기반 통합 테스트(E2E) 시나리오 검증 수립 및 라즈베리파이 실장 배포용 `systemd` 서비스 파일 규격과 배포/운영 체크리스트 문서화.
* **상태**: 완료. 가상 시뮬레이션 E2E 테스트 가이드(`tests/README_test.md`), systemd 서비스 설정 파일(`deployment/lgap-daemon.service`), 프로덕션 실장 전환 체크리스트(`deployment/README_production.md`) 생성 완료.

## 2. 완료된 작업 (Completed Tasks)
* **회사 노트북 환경 지원 및 자동화 스크립트 작성**:
  * 원클릭 가상환경 생성 및 패키지 설치 배치 스크립트([setup_env.bat](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/setup_env.bat)) 작성
  * 회사 노트북용 초기 설정/테스트/Git 동기화 가이드([COMPANY_LAPTOP_SETUP.md](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/COMPANY_LAPTOP_SETUP.md)) 작성
* **현장 하드웨어 결선 및 테스트 매뉴얼 전면 개정 ([next_to_do(need to be updated).md](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/next_to_do%28need%20to%20be%20updated%29.md))**:
  * 과거 ESP32/MQTT 구조 내용 폐기 및 USB-to-RS485 유선 직결 구조 반영
  * 하드웨어/통신 초보자를 위한 쉬운 개념 설명 및 회사 노트북 기반 단계별 현장 절차 수립
* **GitHub 원격 저장소 동기화 완료**:
  * `https://github.com/martinchoi85-lang/lgap-python-raw.git` main 브랜치 Push 완료

## 3. 다음 단계 작업 (Next To-Do / Pending)
* **회사 노트북 Git Clone 및 가상환경 세팅**: `setup_env.bat` 실행을 통한 가상환경 구축
* **현장 USB-to-RS485 물리 결선**: 실외기 `CENA`/`CENB` 단자에 2가닥 배선 및 노트북 USB 연결
* **실물 패킷 정합성 검증**: `main.py` (`use_mock=False`) 실행 후 실제 16바이트 패킷 응답 확인 및 로그 모니터링
