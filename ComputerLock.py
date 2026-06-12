import time
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

from config import migrate_old_config, load_config, save_config
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
whitelist = []


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
        config = load_config(current_mode)
        p1_start = config.get("period1_start", "22:00")
        p1_end = config.get("period1_end", "23:00")
        p2_start = config.get("period2_start", "08:00")
        p2_end = config.get("period2_end", "09:00")
        lock_duration = config.get("lock_duration", 10) * 60
        password = config.get("password", "")
        whitelist = config.get("whitelist", [])

        if check_lock_time(p1_start, p1_end, p2_start, p2_end, current_mode) and not is_locked:
            if is_whitelisted_foreground(whitelist):
                time.sleep(60)
            else:
                lock_request = (lock_duration, password)
                time.sleep(70)
        else:
            time.sleep(60)


def toggle_monitoring():
    global is_monitoring, monitor_thread, lock_entry, pwd_entry, toggle_button, period1_start_entry, period1_end_entry, period2_start_entry, period2_end_entry, mode_combo, current_mode, whitelist
    try:
        lock_min = int(lock_entry.get())
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

        lock_duration = lock_min * 60
        config = {
            "lock_duration": lock_min,
            "password": pwd,
            "period1_start": p1_start,
            "period1_end": p1_end,
            "period2_start": p2_start,
            "period2_end": p2_end,
            "whitelist": whitelist,
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
    global is_locked, lock_request, status_label, current_mode, whitelist
    config = load_config(current_mode)
    current_time = datetime.now().strftime("%H:%M:%S")
    in_lock_period = check_lock_time(
        config.get("period1_start", "22:00"),
        config.get("period1_end", "23:00"),
        config.get("period2_start", "08:00"),
        config.get("period2_end", "09:00"),
        current_mode
    )
    if current_mode == "unlock_period":
        status = "当前在免锁定时段外（应锁屏）" if in_lock_period else "当前在免锁定时段内（不锁屏）"
    else:
        status = "当前在锁定时段内（应锁屏）" if in_lock_period else "当前不在锁定时段内"
    wl = config.get("whitelist", [])
    fg_name = get_foreground_process_name()
    wl_status = f"前台进程：{fg_name}" if fg_name else ""
    if fg_name and fg_name in [normalize_process_name(w) for w in wl if w]:
        wl_status += "（白名单）"
    status_label.config(text=f"当前时间：{current_time}\n{status}\n{wl_status}")
    if lock_request and not is_locked:
        lock_duration, password = lock_request
        lock_request = None
        is_locked = True
        lock_computer(lock_duration, password, root, current_mode,
                      lambda: toggle_monitoring() if is_monitoring else None)
        is_locked = False
    root.after(1000, update_usage_label)


migrate_old_config()
config = load_config("lock_period")

root = tk.Tk()
root.title("电脑锁定设置")
root.eval('tk::PlaceWindow . center')

style = ttk.Style()
style.configure("Accent.TButton", font=("Arial", 12, "bold"), padding=10)

ttk.Label(root, text="锁定持续时间（分钟）：").grid(row=0, column=0, padx=10, pady=5)
lock_entry = ttk.Entry(root)
lock_entry.insert(0, str(config["lock_duration"]))
lock_entry.grid(row=0, column=1, padx=10, pady=5)

ttk.Label(root, text="密码：").grid(row=1, column=0, padx=10, pady=5)
pwd_entry = ttk.Entry(root, show='*')
pwd_entry.insert(0, config["password"])
pwd_entry.grid(row=1, column=1, padx=10, pady=5)

ttk.Label(root, text="锁定模式：").grid(row=2, column=0, padx=10, pady=5)
mode_combo = ttk.Combobox(root, values=["锁定时段内", "锁定时段外"], state="readonly", width=18)
mode_combo.set("锁定时段内")
mode_combo.grid(row=2, column=1, padx=10, pady=5, sticky="w")


def on_mode_change(event):
    global current_mode
    new_mode = "lock_period" if mode_combo.get() == "锁定时段内" else "unlock_period"
    if new_mode != current_mode:
        current_mode = new_mode
        load_settings_from_config()


mode_combo.bind("<<ComboboxSelected>>", on_mode_change)


def load_settings_from_config():
    global whitelist
    cfg = load_config(current_mode)
    lock_entry.delete(0, tk.END)
    lock_entry.insert(0, str(cfg.get("lock_duration", 10)))
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
    whitelist = cfg.get("whitelist", [])
    whitelist_box.delete(0, tk.END)
    for p in whitelist:
        whitelist_box.insert(tk.END, p)
    lock_entry.focus_set()


ttk.Label(root, text="锁定时段1 开始：").grid(row=3, column=0, padx=10, pady=5)
period1_start_entry = ttk.Entry(root, width=10)
period1_start_entry.insert(0, config.get("period1_start", "22:00"))
period1_start_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

ttk.Label(root, text="锁定时段1 结束：").grid(row=4, column=0, padx=10, pady=5)
period1_end_entry = ttk.Entry(root, width=10)
period1_end_entry.insert(0, config.get("period1_end", "23:00"))
period1_end_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")

ttk.Label(root, text="锁定时段2 开始：").grid(row=5, column=0, padx=10, pady=5)
period2_start_entry = ttk.Entry(root, width=10)
period2_start_entry.insert(0, config.get("period2_start", "08:00"))
period2_start_entry.grid(row=5, column=1, padx=10, pady=5, sticky="w")

ttk.Label(root, text="锁定时段2 结束：").grid(row=6, column=0, padx=10, pady=5)
period2_end_entry = ttk.Entry(root, width=10)
period2_end_entry.insert(0, config.get("period2_end", "09:00"))
period2_end_entry.grid(row=6, column=1, padx=10, pady=5, sticky="w")

toggle_button = ttk.Button(root, text="开始监控", command=toggle_monitoring)
toggle_button.grid(row=7, column=0, columnspan=2, pady=10)

status_label = ttk.Label(root, text="", font=("Arial", 12))
status_label.grid(row=8, column=0, columnspan=2, pady=5)

whitelist = config.get("whitelist", [])
wl_frame = ttk.LabelFrame(root, text="Process Whitelist", padding=5)
wl_frame.grid(row=9, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

wl_list_frame = ttk.Frame(wl_frame)
wl_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

whitelist_box = tk.Listbox(wl_list_frame, height=5, width=25)
whitelist_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
wl_scrollbar = ttk.Scrollbar(wl_list_frame, orient=tk.VERTICAL, command=whitelist_box.yview)
wl_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
whitelist_box.config(yscrollcommand=wl_scrollbar.set)

for p in whitelist:
    whitelist_box.insert(tk.END, p)

wl_btn_frame = ttk.Frame(wl_frame)
wl_btn_frame.pack(side=tk.RIGHT, padx=(10, 0), fill=tk.Y)

whitelist_entry = ttk.Entry(wl_btn_frame, width=20)
whitelist_entry.pack(pady=(0, 5))
whitelist_entry.insert(0, "chrome.exe")


def add_whitelist():
    global whitelist
    name = whitelist_entry.get().strip().strip('"')
    if name:
        whitelist.append(name)
        whitelist_box.insert(tk.END, name)
        whitelist_entry.delete(0, tk.END)


def remove_whitelist():
    global whitelist
    sel = whitelist_box.curselection()
    if sel:
        idx = sel[0]
        whitelist_box.delete(idx)
        whitelist.pop(idx)


def add_current_process():
    name = get_foreground_process_name()
    if name:
        whitelist_entry.delete(0, tk.END)
        whitelist_entry.insert(0, name)


ttk.Button(wl_btn_frame, text="Add", command=add_whitelist).pack(pady=2, fill=tk.X)
ttk.Button(wl_btn_frame, text="Remove", command=remove_whitelist).pack(pady=2, fill=tk.X)
ttk.Button(wl_btn_frame, text="Add Current", command=add_current_process).pack(pady=2, fill=tk.X)

if config["password"]:
    toggle_monitoring()

update_usage_label()

root.mainloop()
