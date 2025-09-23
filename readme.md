# 배포

```
cd app
## 가상환경 진입
.\venv\Scripts\Activate
cd ..
start zipBat.bat
@echo off
:: 1. PyInstaller 빌드
pyinstaller --noconsole --onefile --icon=resources/icon.ico main.py

:: 2. ZIP 생성
powershell Compress-Archive -Path dist\main.exe -DestinationPath dist\main.zip

echo ✅ 빌드 + ZIP 완료
pause

```

# 실행

```
cd app
# 가상환경진입
python -m venv venv
# 가상환경 실행
.\venv\Scripts\Activate
# 설치
pip install -r requirements.txt
# 실행
python main.py
```

## QAction import 위치

- from PySide6.QtGui import QIcon, QAction

## requirements만들기

```
python -m pipreqs.pipreqs . --encoding=utf-8 --force
```
