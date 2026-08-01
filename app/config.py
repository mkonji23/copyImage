import json
import os

CONFIG_FILE = "prevConfig.json"
DEFAULT_SRC = "C:/Users/Public/Pictures"
DEFAULT_DST = "C:/Users/Public/Desktop"


DEFAULT_CONFIG = {
    "source_dir": DEFAULT_SRC,
    "target_dir": DEFAULT_DST,
    "template_dir": "",
    "users": [],
    "h_margin": 20,
    "v_margin": 20,
    "target_w": 300,
    "target_h": 160,
    "x_offset1": -5,
    "y_offset1": 104,
    "x_offset2": 0,
    "y_offset2": 154,
    "configured": False,
}


def load_previous_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    config = DEFAULT_CONFIG.copy()
                    config.update(data)
                    config["configured"] = True
                    return config
        except Exception:
            pass

    # prevConfig.json 파일이 없는 경우, 디스크에 파일을 미리 쓰지 않고 configured=False 인 딕셔너리만 반환
    default_config = DEFAULT_CONFIG.copy()
    default_config["configured"] = False
    return default_config


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

