@echo off
:: 1. Activate venv
cd %~dp0
call venv\Scripts\activate.bat

:: 2. Run PyInstaller build
pyinstaller --onefile --noconsole --upx-dir="upx-5.0.2-win64" --icon="resources/icon.ico" main.py

:: 3. Create ZIP
if exist dist\main.exe (
    powershell Compress-Archive -Path dist\main.exe -DestinationPath dist\main.zip -Force
    echo build + zip complete!
) else (
    echo dist\main.exe not found. Build failed!
)

:: 4. Deactivate venv
deactivate

pause