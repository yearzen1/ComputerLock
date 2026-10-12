import os
import sys
import time
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(APP_DIR)

from config import migrate_old_config, load_config, save_config
import config
import autostart
from process_util import (
    SELF_EXE, normalize_process_name, get_foreground_process_name,
    is_whitelisted_foreground
)
from lock_screen import lock_computer

is_locked = False
is_monitoring = False
monitor_thread = None
stop_event = threading.Event()
lock_request = None
current_mode = "lock_period"


def check_lock_time(period1_start, period1_end, period2_start, period2_end, mode="lock_period"):
    now = datetime.now()
    current_minutes = now.hour * 60 + now.minute

    def parse_time(t):
        if not t:
            return None
        parts = t.split(":")
        return int(parts[0]) * 60 + int(parts[1])

    p1_start_mins = parse_time(period1_start)
    p1_end_mins = parse_time(period1_end)
    p2_start_mins = parse_time(period2_start)
    p2_end_mins = parse_time(period2_end)

    def in_period(start_mins, end_mins):
        if start_mins is None or end_mins is None:
            return False
        if start_mins <= end_mins:
            return start_mins <= current_minutes < end_mins
        else:
            return current_minutes >= start_mins or current_minutes < end_mins

    in_period1 = in_period(p1_start_mins, p1_end_mins)
    in_period2 = in_period(p2_start_mins, p2_end_mins)

    if mode == "unlock_period":
        return not in_period1 and not in_period2
    return in_period1 or in_period2


def parse_time(time_str):
    if not time_str:
        return None
    parts = time_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])


def monitor_activity():
    global is_locked, lock_request, current_mode

    while not stop_event.is_set():
        cfg = load_config(current_mode)
        p1_start = cfg.get("period1_start", "22:00")
        p1_end = cfg.get("period1_end", "23:00")
        p2_start = cfg.get("period2_start", "08:00")
        p2_end = cfg.get("period2_end", "09:00")
        password = cfg.get("password", "")
        wl = config.get_whitelist()

        if check_lock_time(p1_start, p1_end, p2_start, p2_end, current_mode) and not is_locked:
            if is_whitelisted_foreground(wl):
                time.sleep(60)
            else:
                lock_request = password
                time.sleep(70)
        else:
            time.sleep(60)


def toggle_monitoring():
    global is_monitoring, monitor_thread, pwd_entry, toggle_button, period1_start_entry, period1_end_entry, period2_start_entry, period2_end_entry, mode_combo, current_mode
    try:
        pwd = pwd_entry.get()
        p1_start = period1_start_entry.get()
        p1_end = period1_end_entry.get()
        p2_start = period2_start_entry.get()
        p2_end = period2_end_entry.get()
        mode_val = mode_combo.get()
        current_mode = "lock_period" if mode_val == "锁定时段内" else "unlock_period"

        if not pwd:
            raise ValueError("密码不能为空")

        for t in [p1_start, p1_end, p2_start, p2_end]:
            if t:
                parse_time(t)

        config = {
            "password": pwd,
            "period1_start": p1_start,
            "period1_end": p1_end,
            "period2_start": p2_start,
            "period2_end": p2_end,
        }
        save_config(config, current_mode)

        if not is_monitoring:
            stop_event.clear()
            monitor_thread = threading.Thread(target=monitor_activity, daemon=True)
            monitor_thread.start()
            is_monitoring = True
            toggle_button.config(text="停止监控")
            root.iconify()
        else:
            stop_event.set()
            if monitor_thread:
                monitor_thread.join(timeout=2)
            is_monitoring = False
            toggle_button.config(text="开始监控")
    except ValueError as e:
        messagebox.showerror("错误", "请输入有效的时间格式（HH:MM）")
    except Exception as e:
        messagebox.showerror("错误", str(e))


def update_usage_label():
    global is_locked, lock_request, status_label, current_mode
    cfg = load_config(current_mode)
    current_time = datetime.now().strftime("%H:%M:%S")
    in_lock_period = check_lock_time(
        cfg.get("period1_start", "22:00"),
        cfg.get("period1_end", "23:00"),
        cfg.get("period2_start", "08:00"),
        cfg.get("period2_end", "09:00"),
        current_mode
    )
    if current_mode == "unlock_period":
        status = "当前在免锁定时段外（应锁屏）" if in_lock_period else "当前在免锁定时段内（不锁屏）"
    else:
        status = "当前在锁定时段内（应锁屏）" if in_lock_period else "当前不在锁定时段内"
    wl = config.get_whitelist()
    fg_name = get_foreground_process_name()
    wl_status = f"前台进程：{fg_name}" if fg_name else ""
    if fg_name and fg_name in [normalize_process_name(w) for w in wl if w]:
        wl_status += "（白名单）"
    status_label.config(text=f"当前时间：{current_time}\n{status}\n{wl_status}")
    if lock_request and not is_locked:
        password = lock_request
        lock_request = None
        is_locked = True
        lock_computer(password, root,
                      lambda: toggle_monitoring() if is_monitoring else None)
        is_locked = False
        load_settings_from_config()
    root.after(1000, update_usage_label)


def load_shared_settings():
    config.reset_daily_tasks()


def rebuild_daily_tasks_listbox():
    daily_tasks_box.delete(0, tk.END)
    for task in config.get_daily_tasks():
        prefix = "✓" if task["done"] else " "
        daily_tasks_box.insert(tk.END, f"[{prefix}] {task['text']}")


def toggle_daily_task():
    sel = daily_tasks_box.curselection()
    if sel:
        config.toggle_daily_task(sel[0])
        rebuild_daily_tasks_listbox()


def add_daily_task():
    text = daily_task_entry.get().strip()
    if text:
        config.add_daily_task(text)
        rebuild_daily_tasks_listbox()
        daily_task_entry.delete(0, tk.END)


def remove_daily_task():
    sel = daily_tasks_box.curselection()
    if sel:
        config.remove_daily_task(sel[0])
        rebuild_daily_tasks_listbox()


migrate_old_config()
if not config.is_autostart_migrated():
    try:
        autostart.set_enabled(True)
        config.mark_autostart_migrated()
    except OSError:
        pass
cfg_init = load_config("lock_period")
load_shared_settings()

root = tk.Tk()
root.title("电脑锁定设置")
root.minsize(460, 380)

style = ttk.Style()
style.configure("Accent.TButton", font=("Arial", 12, "bold"), padding=10)

notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

panel_lock = ttk.Frame(notebook, padding=12)
panel_wl = ttk.Frame(notebook, padding=12)
panel_dt = ttk.Frame(notebook, padding=12)
notebook.add(panel_lock, text="  锁定设置  ")
notebook.add(panel_wl, text="  白名单  ")
notebook.add(panel_dt, text="  每日任务  ")

panel_lock.grid_columnconfigure(0, weight=1)
panel_lock.grid_columnconfigure(1, weight=1)
panel_lock.grid_columnconfigure(2, weight=1)

ttk.Label(panel_lock, text="锁定模式").grid(row=0, column=0, padx=6, pady=(4, 2), sticky="w")
mode_combo = ttk.Combobox(panel_lock, values=["锁定时段内", "锁定时段外"], state="readonly", width=14)
mode_combo.set("锁定时段内")
mode_combo.grid(row=1, column=0, columnspan=3, padx=6, pady=(0, 4), sticky="ew")

ttk.Label(panel_lock, text="密码").grid(row=2, column=0, columnspan=3, padx=6, pady=(4, 2), sticky="w")
pwd_entry = ttk.Entry(panel_lock, show='*', width=24)
pwd_entry.insert(0, cfg_init["password"])
pwd_entry.grid(row=3, column=0, columnspan=3, padx=6, pady=(0, 6), sticky="ew")

ttk.Label(panel_lock, text="开始时间").grid(row=4, column=1, padx=6, pady=(6, 2), sticky="w")
ttk.Label(panel_lock, text="结束时间").grid(row=4, column=2, padx=6, pady=(6, 2), sticky="w")

ttk.Label(panel_lock, text="时段1").grid(row=5, column=0, padx=6, pady=3, sticky="w")
period1_start_entry = ttk.Entry(panel_lock, width=8)
period1_start_entry.insert(0, cfg_init.get("period1_start", "22:00"))
period1_start_entry.grid(row=5, column=1, padx=6, pady=3, sticky="ew")
period1_end_entry = ttk.Entry(panel_lock, width=8)
period1_end_entry.insert(0, cfg_init.get("period1_end", "23:00"))
period1_end_entry.grid(row=5, column=2, padx=6, pady=3, sticky="ew")

ttk.Label(panel_lock, text="时段2").grid(row=6, column=0, padx=6, pady=3, sticky="w")
period2_start_entry = ttk.Entry(panel_lock, width=8)
period2_start_entry.insert(0, cfg_init.get("period2_start", "08:00"))
period2_start_entry.grid(row=6, column=1, padx=6, pady=3, sticky="ew")
period2_end_entry = ttk.Entry(panel_lock, width=8)
period2_end_entry.insert(0, cfg_init.get("period2_end", "09:00"))
period2_end_entry.grid(row=6, column=2, padx=6, pady=3, sticky="ew")

autostart_var = tk.BooleanVar(value=autostart.is_enabled())


def on_autostart_toggle():
    try:
        autostart.set_enabled(autostart_var.get())
    except OSError as e:
        messagebox.showerror("错误", f"设置开机自启动失败：{e}")
        autostart_var.set(autostart.is_enabled())


autostart_check = ttk.Checkbutton(panel_lock, text="开机自启动", variable=autostart_var, command=on_autostart_toggle)
autostart_check.grid(row=7, column=0, columnspan=3, padx=6, pady=(6, 2), sticky="w")


def on_mode_change(event):
    global current_mode
    new_mode = "lock_period" if mode_combo.get() == "锁定时段内" else "unlock_period"
    if new_mode != current_mode:
        current_mode = new_mode
        load_settings_from_config()


mode_combo.bind("<<ComboboxSelected>>", on_mode_change)


def load_settings_from_config():
    cfg = load_config(current_mode)
    pwd_entry.delete(0, tk.END)
    pwd_entry.insert(0, cfg.get("password", ""))
    period1_start_entry.delete(0, tk.END)
    period1_start_entry.insert(0, cfg.get("period1_start", "22:00"))
    period1_end_entry.delete(0, tk.END)
    period1_end_entry.insert(0, cfg.get("period1_end", "23:00"))
    period2_start_entry.delete(0, tk.END)
    period2_start_entry.insert(0, cfg.get("period2_start", "08:00"))
    period2_end_entry.delete(0, tk.END)
    period2_end_entry.insert(0, cfg.get("period2_end", "09:00"))
    load_shared_settings()
    whitelist_box.delete(0, tk.END)
    for p in config.get_whitelist():
        whitelist_box.insert(tk.END, p)
    rebuild_daily_tasks_listbox()
    pwd_entry.focus_set()


status_label = ttk.Label(panel_lock, text="", font=("Arial", 11), anchor="w", justify="left")
status_label.grid(row=8, column=0, columnspan=3, padx=6, pady=(6, 2), sticky="ew")

toggle_button = ttk.Button(panel_lock, text="开始监控", command=toggle_monitoring)
toggle_button.grid(row=9, column=0, columnspan=3, padx=6, pady=(8, 2), sticky="ew", ipady=2)

ttk.Label(panel_wl, text="白名单程序位于前台时锁屏自动隐藏", foreground="#888888").pack(anchor="w", pady=(0, 8))

wl_main = ttk.Frame(panel_wl)
wl_main.pack(fill=tk.BOTH, expand=True)

whitelist_box = tk.Listbox(wl_main, height=10, width=32)
wl_hscrollbar = ttk.Scrollbar(wl_main, orient=tk.HORIZONTAL, command=whitelist_box.xview)
wl_hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
wl_scrollbar = ttk.Scrollbar(wl_main, orient=tk.VERTICAL, command=whitelist_box.yview)
wl_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
whitelist_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
whitelist_box.config(yscrollcommand=wl_scrollbar.set, xscrollcommand=wl_hscrollbar.set)

for p in config.get_whitelist():
    whitelist_box.insert(tk.END, p)

wl_ctrl = ttk.Frame(panel_wl)
wl_ctrl.pack(fill=tk.X, pady=(8, 0))
wl_ctrl_inner = ttk.Frame(wl_ctrl)
wl_ctrl_inner.pack(anchor="center")

whitelist_entry = ttk.Entry(wl_ctrl_inner, width=28)
whitelist_entry.pack(pady=(0, 6))
whitelist_entry.insert(0, "chrome.exe")


def add_whitelist():
    name = whitelist_entry.get().strip().strip('"')
    if name:
        config.add_to_whitelist(name)
        whitelist_entry.delete(0, tk.END)
        whitelist_box.insert(tk.END, name)


def remove_whitelist():
    sel = whitelist_box.curselection()
    if sel:
        idx = sel[0]
        whitelist_box.delete(idx)
        config.remove_from_whitelist(idx)


def add_current_process():
    name = get_foreground_process_name()
    if name:
        whitelist_entry.delete(0, tk.END)
        whitelist_entry.insert(0, name)


ttk.Button(wl_ctrl_inner, text="Add", command=add_whitelist).pack(side=tk.LEFT, padx=3)
ttk.Button(wl_ctrl_inner, text="Remove", command=remove_whitelist).pack(side=tk.LEFT, padx=3)
ttk.Button(wl_ctrl_inner, text="Add Current", command=add_current_process).pack(side=tk.LEFT, padx=3)

ttk.Label(panel_dt, text="锁屏时需完成全部每日任务才能解锁", foreground="#888888").pack(anchor="w", pady=(0, 8))

dt_main = ttk.Frame(panel_dt)
dt_main.pack(fill=tk.BOTH, expand=True)

daily_tasks_box = tk.Listbox(dt_main, height=10, width=32)
dt_hscrollbar = ttk.Scrollbar(dt_main, orient=tk.HORIZONTAL, command=daily_tasks_box.xview)
dt_hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
dt_scrollbar = ttk.Scrollbar(dt_main, orient=tk.VERTICAL, command=daily_tasks_box.yview)
dt_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
daily_tasks_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
daily_tasks_box.config(yscrollcommand=dt_scrollbar.set, xscrollcommand=dt_hscrollbar.set)

rebuild_daily_tasks_listbox()

dt_ctrl = ttk.Frame(panel_dt)
dt_ctrl.pack(fill=tk.X, pady=(8, 0))
dt_ctrl_inner = ttk.Frame(dt_ctrl)
dt_ctrl_inner.pack(anchor="center")

daily_task_entry = ttk.Entry(dt_ctrl_inner, width=28)
daily_task_entry.pack(pady=(0, 6))
daily_task_entry.insert(0, "New task")

ttk.Button(dt_ctrl_inner, text="Toggle", command=toggle_daily_task).pack(side=tk.LEFT, padx=3)
ttk.Button(dt_ctrl_inner, text="Add Task", command=add_daily_task).pack(side=tk.LEFT, padx=3)
ttk.Button(dt_ctrl_inner, text="Remove Task", command=remove_daily_task).pack(side=tk.LEFT, padx=3)

if cfg_init["password"]:
    toggle_monitoring()

update_usage_label()

root.update_idletasks()
_w = min(root.winfo_reqwidth() + 40, root.winfo_screenwidth() - 80)
_h = min(root.winfo_reqheight() + 40, root.winfo_screenheight() - 120)
root.geometry(f"{_w}x{_h}")
root.eval('tk::PlaceWindow . center')

root.mainloop()
