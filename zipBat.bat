@echo off
cd app
:: 1. PyInstaller 빌드
pyinstaller main.spec --upx-dir="./upx-5.0.2-win64"

:: 2. ZIP 생성
powershell Compress-Archive -Path dist\main.exe -DestinationPath  dist\main.zip -Force

echo build + zip complete!ㄴ