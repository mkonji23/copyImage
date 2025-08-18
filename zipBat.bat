@echo off
cd app
:: 1. PyInstaller 빌드
pyinstaller --noconsole --onefile --icon=resources/icon.ico main.py

:: 2. ZIP 생성
powershell Compress-Archive -Path dist\main.exe -DestinationPath  dist\main.zip -Force

echo build + zip complete!
cd ..

pause