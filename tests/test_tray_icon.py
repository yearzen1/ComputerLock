import inspect
import queue
from pathlib import Path

import lock_screen
import tray_icon

SRC_DIR = Path(__file__).resolve().parents[1] / "src"


def test_build_icon_image_is_64px_rgba():
    img = tray_icon.build_icon_image()
    assert img.size == (64, 64)
    assert img.mode == "RGBA"


def test_menu_labels():
    assert tray_icon.menu_labels() == ["显示主窗口", "退出"]


def test_make_handlers_enqueue_actions():
    actions = queue.Queue()
    handlers = tray_icon.make_handlers(actions)
    handlers["show"]()
    handlers["quit"]()
    assert actions.get_nowait() == "show"
    assert actions.get_nowait() == "quit"


def test_create_icon_uses_labels_and_default_action():
    actions = queue.Queue()
    icon = tray_icon.create_icon(actions)
    assert [item.text for item in icon.menu] == tray_icon.menu_labels()
    default_items = [item for item in icon.menu if item.default]
    assert len(default_items) == 1


def test_computerlock_source_uses_tray_instead_of_iconify():
    src = (SRC_DIR / "ComputerLock.py").read_text(encoding="utf-8")
    assert "root.iconify(" not in src
    assert "hide_to_tray" in src
    assert "WM_DELETE_WINDOW" in src


def test_lock_screen_restores_from_withdrawn():
    src = inspect.getsource(lock_screen.lock_computer)
    assert "'withdrawn'" in src
