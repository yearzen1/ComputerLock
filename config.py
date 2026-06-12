import json
import os

CONFIG_FILES = {
    "lock_period": "config_lock_period.json",
    "unlock_period": "config_unlock_period.json"
}

DEFAULT_CONFIG = {"lock_duration": 10, "password": "", "period1_start": "22:00", "period1_end": "23:00", "period2_start": "08:00", "period2_end": "09:00", "whitelist": []}


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
