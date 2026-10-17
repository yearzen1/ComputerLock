import ctypes

import process_util
from process_util import (
    display_name, get_foreground_process_name, normalize_process_name
)


def test_strips_exe_extension():
    assert display_name("edge.exe") == "edge"
    assert display_name("code.exe") == "code"
    assert display_name("chrome.exe") == "chrome"


def test_strips_full_windows_path():
    assert display_name(r"D:\Program Files\Code.exe") == "Code"


def test_strips_posix_path():
    assert display_name("/usr/bin/app.exe") == "app"


def test_keeps_name_without_extension():
    assert display_name("notepad") == "notepad"


def test_case_insensitive_exe_suffix():
    assert display_name("Chrome.EXE") == "Chrome"


def test_normalize_strips_quotes_path_and_case():
    assert normalize_process_name('"D:\\Microsoft VS Code\\Code.exe"') == "code.exe"
    assert normalize_process_name("/usr/bin/app.EXE") == "app.exe"
    assert normalize_process_name("") == ""
    assert normalize_process_name(None) == ""


def test_foreground_process_name_is_bare_lowercase():
    name = get_foreground_process_name()
    assert name is None or (name == name.lower() and "\\" not in name and "/" not in name)


def test_fast_path_used_when_process_query_succeeds(monkeypatch):
    monkeypatch.setattr(process_util, "_pid_of_foreground_window", lambda: 4242)
    monkeypatch.setattr(
        process_util, "_exe_path_of_pid",
        lambda pid: r"D:\Microsoft VS Code\Code.exe"
    )

    def boom():
        raise AssertionError("snapshot fallback must not run when fast path works")

    monkeypatch.setattr(process_util, "_get_foreground_process_name_snapshot", boom)

    assert get_foreground_process_name() == "code.exe"


def test_fallback_to_snapshot_when_process_query_fails(monkeypatch):
    monkeypatch.setattr(process_util, "_pid_of_foreground_window", lambda: 4242)
    monkeypatch.setattr(process_util, "_exe_path_of_pid", lambda pid: None)
    monkeypatch.setattr(
        process_util, "_get_foreground_process_name_snapshot", lambda: "explorer.exe"
    )

    assert get_foreground_process_name() == "explorer.exe"


def test_fallback_to_snapshot_without_foreground_window(monkeypatch):
    monkeypatch.setattr(process_util, "_pid_of_foreground_window", lambda: None)
    monkeypatch.setattr(
        process_util, "_get_foreground_process_name_snapshot", lambda: "explorer.exe"
    )

    assert get_foreground_process_name() == "explorer.exe"


def test_exe_path_of_pid_returns_none_when_open_process_fails(monkeypatch):
    monkeypatch.setattr(ctypes.windll.kernel32, "OpenProcess", lambda *args, **kwargs: 0)

    assert process_util._exe_path_of_pid(1234) is None
