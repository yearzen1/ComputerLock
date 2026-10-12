import tkinter as tk
import subprocess
from datetime import datetime
import ctypes
from config import load_config
import config
from process_util import (
    SELF_EXE, normalize_process_name, display_name, get_foreground_process_name,
    install_keyboard_block, uninstall_keyboard_block, bring_window_to_front
)

LOG_FILE = "lock_debug.log"

PALETTE = {
    "bg": "#1e1e2e",
    "card": "#2a2d3e",
    "accent": "#4a9eff",
    "text": "#ffffff",
    "subtext": "#a0a4b8",
    "error": "#ff6b6b",
    "chip": "#3a4160",
}


def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {msg}\n")


def ask_password(parent, title, prompt):
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.configure(bg=PALETTE["card"])
    window_width = 320
    window_height = 170
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
    dialog.transient(parent)
    dialog.grab_set()
    tk.Label(dialog, text=prompt, font=("Segoe UI", 11),
             fg=PALETTE["text"], bg=PALETTE["card"]).pack(pady=(18, 8))
    entry = tk.Entry(dialog, font=("Segoe UI", 12), fg=PALETTE["text"], bg=PALETTE["bg"],
                     insertbackground=PALETTE["text"], relief=tk.FLAT, show="*",
                     highlightthickness=1, highlightbackground=PALETTE["chip"],
                     highlightcolor=PALETTE["accent"])
    entry.pack(pady=(0, 14), ipady=4)
    result = [None]
    def on_ok():
        result[0] = entry.get()
        dialog.destroy()
    def on_cancel():
        result[0] = None
        dialog.destroy()
    entry.bind("<Return>", lambda e: on_ok())
    entry.focus_set()
    frame = tk.Frame(dialog, bg=PALETTE["card"])
    frame.pack(pady=(0, 10))
    tk.Button(frame, text="OK", command=on_ok,
              font=("Segoe UI", 11, "bold"), fg=PALETTE["text"], bg=PALETTE["accent"],
              activebackground="#2a7ae0", activeforeground=PALETTE["text"],
              relief=tk.FLAT, bd=0, highlightthickness=0, padx=24, pady=4,
              cursor="hand2").pack(side=tk.LEFT, padx=6)
    tk.Button(frame, text="Cancel", command=on_cancel,
              font=("Segoe UI", 11), fg=PALETTE["text"], bg=PALETTE["chip"],
              activebackground="#4a5578", activeforeground=PALETTE["text"],
              relief=tk.FLAT, bd=0, highlightthickness=0, padx=24, pady=4,
              cursor="hand2").pack(side=tk.LEFT, padx=6)
    parent.wait_window(dialog)
    return result[0]


def lock_computer(password, root, on_unlock_callback):
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
    lock_window.configure(bg=PALETTE["bg"])
    lock_window.title("Locked")

    card = tk.Frame(lock_window, bg=PALETTE["card"], padx=60, pady=48,
                    highlightbackground=PALETTE["chip"], highlightthickness=1)
    card.pack(expand=True)

    week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    time_label = tk.Label(card, font=("Segoe UI", 72, "bold"), fg=PALETTE["text"], bg=PALETTE["card"])
    time_label.pack(pady=(0, 6))

    date_label = tk.Label(card, font=("Segoe UI", 16), fg=PALETTE["subtext"], bg=PALETTE["card"])
    date_label.pack(pady=(0, 2))

    week_label = tk.Label(card, font=("Segoe UI", 16), fg=PALETTE["subtext"], bg=PALETTE["card"])
    week_label.pack(pady=(0, 4))

    divider = tk.Frame(card, bg=PALETTE["accent"], height=2)
    divider.pack(fill=tk.X, pady=(16, 0))

    def update_datetime():
        now = datetime.now()
        time_label.config(text=now.strftime("%H:%M:%S"))
        date_label.config(text=now.strftime("%B %d, %Y"))
        week_label.config(text=week_days[now.weekday()])
        lock_window.after(1000, update_datetime)

    update_datetime()

    lock_label = tk.Label(card, text="🔒", font=("Segoe UI", 30), bg=PALETTE["card"], fg=PALETTE["text"])
    lock_label.pack(pady=(24, 8))

    label = tk.Label(card, text="This computer is locked",
                     font=("Segoe UI", 14, "bold"), fg=PALETTE["text"], bg=PALETTE["card"])
    label.pack()

    sub_label = tk.Label(card, text="Enter password to unlock",
                         font=("Segoe UI", 13), fg=PALETTE["subtext"], bg=PALETTE["card"])
    sub_label.pack(pady=(2, 16))

    config.reset_daily_tasks()
    daily_tasks = config.get_daily_tasks()

    if daily_tasks:
        tasks_title = tk.Label(card, text="Daily Tasks", font=("Segoe UI", 13, "bold"),
                               fg=PALETTE["accent"], bg=PALETTE["card"])
        tasks_title.pack(pady=(4, 6))

        tasks_frame = tk.Frame(card, bg=PALETTE["card"])
        tasks_frame.pack(pady=(0, 10))

        task_vars = []
        for idx, task in enumerate(daily_tasks):
            var = tk.BooleanVar(value=task["done"])
            task_vars.append(var)
            def make_cmd(i):
                def cmd():
                    config.toggle_daily_task(i)
                    error_label.config(text="")
                return cmd
            cb = tk.Checkbutton(tasks_frame, text=task["text"], variable=var,
                                font=("Segoe UI", 12), fg=PALETTE["text"], bg=PALETTE["card"],
                                selectcolor=PALETTE["bg"], activebackground=PALETTE["card"],
                                activeforeground=PALETTE["accent"],
                                command=make_cmd(idx))
            cb.pack(anchor="w", padx=30, pady=1)

    error_label = tk.Label(card, text="", font=("Segoe UI", 12, "bold"),
                           fg=PALETTE["error"], bg=PALETTE["card"])
    error_label.pack(pady=(0, 8))

    def try_unlock():
        error_label.config(text="")
        tasks = config.get_daily_tasks()
        if not all(t["done"] for t in tasks):
            error_label.config(text="Please complete all daily tasks")
            return
        pwd = ask_password(lock_window, "Unlock", "Enter password:")
        if pwd == password:
            uninstall_keyboard_block()
            lock_window.destroy()
            if root.state() in ('iconic', 'withdrawn'):
                root.deiconify()
            on_unlock_callback()
        else:
            error_label.config(text="Incorrect password.")

    def on_lockDestroy():
        uninstall_keyboard_block()
        lock_window.destroy()

    button = tk.Button(card, text="Unlock", command=try_unlock,
                       font=("Segoe UI", 13, "bold"), fg=PALETTE["text"], bg=PALETTE["accent"],
                       activebackground="#2a7ae0", activeforeground=PALETTE["text"],
                       relief=tk.FLAT, bd=0, highlightthickness=0, cursor="hand2")
    button.pack(fill=tk.X, pady=(4, 10), ipady=6)

    wl_config = config.get_whitelist()
    wl_names_lower = [normalize_process_name(w) for w in wl_config if w]
    if wl_config:
        wl_title = tk.Label(card, text="Whitelisted Apps", font=("Segoe UI", 12, "bold"),
                            fg=PALETTE["subtext"], bg=PALETTE["card"])
        wl_title.pack(pady=(10, 6))
        wl_btn_frame_inner = tk.Frame(card, bg=PALETTE["card"])
        wl_btn_frame_inner.pack(pady=(0, 4))
        for entry in wl_config:
            name = display_name(entry)
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
            tk.Button(wl_btn_frame_inner, text=name, font=("Segoe UI", 11),
                      fg=PALETTE["text"], bg=PALETTE["chip"],
                      activebackground="#4a5578", activeforeground=PALETTE["text"],
                      relief=tk.FLAT, bd=0, highlightthickness=0, padx=12, pady=4,
                      cursor="hand2",
                      command=launch_and_hide
                      ).pack(side=tk.LEFT, padx=4, pady=2)

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

    while lock_window.winfo_exists():
        lock_window.update()
