# 회사 노트북 초기 설정 및 테스트 가이드 (Company Laptop Setup & Run Guide)

본 문서는 회사 보안 정책상 Antigravity IDE를 사용할 수 없는 **회사 업무용 노트북(Windows)**에서 코드를 받아 가상환경을 구축하고, 가상 시뮬레이션 및 실제 RS-485 실외기 테스트를 수행하는 절차를 설명합니다.

---

## 1. 최초 저장소 복제 (Git Clone)

회사 노트북의 작업 폴더(예: `C:\Users\martin85.choi\Documents\Workspace\`)에서 터미널(PowerShell 또는 CMD)을 열고 아래 명령어를 실행합니다.

```powershell
# 작업 디렉토리 이동
cd C:\Users\martin85.choi\Documents\Workspace

# GitHub 저장소 복제
git clone https://github.com/martinchoi85-lang/lgap-python-raw.git

# 프로젝트 폴더 진입
cd lgap-python-raw
```

---

## 2. 가상환경 구축 (2가지 방법 중 택1)

### 방법 A. 자동 스크립트 실행 (권장)
프로젝트 루트에 있는 `setup_env.bat` 파일을 탐색기에서 **더블 클릭**하거나 터미널에서 실행합니다.
```cmd
setup_env.bat
```
*(Python venv 생성 및 `pyserial` 패키지 자동 설치가 한 번에 완료됩니다.)*

### 방법 B. 수동 터미널 명령 실행
```powershell
# 1. 가상환경 생성 (Python 3.10+ 기준)
python -m venv venv

# 2. pip 업그레이드 및 pyserial 설치
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install pyserial
```

---

## 3. 1단계: 가상 시뮬레이션(Mock) 테스트 실행

실제 에어컨 기기에 연결하기 전, 소프트웨어 엔진이 정상 동작하는지 노트북 단독으로 검증합니다.

```powershell
# 가상환경 활성화
.\venv\Scripts\activate

# 데몬 실행 (기본 use_mock=True 로 가상 에어컨 작동)
python main.py
```

### 정상 실행 화면 확인:
1. 터미널에 `[INFO] LGAP Engine 스케줄러가 시작되었습니다.` 및 `API Server started on port 8080` 출력
2. 1초 간격으로 실내기 번호별 패킷 송수신 로그 및 파싱된 상태가 실시간으로 출력됩니다:
   ```text
   2026-08-31 15:16:00 [INFO] root - [POLL TX] 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00
   2026-08-31 15:16:00 [INFO] root - [POLL RX] 00 01 00 00 00 00 04 09 72 90 00 00 00 00 00 54
   2026-08-31 15:16:00 [INFO] root - [STATE] Unit 1 -> Target: 24°C, Room: 26.0°C, Pipe: 15.0°C
   ```
3. 별도 터미널 또는 웹 브라우저에서 상태 조회 확인:
   * **PowerShell**: `curl.exe http://127.0.0.1:8080/states` (또는 `Invoke-RestMethod http://127.0.0.1:8080/states`)
   * **CMD**: `curl http://127.0.0.1:8080/states`
   * **웹 브라우저**: 주소창에 `http://localhost:8080/states` 입력
4. 종료 시: 데몬 터미널 창에서 `Ctrl + C` (Graceful Shutdown)

---

## 4. 2단계: 현장 실기기(RS-485) 연결 및 실물 테스트

실제 실외기 단자대와 노트북을 연결하여 테스트할 때의 단계입니다.

### 4.1 USB to RS-485 컨버터 COM 포트 확인
1. **USB to RS-485 컨버터**를 노트북 USB 포트에 꽂습니다.
2. Windows 시작 버튼 우클릭 ➔ **[장치 관리자]** 실행
3. **[포트 (COM & LPT)]** 항목을 펼쳐 인식된 번호 확인 (예: `USB-SERIAL CH340 (COM3)` 또는 `USB Serial Port (COM4)`)

### 4.2 설정 파일 수정
1. **`config.py`** 파일 열기:
   ```python
   # Windows COM 포트 번호로 변경
   SERIAL_PORT = "COM3"  # 장치 관리자에서 확인한 포트 번호
   ```
2. **`main.py`** 파일 열기 (하단 `controller` 인스턴스화 부분):
   ```python
   # use_mock을 False로 변경하여 실제 시리얼 포트 열기
   controller = DaemonController(use_mock=False)
   ```

### 4.3 실기기 데몬 실행
```powershell
python main.py
```
* 실외기로부터 실제 응답이 수신되면 `[POLL RX] 02 00 00 ...` 로그와 함께 현재 온도, 동작 상태가 파싱되어 출력됩니다.

---

## 5. 미니PC와의 코드 동기화 워크플로우

1. **미니PC에서 코드 수정 후 Push한 경우 (회사 노트북에서 최신 코드 받기):**
   ```powershell
   git pull origin main
   ```
2. **회사 노트북에서 현장 테스트 중 긴급 수정한 경우 (미니PC로 올리기):**
   ```powershell
   git add .
   git commit -m "Fix: 현장 테스트 패킷 파싱 파라미터 조정"
   git push origin main
   ```
