# 배포

```
cd app

start zipBat.bat
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
