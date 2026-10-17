import inspect
from pathlib import Path

import lock_screen
from lock_screen import lock_computer, should_auto_unlock

SRC_DIR = Path(__file__).resolve().parents[1] / "src"


def test_no_predicate_never_auto_unlocks():
    assert should_auto_unlock(None, False) is False


def test_predicate_true_keeps_screen_locked():
    assert should_auto_unlock(lambda: True, False) is False


def test_predicate_false_releases_screen():
    assert should_auto_unlock(lambda: False, False) is True


def test_open_password_dialog_suppresses_auto_unlock():
    assert should_auto_unlock(lambda: False, True) is False


def test_lock_computer_takes_should_stay_locked():
    assert "should_stay_locked" in inspect.signature(lock_computer).parameters


def test_lock_computer_source_has_no_dead_on_lock_destroy():
    src = (SRC_DIR / "lock_screen.py").read_text(encoding="utf-8")
    assert "on_lockDestroy" not in src


def _auto_unlock_segment():
    src = inspect.getsource(lock_screen.lock_computer)
    assert "AUTO_UNLOCK" in src, "auto-unlock branch not found in lock_computer"
    return src.split("AUTO_UNLOCK", 1)[1]


def test_auto_unlock_unblocks_keyboard_and_destroys_window():
    segment = _auto_unlock_segment()
    head = segment.split("def ", 1)[0]
    assert "uninstall_keyboard_block()" in head
    assert "lock_window.destroy()" in head


def test_auto_unlock_keeps_monitoring_alive():
    segment = _auto_unlock_segment()
    head = segment.split("def ", 1)[0]
    assert "on_unlock_callback" not in head


def test_period_state_checker_reschedules_itself():
    src = inspect.getsource(lock_screen.lock_computer)
    assert "def check_lock_state" in src
    assert "after(PERIOD_POLL_MS, check_lock_state)" in src


def test_password_dialog_guards_auto_unlock():
    src = inspect.getsource(lock_screen.lock_computer)
    assert "unlock_dialog_open" in src
    assert "should_auto_unlock(should_stay_locked, unlock_dialog_open)" in src


def test_computerlock_passes_period_predicate_snapshot():
    src = (SRC_DIR / "ComputerLock.py").read_text(encoding="utf-8")
    assert "should_stay_locked=" in src
    assert "check_lock_time(" in src
