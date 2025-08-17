import json
import os

CONFIG_FILE = "prevConfig.json"
DEFAULT_SRC = "C:/Users/Public/Pictures"
DEFAULT_DST = "C:/Users/Public/Desktop"


def load_previous_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    else:
        return None  # 초기 설정 필요


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
