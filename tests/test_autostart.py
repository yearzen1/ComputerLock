import sys

import pytest

import autostart


class FakeKey:
    def __init__(self, registry, subkey):
        self._registry = registry
        self._subkey = subkey

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeWinreg:
    HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
    REG_SZ = 1
    KEY_READ = 1
    KEY_SET_VALUE = 2

    def __init__(self):
        self.values = {}  # (hive, subkey, name) -> data

    def OpenKey(self, hive, subkey, reserved, access):
        if not any(k[:2] == (hive, subkey) for k in self.values):
            raise FileNotFoundError
        return FakeKey(self, subkey)

    def CreateKeyEx(self, hive, subkey, reserved, access):
        return FakeKey(self, subkey)

    def QueryValueEx(self, key, name):
        k = (FakeWinreg.HKEY_CURRENT_USER, key._subkey, name)
        if k not in self.values:
            raise FileNotFoundError
        return (self.values[k], FakeWinreg.REG_SZ)

    def SetValueEx(self, key, name, reserved, typ, data):
        self.values[(FakeWinreg.HKEY_CURRENT_USER, key._subkey, name)] = data

    def DeleteValue(self, key, name):
        k = (FakeWinreg.HKEY_CURRENT_USER, key._subkey, name)
        if k not in self.values:
            raise FileNotFoundError
        del self.values[k]


@pytest.fixture
def fake_winreg(monkeypatch):
    fake = FakeWinreg()
    monkeypatch.setattr(autostart, "winreg", fake)
    return fake


def test_get_command_frozen_uses_current_exe_path(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\apps\final\ComputerLock.exe")

    cmd = autostart.get_command()

    assert cmd == r'"C:\apps\final\ComputerLock.exe"'


def test_get_command_script_uses_python_and_script_paths(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\Python312\python.exe")
    monkeypatch.setattr(sys, "argv", [r"C:\proj\ComputerLock.py"])

    cmd = autostart.get_command()

    assert cmd == r'"C:\Python312\python.exe" "C:\proj\ComputerLock.py"'


def test_is_enabled_true_when_value_exists(fake_winreg):
    fake_winreg.values[("HKEY_CURRENT_USER", autostart.RUN_KEY, autostart.VALUE_NAME)] = '"x.exe"'

    assert autostart.is_enabled() is True


def test_is_enabled_false_when_no_value(fake_winreg):
    assert autostart.is_enabled() is False


def test_set_enabled_true_writes_run_value(fake_winreg, monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\apps\final\ComputerLock.exe")

    autostart.set_enabled(True)

    key = ("HKEY_CURRENT_USER", autostart.RUN_KEY, autostart.VALUE_NAME)
    assert fake_winreg.values[key] == r'"C:\apps\final\ComputerLock.exe"'
    assert autostart.is_enabled() is True


def test_set_enabled_false_deletes_run_value(fake_winreg):
    fake_winreg.values[("HKEY_CURRENT_USER", autostart.RUN_KEY, autostart.VALUE_NAME)] = '"x.exe"'

    autostart.set_enabled(False)

    assert autostart.is_enabled() is False


def test_set_enabled_false_when_value_absent_is_noop(fake_winreg):
    autostart.set_enabled(False)

    assert autostart.is_enabled() is False
