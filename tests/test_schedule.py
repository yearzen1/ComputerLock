from datetime import datetime

from schedule import check_lock_time, parse_time


def dt(hour, minute=0):
    return datetime(2026, 10, 17, hour, minute)


def test_parse_time_handles_empty_and_values():
    assert parse_time("") is None
    assert parse_time(None) is None
    assert parse_time("8:00") == 480
    assert parse_time("22:30") == 1350


def test_locked_inside_period():
    assert check_lock_time("8:00", "22:00", "", "", "lock_period", now=dt(21, 59)) is True


def test_period_end_releases_lock_at_2201():
    assert check_lock_time("8:00", "22:00", "", "", "lock_period", now=dt(22, 1)) is False


def test_overnight_period_still_locked_after_midnight():
    assert check_lock_time("22:00", "8:00", "", "", "lock_period", now=dt(3)) is True


def test_overnight_period_releases_after_end():
    assert check_lock_time("22:00", "8:00", "", "", "lock_period", now=dt(8, 1)) is False


def test_gap_between_two_periods_releases_lock():
    args = ("8:00", "12:00", "14:00", "18:00", "lock_period")
    assert check_lock_time(*args, now=dt(13)) is False
    assert check_lock_time(*args, now=dt(15)) is True


def test_second_period_end_releases_lock():
    args = ("8:00", "12:00", "14:00", "18:00", "lock_period")
    assert check_lock_time(*args, now=dt(18, 30)) is False


def test_unlock_period_mode_releases_when_free_window_starts():
    assert check_lock_time("8:00", "22:00", "", "", "unlock_period", now=dt(14)) is False


def test_unlock_period_mode_keeps_locked_outside_free_window():
    assert check_lock_time("8:00", "22:00", "", "", "unlock_period", now=dt(23)) is True


def test_always_on_period_never_releases():
    assert check_lock_time("0:00", "24:00", "", "", "lock_period", now=dt(3)) is True
    assert check_lock_time("0:00", "24:00", "", "", "lock_period", now=dt(23, 59)) is True


def test_empty_period_never_locks():
    assert check_lock_time("", "", "", "", "lock_period", now=dt(12)) is False


def test_uses_current_time_by_default():
    now = datetime.now()
    inside = check_lock_time("0:00", "24:00", "", "", "lock_period")
    assert inside is (now.hour * 60 + now.minute < 1440)
