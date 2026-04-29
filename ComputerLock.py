import time
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import threading
import json
import os
from datetime import datetime

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

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

is_locked = False
is_monitoring = False
monitor_thread = None
stop_event = threading.Event()
lock_request = None
current_mode = "lock_period"

CONFIG_FILES = {
    "lock_period": "config_lock_period.json",
    "unlock_period": "config_unlock_period.json"
}

DEFAULT_CONFIG = {"lock_duration": 10, "password": "", "period1_start": "22:00", "period1_end": "23:00", "period2_start": "08:00", "period2_end": "09:00"}

def get_config_file(mode):
    return CONFIG_FILES.get(mode, "config_lock_period.json")

def migrate_old_config():
    old_file = "config.json"
    if os.path.exists(old_file):
        with open(old_file, 'r') as f:
            old_config = json.load(f)
        new_file = get_config_file("lock_period")
        if not os.path.exists(new_file):
            with open(new_file, 'w') as f:
                json.dump(old_config, f)
        os.remove(old_file)

def load_config(mode="lock_period"):
    config_file = get_config_file(mode)
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    other_mode = "unlock_period" if mode == "lock_period" else "lock_period"
    other_file = get_config_file(other_mode)
    if os.path.exists(other_file):
        with open(other_file, 'r') as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

def save_config(config, mode="lock_period"):
    config_file = get_config_file(mode)
    with open(config_file, 'w') as f:
        json.dump(config, f)

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
    ttk.Button(frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=5)
    ttk.Button(frame, text="取消", command=on_cancel).pack(side=tk.LEFT, padx=5)
    parent.wait_window(dialog)
    return result[0]

def lock_computer(duration, password):
    global is_locked
    is_locked = True
    install_keyboard_block()
    # Use Toplevel instead of new Tk() to avoid multiple Tk instances
    lock_window = tk.Toplevel(root)
    # 支持多显示器：使用虚拟屏幕尺寸覆盖所有显示器
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
        # 回退到单显示器全屏
        lock_window.geometry(f"{lock_window.winfo_screenwidth()}x{lock_window.winfo_screenheight()}+0+0")
    lock_window.overrideredirect(True)  # remove window decorations to disable minimize, drag, close
    lock_window.attributes("-topmost", True)
    lock_window.configure(bg="#000000")  # 现代深色背景
    lock_window.title("已锁定")

    # 主框架（使用 tk.Frame 以便设置背景色）
    main_frame = tk.Frame(lock_window, bg="#000000", padx=20, pady=20)
    main_frame.pack(expand=True, fill='both')

    week_days = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

    time_label = tk.Label(main_frame, font=("Arial", 36, "bold"), fg="#00ff00", bg="#000000")
    time_label.pack(pady=(0, 5))

    date_label = tk.Label(main_frame, font=("Arial", 18), fg="#00ff00", bg="#000000")
    date_label.pack(pady=(0, 5))

    week_label = tk.Label(main_frame, font=("Arial", 18), fg="#00ff00", bg="#000000")
    week_label.pack(pady=(0, 20))

    def update_datetime():
        now = datetime.now()
        time_label.config(text=now.strftime("%H:%M:%S"))
        date_label.config(text=now.strftime(f"{now.year}年%m月%d日"))
        week_label.config(text=week_days[now.weekday()])
        lock_window.after(1000, update_datetime)

    update_datetime()

    # 锁图标（用文本模拟）
    lock_label = tk.Label(main_frame, text="🔒", font=("Arial", 48), bg="#000000", fg="#ffffff")
    lock_label.pack(pady=(0, 10))

    # 锁定消息
    label = tk.Label(main_frame, text="电脑已锁定。输入密码解锁。", font=("Arial", 16, "bold"), fg="#ffffff", bg="#000000")
    label.pack(pady=(0, 20))

    # 计时器
    timer_label = tk.Label(main_frame, text="", font=("Arial", 14), fg="#ffffff", bg="#000000")
    timer_label.pack(pady=(0, 20))

    # 解锁按钮
    def try_unlock():
        pwd = ask_password(lock_window, "解锁", "输入密码：")
        if pwd == password:
            uninstall_keyboard_block()
            lock_window.destroy()
            if root.state() == 'iconic':
                root.deiconify()
            if is_monitoring:
                toggle_monitoring()
        else:
            messagebox.showerror("错误", "密码错误。")

    def on_lockDestroy():
        uninstall_keyboard_block()
        lock_window.destroy()

    button = ttk.Button(main_frame, text="解锁", command=try_unlock, style="Accent.TButton")
    button.pack(pady=(0, 10))

    remaining = duration
    def update_timer():
        nonlocal remaining
        if remaining > 0:
            mins = remaining // 60
            secs = remaining % 60
            timer_label.config(text=f"自动解锁剩余 {mins} 分钟 {secs} 秒")
            remaining -= 1
            lock_window.after(1000, update_timer)
        else:
            uninstall_keyboard_block()
            lock_window.destroy()

    update_timer()
    # Wait for window to be destroyed
    lock_window.wait_window()
    is_locked = False

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

        if check_lock_time(p1_start, p1_end, p2_start, p2_end, current_mode) and not is_locked:
            lock_request = (lock_duration, password)
            time.sleep(70)
        else:
            time.sleep(60)

def toggle_monitoring():
    global is_monitoring, monitor_thread, lock_entry, pwd_entry, toggle_button, period1_start_entry, period1_end_entry, period2_start_entry, period2_end_entry, mode_combo, current_mode
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
    global lock_request, status_label, current_mode
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
    status_label.config(text=f"当前时间：{current_time}\n{status}")
    if lock_request and not is_locked:
        lock_duration, password = lock_request
        lock_request = None
        lock_computer(lock_duration, password)
    root.after(1000, update_usage_label)

# Load config
migrate_old_config()
config = load_config("lock_period")

root = tk.Tk()
root.title("电脑锁定设置")
root.eval('tk::PlaceWindow . center')

# 设置ttk样式
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

if config["password"]:
    toggle_monitoring()

update_usage_label()  # start updating the usage label

root.mainloop()