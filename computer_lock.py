import time
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import threading
import json
import os

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]

is_locked = False  # global flag for lock status
is_monitoring = False
monitor_thread = None
stop_event = threading.Event()
continuous_usage = 0  # global variable for continuous usage
lock_request = None  # flag to request lock from main thread

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"usage_threshold": 30, "lock_duration": 10, "password": "", "continuous_mode": False}

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

def mute_system():
   pass

def get_idle_time():
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
    return (ctypes.windll.kernel32.GetTickCount() - lii.dwTime) / 1000.0

def lock_computer(duration, password):
    global is_locked
    is_locked = True
    mute_system()  # 静音系统
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
            lock_window.destroy()
        else:
            messagebox.showerror("错误", "密码错误。")

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
            lock_window.destroy()

    update_timer()
    # Wait for window to be destroyed
    lock_window.wait_window()
    is_locked = False

def monitor_activity(usage_threshold, lock_duration, password, use_continuous_mode):
    global is_locked, continuous_usage
    continuous_usage = 0

    while not stop_event.is_set():
        if use_continuous_mode:
            # Continuous usage mode: count as long as not locked
            if not is_locked:
                continuous_usage += 60  # add 60 seconds per check
            else:
                continuous_usage = 0
        else:
            # Original mode: based on input activity
            idle = get_idle_time()
            if idle < 60:  # if active within last 60 seconds
                continuous_usage += 60  # add 60 seconds
            else:
                continuous_usage = 0

def monitor_activity(usage_threshold, lock_duration, password, use_continuous_mode):
    global is_locked, continuous_usage, lock_request
    continuous_usage = 0

    while not stop_event.is_set():
        if use_continuous_mode:
            # Continuous usage mode: count as long as not locked
            if not is_locked:
                continuous_usage += 60  # add 60 seconds per check
            else:
                continuous_usage = 0
        else:
            # Original mode: based on input activity
            idle = get_idle_time()
            if idle < 60:  # if active within last 60 seconds
                continuous_usage += 60  # add 60 seconds
            else:
                continuous_usage = 0

        if continuous_usage > usage_threshold and not is_locked:
            lock_request = (lock_duration, password)  # request lock from main thread
            continuous_usage = 0  # reset after lock

        time.sleep(60)  # check every 60 seconds to save resources

def toggle_monitoring():
    global is_monitoring, monitor_thread
    try:
        usage_min = int(usage_entry.get())
        lock_min = int(lock_entry.get())
        pwd = pwd_entry.get()
        use_continuous = continuous_var.get()
        if not pwd:
            raise ValueError("Password is required")
        usage_threshold = usage_min * 60
        lock_duration = lock_min * 60
        # Save config
        config = {
            "usage_threshold": usage_min,
            "lock_duration": lock_min,
            "password": pwd,
            "continuous_mode": use_continuous
        }
        save_config(config)
        
        if not is_monitoring:
            # Start monitoring
            stop_event.clear()
            monitor_thread = threading.Thread(target=monitor_activity, args=(usage_threshold, lock_duration, pwd, use_continuous), daemon=True)
            monitor_thread.start()
            is_monitoring = True
            toggle_button.config(text="停止监控")
            root.iconify()  # minimize to taskbar
        else:
            # Stop monitoring
            stop_event.set()
            if monitor_thread:
                monitor_thread.join(timeout=2)
            is_monitoring = False
            toggle_button.config(text="开始监控")
    except ValueError as e:
        messagebox.showerror("错误", str(e))

def update_usage_label():
    global continuous_usage, lock_request
    usage_label.config(text=f"连续使用：{continuous_usage / 60:.0f} 分钟")
    # Check for lock request from monitor thread
    if lock_request and not is_locked:
        lock_duration, password = lock_request
        lock_request = None
        lock_computer(lock_duration, password)
    root.after(1000, update_usage_label)  # update every second

# Load config
config = load_config()

root = tk.Tk()
root.title("电脑锁定设置")
root.eval('tk::PlaceWindow . center')

# 设置ttk样式
style = ttk.Style()
style.configure("Accent.TButton", font=("Arial", 12, "bold"), padding=10)

ttk.Label(root, text="连续使用阈值（分钟）：").grid(row=0, column=0, padx=10, pady=5)
usage_entry = ttk.Entry(root)
usage_entry.insert(0, str(config["usage_threshold"]))
usage_entry.grid(row=0, column=1, padx=10, pady=5)

ttk.Label(root, text="锁定持续时间（分钟）：").grid(row=1, column=0, padx=10, pady=5)
lock_entry = ttk.Entry(root)
lock_entry.insert(0, str(config["lock_duration"]))
lock_entry.grid(row=1, column=1, padx=10, pady=5)

ttk.Label(root, text="密码：").grid(row=2, column=0, padx=10, pady=5)
pwd_entry = ttk.Entry(root, show='*')
pwd_entry.insert(0, config["password"])
pwd_entry.grid(row=2, column=1, padx=10, pady=5)

continuous_var = tk.BooleanVar(value=config["continuous_mode"])
ttk.Checkbutton(root, text="连续使用模式（忽略输入，只要未锁定就计数）", variable=continuous_var).grid(row=3, column=0, columnspan=2, pady=5)

toggle_button = ttk.Button(root, text="开始监控", command=toggle_monitoring)
toggle_button.grid(row=4, column=0, columnspan=2, pady=10)

usage_label = ttk.Label(root, text="连续使用：0 秒", font=("Arial", 12))
usage_label.grid(row=5, column=0, columnspan=2, pady=5)

# Auto start if password is set
if config["password"]:
    toggle_monitoring()

update_usage_label()  # start updating the usage label

root.mainloop()