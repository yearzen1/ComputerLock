import json
import os
from datetime import datetime

CONFIG_FILES = {
    "lock_period": "config_lock_period.json",
    "unlock_period": "config_unlock_period.json"
}
SHARED_CONFIG_FILE = "config_shared.json"

DEFAULT_CONFIG = {"lock_duration": 10, "password": "", "period1_start": "22:00", "period1_end": "23:00", "period2_start": "08:00", "period2_end": "09:00"}
DEFAULT_SHARED_CONFIG = {"whitelist": [], "daily_tasks": [], "daily_tasks_date": ""}


def get_config_file(mode):
    return CONFIG_FILES.get(mode, "config_lock_period.json")


def migrate_old_config():
    old_file = "config.json"
    if os.path.exists(old_file):
        with open(old_file, 'r') as f:
            old_config = json.load(f)
        new_file = get_config_file("lock_period")
        if not os.path.exists(new_file):
            with open(new_file, 'w') as f:
                json.dump(old_config, f)
        os.remove(old_file)

    if not os.path.exists(SHARED_CONFIG_FILE):
        save_shared_config(DEFAULT_SHARED_CONFIG.copy())

    shared = load_shared_config()
    changed = False

    for mode in ["lock_period", "unlock_period"]:
        cfg_file = get_config_file(mode)
        if os.path.exists(cfg_file):
            with open(cfg_file, 'r') as f:
                cfg = json.load(f)
            if "whitelist" in cfg and cfg["whitelist"]:
                for item in cfg["whitelist"]:
                    if item not in shared["whitelist"]:
                        shared["whitelist"].append(item)
                del cfg["whitelist"]
                with open(cfg_file, 'w') as f:
                    json.dump(cfg, f)
                changed = True

    if changed:
        save_shared_config(shared)


def load_config(mode="lock_period"):
    config_file = get_config_file(mode)
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    other_mode = "unlock_period" if mode == "lock_period" else "lock_period"
    other_file = get_config_file(other_mode)
    if os.path.exists(other_file):
        with open(other_file, 'r') as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()


def save_config(config, mode="lock_period"):
    config_file = get_config_file(mode)
    with open(config_file, 'w') as f:
        json.dump(config, f)


def load_shared_config():
    if os.path.exists(SHARED_CONFIG_FILE):
        with open(SHARED_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_SHARED_CONFIG.copy()


def save_shared_config(config):
    with open(SHARED_CONFIG_FILE, 'w') as f:
        json.dump(config, f)


def reset_daily_tasks_if_new_day(shared_cfg):
    today = datetime.now().strftime("%Y-%m-%d")
    stored_date = shared_cfg.get("daily_tasks_date", "")
    if stored_date != today:
        for task in shared_cfg.get("daily_tasks", []):
            task["done"] = False
        shared_cfg["daily_tasks_date"] = today
        save_shared_config(shared_cfg)
        return True
    return False
