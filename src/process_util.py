import ctypes
from ctypes import wintypes
import os
import sys

SELF_EXE = os.path.basename(sys.executable).lower()


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_void_p),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False


def normalize_process_name(name):
    if not name:
        return ""
    return name.strip().strip('"').rsplit('\\', 1)[-1].rsplit('/', 1)[-1].lower()


def get_foreground_process_name():
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    pid = wintypes.DWORD()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == 0:
        return None

    TH32CS_SNAPPROCESS = 0x00000002
    snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == -1:
        return None

    pe = PROCESSENTRY32W()
    pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
    try:
        if not ctypes.windll.kernel32.Process32FirstW(snapshot, ctypes.byref(pe)):
            return None
        while True:
            if pe.th32ProcessID == pid.value:
                return pe.szExeFile.lower()
            if not ctypes.windll.kernel32.Process32NextW(snapshot, ctypes.byref(pe)):
                break
    finally:
        ctypes.windll.kernel32.CloseHandle(snapshot)
    return None


def bring_window_to_front(exe_name_lower):
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    target_pids = set()

    TH32CS_SNAPPROCESS = 0x00000002
    snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot != -1:
        pe = PROCESSENTRY32W()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        try:
            if ctypes.windll.kernel32.Process32FirstW(snapshot, ctypes.byref(pe)):
                while True:
                    if pe.szExeFile.lower() == exe_name_lower:
                        target_pids.add(pe.th32ProcessID)
                    if not ctypes.windll.kernel32.Process32NextW(snapshot, ctypes.byref(pe)):
                        break
        finally:
            ctypes.windll.kernel32.CloseHandle(snapshot)

    if not target_pids:
        return False

    found_hwnd = [None]
    def enum_callback(hwnd, lparam):
        if found_hwnd[0] is not None:
            return False
        if not ctypes.windll.user32.IsWindowVisible(hwnd):
            return True
        pid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in target_pids:
            found_hwnd[0] = hwnd
            return False
        return True

    callback = WNDENUMPROC(enum_callback)
    ctypes.windll.user32.EnumWindows(callback, 0)

    if found_hwnd[0] is not None:
        ctypes.windll.user32.ShowWindow(found_hwnd[0], 1)
        ctypes.windll.user32.SetForegroundWindow(found_hwnd[0])
        return True
    return False


def install_keyboard_block():
    if not HAS_KEYBOARD:
        return
    keyboard.block_key('windows')
    keyboard.block_key('alt')
    keyboard.block_key('tab')
    keyboard.block_key('f4')
    keyboard.block_key('esc')
    keyboard.block_key('shift')
    keyboard.block_key('ctrl')
    keyboard.block_key('delete')


def uninstall_keyboard_block():
    if not HAS_KEYBOARD:
        return
    keyboard.unhook_all()


def is_whitelisted_foreground(whitelist):
    if not whitelist:
        return False
    name = get_foreground_process_name()
    if name is None:
        return False
    return name in [normalize_process_name(w) for w in whitelist if w]
