import inspect
from pathlib import Path

import config
from lock_screen import lock_computer

SRC_DIR = Path(__file__).resolve().parents[1] / "src"


def test_default_config_has_no_lock_duration():
    assert "lock_duration" not in config.DEFAULT_CONFIG


def test_lock_computer_has_no_duration_param():
    assert "duration" not in inspect.signature(lock_computer).parameters


def test_lock_screen_source_has_no_auto_unlock_countdown():
    src = (SRC_DIR / "lock_screen.py").read_text(encoding="utf-8")
    assert "Auto-unlock" not in src
    assert "update_timer" not in src


def test_computerlock_source_has_no_lock_duration():
    src = (SRC_DIR / "ComputerLock.py").read_text(encoding="utf-8")
    assert "lock_duration" not in src
    assert "lock_entry" not in src
