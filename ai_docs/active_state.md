# Active State - LGAP Python Raw Daemon

## 1. 현재 세션 진행 상태
* **목표**: 회사 노트북 이원화 개발 환경 구축, GitHub 원격 저장소 초기화/동기화, 하드웨어 직결 테스트 매뉴얼 개정 및 터미널 패킷 로깅 가시화.
* **상태**: 완료. 가상 에어컨(MockSerial) E2E 검증 통과, 터미널 16바이트 TX/RX 패킷 실시간 로깅 반영, 회사 노트북 원클릭 셋업 스크립트([setup_env.bat](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/setup_env.bat)) 및 현장 매뉴얼([next_to_do(need to be updated).md](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/next_to_do%28need%20to%20be%20updated%29.md)) 작성 완료.

## 2. 완료된 작업 (Completed Tasks)
* **GitHub 원격 저장소 초기화 및 푸시**:
  * `https://github.com/martinchoi85-lang/lgap-python-raw.git` main 브랜치 생성 및 소스코드 전체 동기화
* **회사 노트북 이원화 환경 구축**:
  * [PRD.md](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/ai_docs/PRD.md)에 미니PC(Antigravity 개발) ↔ 회사 노트북(현장 구동/테스트) 워크플로우 명시
  * 원클릭 가상환경 생성 및 패키지 설치 배치 스크립트([setup_env.bat](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/setup_env.bat)) 작성
  * 회사 노트북용 초기 설정/테스트 가이드([COMPANY_LAPTOP_SETUP.md](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/COMPANY_LAPTOP_SETUP.md)) 작성
* **현장 하드웨어 결선 및 테스트 매뉴얼 전면 개정 ([next_to_do(need to be updated).md](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/next_to_do%28need%20to%20be%20updated%29.md))**:
  * 과거 ESP32/MQTT 구조 내용 폐기 및 USB-to-RS485 2가닥 유선 직결 구조 반영
  * 하드웨어/통신 초보자용 쉬운 개념 설명 및 회사 노트북 기준 단계별 현장 절차 수립
* **터미널 패킷 송수신 로그 개선 ([core/polling.py](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/core/polling.py))**:
  * `[POLL TX]`, `[POLL RX]` 16바이트 헥사 및 상태 갱신 정보를 `INFO` 레벨로 출력하여 터미널에서 즉각 육안 관측 가능하도록 수정
  * 가상 에어컨(`MockSerial`) 기반 E2E 폴링 및 HTTP 상태 조회(/states) 정상 동작 검증 완료
* **세션 종료 스킬 지침 업데이트 ([.agents/skills/session-end/SKILL.md](file:///c:/Users/MartinChoi/Documents/WorkSpace/lgap-python-raw/.agents/skills/session-end/SKILL.md))**:
  * IDE가 직접 Git commit 및 push까지 완결하도록 프로토콜 수정

## 3. 다음 단계 작업 (Next To-Do / Pending)
* **회사 노트북 Git Clone 및 환경 구축**: `git clone` 후 `setup_env.bat` 실행하여 venv 세팅
* **현장 실기기 물리 결선**: 에어컨 차단기 차단 ➔ 실외기 `CENA`/`CENB` 단자에 2가닥 배선 ➔ USB-to-RS485 컨버터 연결 ➔ 노트북 USB 연결
* **실물 패킷 정합성 검증**: 장치 관리자 COM 포트 확인 ➔ `config.py` 수정 ➔ `main.py` (`use_mock=False`) 실행 후 실제 실외기 16바이트 패킷 응답 확인
