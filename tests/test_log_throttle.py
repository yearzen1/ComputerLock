import inspect

import pytest

import lock_screen

STATE = "CHECK_FG fg_name=explorer.exe whitelisted=False hidden=False"


@pytest.fixture
def log_env(tmp_path, monkeypatch):
    log_path = tmp_path / "lock_debug.log"
    clock = [0.0]
    monkeypatch.setattr(lock_screen, "LOG_FILE", str(log_path))
    monkeypatch.setattr(lock_screen, "_monotonic", lambda: clock[0])
    monkeypatch.setattr(lock_screen, "_last_log_message", None)
    monkeypatch.setattr(lock_screen, "_last_log_time", 0.0)
    return log_path, clock


def _lines(path):
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def test_repeated_state_is_throttled(log_env):
    path, _ = log_env
    for _ in range(5):
        lock_screen.log(STATE)
    assert len(_lines(path)) == 1


def test_changed_state_is_logged(log_env):
    path, _ = log_env
    lock_screen.log(STATE)
    lock_screen.log("CHECK_FG fg_name=code.exe whitelisted=True hidden=False")
    assert len(_lines(path)) == 2


def test_forced_event_always_logged(log_env):
    path, _ = log_env
    for _ in range(3):
        lock_screen.log("WHITELIST_LAUNCH path=code.exe", force=True)
    assert len(_lines(path)) == 3


def test_heartbeat_rewrites_unchanged_state(log_env):
    path, clock = log_env
    lock_screen.log(STATE)
    clock[0] = lock_screen.LOG_HEARTBEAT_S + 1
    lock_screen.log(STATE)
    assert len(_lines(path)) == 2


def test_no_heartbeat_before_interval(log_env):
    path, clock = log_env
    lock_screen.log(STATE)
    clock[0] = lock_screen.LOG_HEARTBEAT_S - 1
    lock_screen.log(STATE)
    assert len(_lines(path)) == 1


def test_rotate_renames_oversized_log(log_env):
    path, _ = log_env
    path.write_bytes(b"x" * (lock_screen.MAX_LOG_BYTES + 1))

    lock_screen.rotate_log_if_needed()

    assert not path.exists()
    assert (path.parent / (path.name + ".old")).exists()


def test_rotate_keeps_small_log(log_env):
    path, _ = log_env
    path.write_text("small", encoding="utf-8")

    lock_screen.rotate_log_if_needed()

    assert path.exists() and path.read_text(encoding="utf-8") == "small"
    assert not (path.parent / (path.name + ".old")).exists()


def test_rotate_missing_log_is_safe(log_env):
    path, _ = log_env
    lock_screen.rotate_log_if_needed()
    assert not path.exists()


def test_key_events_are_forced_in_lock_screen():
    src = inspect.getsource(lock_screen.lock_computer)
    assert "AUTO_UNLOCK" in src
    assert src.count("force=True") >= 3


def test_lock_start_rotates_log():
    src = inspect.getsource(lock_screen.lock_computer)
    assert "rotate_log_if_needed()" in src
