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

def get_idle_time():
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
    return (ctypes.windll.kernel32.GetTickCount() - lii.dwTime) / 1000.0

def lock_computer(duration, password):
    global is_locked
    is_locked = True
    # Use Toplevel instead of new Tk() to avoid multiple Tk instances
    lock_window = tk.Toplevel(root)
    lock_window.geometry(f"{lock_window.winfo_screenwidth()}x{lock_window.winfo_screenheight()}+0+0")
    lock_window.overrideredirect(True)  # remove window decorations to disable minimize, drag, close
    lock_window.attributes("-topmost", True)
    lock_window.configure(bg='black')
    lock_window.title("Locked")

    label = tk.Label(lock_window, text="Computer is locked. Enter password to unlock.", font=("Arial", 30), fg="white", bg="black")
    label.pack(expand=True)

    timer_label = tk.Label(lock_window, text="", font=("Arial", 20), fg="white", bg="black")
    timer_label.pack()

    def try_unlock():
        pwd = simpledialog.askstring("Unlock", "Enter password:", parent=lock_window, show='*')
        if pwd == password:
            lock_window.destroy()
        else:
            messagebox.showerror("Error", "Wrong password.")

    button = tk.Button(lock_window, text="Unlock", command=try_unlock, font=("Arial", 20))
    button.pack()

    remaining = duration
    def update_timer():
        nonlocal remaining
        if remaining > 0:
            mins = remaining // 60
            secs = remaining % 60
            timer_label.config(text=f"Auto unlock in {mins} minutes {secs} seconds")
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
            toggle_button.config(text="Stop Monitoring")
            root.iconify()  # minimize to taskbar
        else:
            # Stop monitoring
            stop_event.set()
            if monitor_thread:
                monitor_thread.join(timeout=2)
            is_monitoring = False
            toggle_button.config(text="Start Monitoring")
    except ValueError as e:
        messagebox.showerror("Error", str(e))

def update_usage_label():
    global continuous_usage, lock_request
    usage_label.config(text=f"Continuous Usage: {continuous_usage / 60:.0f} minutes")
    # Check for lock request from monitor thread
    if lock_request and not is_locked:
        lock_duration, password = lock_request
        lock_request = None
        lock_computer(lock_duration, password)
    root.after(1000, update_usage_label)  # update every second

# Load config
config = load_config()

root = tk.Tk()
root.title("Computer Lock Settings")

tk.Label(root, text="Continuous Usage Threshold (minutes):").grid(row=0, column=0, padx=10, pady=5)
usage_entry = tk.Entry(root)
usage_entry.insert(0, str(config["usage_threshold"]))
usage_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="Lock Duration (minutes):").grid(row=1, column=0, padx=10, pady=5)
lock_entry = tk.Entry(root)
lock_entry.insert(0, str(config["lock_duration"]))
lock_entry.grid(row=1, column=1, padx=10, pady=5)

tk.Label(root, text="Password:").grid(row=2, column=0, padx=10, pady=5)
pwd_entry = tk.Entry(root, show='*')
pwd_entry.insert(0, config["password"])
pwd_entry.grid(row=2, column=1, padx=10, pady=5)

continuous_var = tk.BooleanVar(value=config["continuous_mode"])
tk.Checkbutton(root, text="Continuous usage mode (ignore input, count as long as not locked)", variable=continuous_var).grid(row=3, column=0, columnspan=2, pady=5)

toggle_button = tk.Button(root, text="Start Monitoring", command=toggle_monitoring)
toggle_button.grid(row=4, column=0, columnspan=2, pady=10)

usage_label = tk.Label(root, text="Continuous Usage: 0 seconds", font=("Arial", 12))
usage_label.grid(row=5, column=0, columnspan=2, pady=5)

# Auto start if password is set
if config["password"]:
    toggle_monitoring()

update_usage_label()  # start updating the usage label

root.mainloop()