@echo off
chcp 65001 > nul
echo ========================================================
echo   LGAP Python Raw Daemon - 회사 노트북 환경 설정 스크립트
echo ========================================================
echo.

:: 1. Python 설치 확인
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python이 시스템 PATH에 등록되어 있지 않습니다.
    echo Python 3.10 이상이 설치되어 있는지 확인하거나 경로를 지정해주세요.
    echo (기본 경로 C:\Python314\python.exe 확인 중...)
    if exist "C:\Python314\python.exe" (
        set "PY_CMD=C:\Python314\python.exe"
        echo [OK] C:\Python314\python.exe 를 찾았습니다.
    ) else (
        echo [ERROR] Python을 찾을 수 없습니다. 설치 후 다시 시도해주세요.
        pause
        exit /b 1
    )
) else (
    set "PY_CMD=python"
)

echo [1/3] Python 버전 확인:
%PY_CMD% --version
if %errorlevel% neq 0 (
    echo [ERROR] Python 실행에 실패했습니다.
    pause
    exit /b 1
)
echo.

:: 2. 가상환경 (venv) 생성
if not exist "venv" (
    echo [2/3] 가상환경(venv) 생성 중...
    %PY_CMD% -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] 가상환경 생성 실패!
        pause
        exit /b 1
    )
    echo [OK] venv 생성 완료.
) else (
    echo [2/3] 기존 venv 가상환경이 존재합니다. 건너뜁니다.
)
echo.

:: 3. 종속성 패키지 설치 (pyserial)
echo [3/3] 필수 라이브러리(pyserial) 설치 및 업그레이드 중...
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install pyserial

if %errorlevel% neq 0 (
    echo [ERROR] 패키지 설치 중 오류가 발생했습니다.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo   [성공] 환경 설정이 완료되었습니다!
echo ========================================================
echo.
echo [실행 방법 안내]
echo 1. 가상환경 활성화:
echo    .\venv\Scripts\activate
echo.
echo 2. 가상 시뮬레이션(Mock) 테스트 실행:
echo    python main.py
echo.
echo 3. 실물 RS-485 장비 연결 후 실행:
echo    config.py 에서 SERIAL_PORT 설정 (예: 'COM3')
echo    main.py 에서 use_mock=False 로 변경 후 python main.py
echo ========================================================
echo.
pause
