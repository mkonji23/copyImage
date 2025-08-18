# 배포

```
cd app
pyinstaller --noconsole --onefile --icon=resources/icon.png main.py
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
