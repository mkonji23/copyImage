# 배포

```
cd app

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
python main.py
```

## QAction import 위치

- from PySide6.QtGui import QIcon, QAction

## requirements만들기

```
python -m pipreqs.pipreqs . --encoding=utf-8 --force
```
