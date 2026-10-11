from process_util import display_name


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
