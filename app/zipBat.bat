@echo off
:: -----------------------------
:: 1. venv 활성화
:: -----------------------------
cd %~dp0
call venv\Scripts\activate.bat

:: -----------------------------
:: 2. PyInstaller 빌드
:: -----------------------------
:: main.py 기준으로 --onefile, UPX 경로 지정
pyinstaller --onefile --noconsole --upx-dir="upx-5.0.2-win64" main.py

:: -----------------------------
:: 3. ZIP 생성
:: -----------------------------
if exist dist\main.exe (
    powershell Compress-Archive -Path dist\main.exe -DestinationPath dist\main.zip -Force
    echo ✅ build + zip complete!
) else (
    echo ❌ dist\main.exe not found. Build failed!
)

:: -----------------------------
:: 4. venv 비활성화
:: -----------------------------
deactivate

pause
