import inspect
import re

import lock_screen

PALETTE_KEYS = ("bg", "card", "accent", "text", "subtext", "error", "chip")


def test_palette_defined_and_valid():
    palette = lock_screen.PALETTE
    for key in PALETTE_KEYS:
        assert key in palette, f"missing palette key: {key}"
        value = palette[key]
        assert re.fullmatch(r"#[0-9a-fA-F]{6}", value), f"invalid color: {value}"


def test_lock_screen_uses_palette_not_legacy_colors():
    src = inspect.getsource(lock_screen)
    assert "#00ff00" not in src
    lock_src = inspect.getsource(lock_screen.lock_computer)
    assert "#000000" not in lock_src


def test_lock_computer_uses_card_container():
    lock_src = inspect.getsource(lock_screen.lock_computer)
    assert 'PALETTE["card"]' in lock_src
    assert 'PALETTE["bg"]' in lock_src
    assert 'PALETTE["accent"]' in lock_src


def test_time_label_font_is_large():
    lock_src = inspect.getsource(lock_screen.lock_computer)
    match = re.search(r'time_label\s*=\s*tk\.Label\([^)]*font=\([^,]+,\s*(\d+)', lock_src)
    assert match, "time_label with a font size not found"
    assert int(match.group(1)) >= 60


def test_ask_password_uses_dark_palette():
    dialog_src = inspect.getsource(lock_screen.ask_password)
    assert "PALETTE" in dialog_src
    assert "ttk." not in dialog_src


def test_foreground_poll_interval_is_two_seconds():
    assert lock_screen.FG_POLL_MS == 2000


def test_period_poll_interval_is_one_second():
    assert lock_screen.PERIOD_POLL_MS == 1000


def test_foreground_poller_uses_the_interval_constant():
    src = inspect.getsource(lock_screen.lock_computer)
    assert "after(FG_POLL_MS, check_foreground)" in src
