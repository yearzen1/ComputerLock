import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import subprocess
from datetime import datetime
import ctypes
from config import load_config, load_shared_config, save_shared_config, reset_daily_tasks_if_new_day
from process_util import (
    SELF_EXE, normalize_process_name, get_foreground_process_name,
    install_keyboard_block, uninstall_keyboard_block, bring_window_to_front
)

LOG_FILE = "lock_debug.log"


def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {msg}\n")


def ask_password(parent, title, prompt):
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    window_width = 300
    window_height = 150
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
    dialog.transient(parent)
    dialog.grab_set()
    ttk.Label(dialog, text=prompt).pack(pady=10)
    entry = ttk.Entry(dialog, show='*')
    entry.pack(pady=5)
    result = [None]
    def on_ok():
        result[0] = entry.get()
        dialog.destroy()
    def on_cancel():
        result[0] = None
        dialog.destroy()
    entry.bind("<Return>", lambda e: on_ok())
    entry.focus_set()
    frame = ttk.Frame(dialog)
    frame.pack(pady=10)
    ttk.Button(frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
    ttk.Button(frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
    parent.wait_window(dialog)
    return result[0]


def lock_computer(duration, password, root, on_unlock_callback):
    install_keyboard_block()
    lock_window = tk.Toplevel(root)

    SM_CXVIRTUALSCREEN = 78
    SM_CYVIRTUALSCREEN = 79
    SM_XVIRTUALSCREEN = 76
    SM_YVIRTUALSCREEN = 77
    try:
        vwidth = ctypes.windll.user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        vheight = ctypes.windll.user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        vleft = ctypes.windll.user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
        vtop = ctypes.windll.user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
        lock_window.geometry(f"{vwidth}x{vheight}+{vleft}+{vtop}")
    except Exception:
        lock_window.geometry(f"{lock_window.winfo_screenwidth()}x{lock_window.winfo_screenheight()}+0+0")
    lock_window.overrideredirect(True)
    lock_window.attributes("-topmost", True)
    lock_window.configure(bg="#000000")
    lock_window.title("Locked")

    main_frame = tk.Frame(lock_window, bg="#000000", padx=20, pady=20)
    main_frame.pack(expand=True, fill='both')

    week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    time_label = tk.Label(main_frame, font=("Arial", 36, "bold"), fg="#00ff00", bg="#000000")
    time_label.pack(pady=(0, 5))

    date_label = tk.Label(main_frame, font=("Arial", 18), fg="#00ff00", bg="#000000")
    date_label.pack(pady=(0, 5))

    week_label = tk.Label(main_frame, font=("Arial", 18), fg="#00ff00", bg="#000000")
    week_label.pack(pady=(0, 20))

    def update_datetime():
        now = datetime.now()
        time_label.config(text=now.strftime("%H:%M:%S"))
        date_label.config(text=now.strftime("%B %d, %Y"))
        week_label.config(text=week_days[now.weekday()])
        lock_window.after(1000, update_datetime)

    update_datetime()

    lock_label = tk.Label(main_frame, text="🔒", font=("Arial", 48), bg="#000000", fg="#ffffff")
    lock_label.pack(pady=(0, 10))

    label = tk.Label(main_frame, text="This computer is locked\nEnter password to unlock", font=("Arial", 14, "bold"), fg="#ffffff", bg="#000000")
    label.pack(pady=(0, 10))

    shared = load_shared_config()
    reset_daily_tasks_if_new_day(shared)
    daily_tasks = shared.get("daily_tasks", [])

    if daily_tasks:
        tasks_title = tk.Label(main_frame, text="Daily Tasks", font=("Arial", 14, "bold"), fg="#00ff00", bg="#000000")
        tasks_title.pack(pady=(5, 5))

        tasks_frame = tk.Frame(main_frame, bg="#000000")
        tasks_frame.pack(pady=(0, 10))

        def make_toggle_cmd(task, var):
            def cmd():
                task["done"] = var.get()
                cfg = load_shared_config()
                cfg["daily_tasks"] = daily_tasks
                save_shared_config(cfg)
                error_label.config(text="")
            return cmd

        for task in daily_tasks:
            var = tk.BooleanVar(value=task["done"])
            cb = tk.Checkbutton(tasks_frame, text=task["text"], variable=var,
                                font=("Arial", 12), fg="#ffffff", bg="#000000",
                                selectcolor="#000000", activebackground="#333333",
                                activeforeground="#ffffff",
                                command=make_toggle_cmd(task, var))
            cb.pack(anchor="w", padx=30)

    timer_label = tk.Label(main_frame, text="", font=("Arial", 14), fg="#ffffff", bg="#000000")
    timer_label.pack(pady=(0, 10))

    error_label = tk.Label(main_frame, text="", font=("Arial", 12, "bold"),
                           fg="#ff4444", bg="#000000")
    error_label.pack(pady=(0, 10))

    def try_unlock():
        error_label.config(text="")
        if not all(t["done"] for t in daily_tasks):
            error_label.config(text="Please complete all daily tasks")
            return
        pwd = ask_password(lock_window, "Unlock", "Enter password:")
        if pwd == password:
            uninstall_keyboard_block()
            lock_window.destroy()
            if root.state() == 'iconic':
                root.deiconify()
            on_unlock_callback()
        else:
            error_label.config(text="Incorrect password.")

    def on_lockDestroy():
        uninstall_keyboard_block()
        lock_window.destroy()

    button = tb.Button(main_frame, text="Unlock", command=try_unlock, bootstyle=SUCCESS)
    button.pack(pady=(0, 10))

    wl_config = shared.get("whitelist", [])
    wl_names_lower = [normalize_process_name(w) for w in wl_config if w]
    if wl_config:
        wl_title = tk.Label(main_frame, text="Whitelisted Apps", font=("Arial", 12, "bold"), fg="#aaaaaa", bg="#000000")
        wl_title.pack(pady=(10, 5))
        wl_btn_frame_inner = tk.Frame(main_frame, bg="#000000")
        wl_btn_frame_inner.pack(pady=(0, 15))
        for entry in wl_config:
            name = entry.strip().rstrip('.exe').split('\\')[-1].split('/')[-1]
            def launch_and_hide(path=entry):
                nonlocal lock_window_hidden, _check_id
                log(f"WHITELIST_LAUNCH path={path}")
                if not lock_window_hidden:
                    lock_window_hidden = True
                    uninstall_keyboard_block()
                    lock_window.withdraw()
                    log("WHITELIST_LAUNCH window hidden")
                exe = normalize_process_name(path)
                if not bring_window_to_front(exe):
                    subprocess.Popen(path, shell=False)
                    log(f"WHITELIST_LAUNCH started new: {exe}")
                if _check_id is not None:
                    lock_window.after_cancel(_check_id)
                _check_id = lock_window.after(3000, check_foreground)
            tk.Button(wl_btn_frame_inner, text=name, font=("Arial", 11),
                      fg="#ffffff", bg="#333333", activebackground="#555555",
                      relief=tk.FLAT, padx=12, pady=4,
                      command=launch_and_hide
                      ).pack(side=tk.LEFT, padx=4)

    lock_window_hidden = False
    _check_id = None

    def check_foreground():
        nonlocal lock_window_hidden, _check_id
        fg_name = get_foreground_process_name()
        is_whitelisted = fg_name is not None and fg_name in wl_names_lower
        log(f"CHECK_FG fg_name={fg_name} whitelisted={is_whitelisted} hidden={lock_window_hidden}")
        if is_whitelisted and not lock_window_hidden:
            lock_window_hidden = True
            uninstall_keyboard_block()
            lock_window.withdraw()
            log("CHECK_FG -> hide (whitelisted foreground)")
        elif lock_window_hidden and fg_name is not None \
                and fg_name != SELF_EXE and not is_whitelisted:
            lock_window_hidden = False
            install_keyboard_block()
            lock_window.deiconify()
            lock_window.attributes("-topmost", True)
            lock_window.lift()
            log(f"CHECK_FG -> show (non-whitelisted: {fg_name})")
        _check_id = lock_window.after(1000, check_foreground)

    check_foreground()

    remaining = duration
    def update_timer():
        nonlocal remaining
        if remaining > 0:
            mins = remaining // 60
            secs = remaining % 60
            timer_label.config(text=f"Auto-unlock in {mins}m {secs}s")
            remaining -= 1
            lock_window.after(1000, update_timer)
        else:
            uninstall_keyboard_block()
            lock_window.destroy()

    update_timer()

    while lock_window.winfo_exists():
        lock_window.update()
