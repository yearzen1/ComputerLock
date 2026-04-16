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
    keyboard.block_key('enter')

def uninstall_keyboard_block():
    if not HAS_KEYBOARD:
        return
    keyboard.unhook_all()

is_locked = False
is_monitoring = False
monitor_thread = None
stop_event = threading.Event()
lock_request = None

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"lock_duration": 10, "password": "", "period1_start": "22:00", "period1_end": "23:00", "period2_start": "08:00", "period2_end": "09:00"}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
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

def check_lock_time(period1_start, period1_end, period2_start, period2_end):
    now = datetime.now()
    current_minutes = now.hour * 60 + now.minute

    p1_start_mins = parse_time(period1_start)
    p1_end_mins = parse_time(period1_end)
    p2_start_mins = parse_time(period2_start)
    p2_end_mins = parse_time(period2_end)

    in_period1 = False
    in_period2 = False

    if p1_start_mins <= p1_end_mins:
        in_period1 = p1_start_mins <= current_minutes < p1_end_mins
    else:
        in_period1 = current_minutes >= p1_start_mins or current_minutes < p1_end_mins

    if p2_start_mins <= p2_end_mins:
        in_period2 = p2_start_mins <= current_minutes < p2_end_mins
    else:
        in_period2 = current_minutes >= p2_start_mins or current_minutes < p2_end_mins

    return in_period1 or in_period2

def parse_time(time_str):
    parts = time_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])

def monitor_activity():
    global is_locked, lock_request

    while not stop_event.is_set():
        config = load_config()
        p1_start = config.get("period1_start", "22:00")
        p1_end = config.get("period1_end", "23:00")
        p2_start = config.get("period2_start", "08:00")
        p2_end = config.get("period2_end", "09:00")
        lock_duration = config.get("lock_duration", 10) * 60
        password = config.get("password", "")

        if check_lock_time(p1_start, p1_end, p2_start, p2_end) and not is_locked:
            lock_request = (lock_duration, password)
            time.sleep(70)
        else:
            time.sleep(60)

def toggle_monitoring():
    global is_monitoring, monitor_thread, lock_entry, pwd_entry, toggle_button, period1_start_entry, period1_end_entry, period2_start_entry, period2_end_entry
    try:
        lock_min = int(lock_entry.get())
        pwd = pwd_entry.get()
        p1_start = period1_start_entry.get()
        p1_end = period1_end_entry.get()
        p2_start = period2_start_entry.get()
        p2_end = period2_end_entry.get()

        if not pwd:
            raise ValueError("密码不能为空")

        parse_time(p1_start)
        parse_time(p1_end)
        parse_time(p2_start)
        parse_time(p2_end)

        lock_duration = lock_min * 60
        config = {
            "lock_duration": lock_min,
            "password": pwd,
            "period1_start": p1_start,
            "period1_end": p1_end,
            "period2_start": p2_start,
            "period2_end": p2_end,
        }
        save_config(config)

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
    global lock_request, status_label
    config = load_config()
    current_time = datetime.now().strftime("%H:%M:%S")
    in_lock_period = check_lock_time(config.get("period1_start", "22:00"), config.get("period1_end", "23:00"), config.get("period2_start", "08:00"), config.get("period2_end", "09:00"))
    status = "当前在锁定时段内" if in_lock_period else "当前不在锁定时段内"
    status_label.config(text=f"当前时间：{current_time}\n{status}")
    if lock_request and not is_locked:
        lock_duration, password = lock_request
        lock_request = None
        lock_computer(lock_duration, password)
    root.after(1000, update_usage_label)

# Load config
config = load_config()

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

ttk.Label(root, text="锁定时段1 开始：").grid(row=2, column=0, padx=10, pady=5)
period1_start_entry = ttk.Entry(root, width=10)
period1_start_entry.insert(0, config.get("period1_start", "22:00"))
period1_start_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

ttk.Label(root, text="锁定时段1 结束：").grid(row=3, column=0, padx=10, pady=5)
period1_end_entry = ttk.Entry(root, width=10)
period1_end_entry.insert(0, config.get("period1_end", "23:00"))
period1_end_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

ttk.Label(root, text="锁定时段2 开始：").grid(row=4, column=0, padx=10, pady=5)
period2_start_entry = ttk.Entry(root, width=10)
period2_start_entry.insert(0, config.get("period2_start", "08:00"))
period2_start_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")

ttk.Label(root, text="锁定时段2 结束：").grid(row=5, column=0, padx=10, pady=5)
period2_end_entry = ttk.Entry(root, width=10)
period2_end_entry.insert(0, config.get("period2_end", "09:00"))
period2_end_entry.grid(row=5, column=1, padx=10, pady=5, sticky="w")

toggle_button = ttk.Button(root, text="开始监控", command=toggle_monitoring)
toggle_button.grid(row=6, column=0, columnspan=2, pady=10)

status_label = ttk.Label(root, text="", font=("Arial", 12))
status_label.grid(row=7, column=0, columnspan=2, pady=5)

if config["password"]:
    toggle_monitoring()

update_usage_label()  # start updating the usage label

root.mainloop()