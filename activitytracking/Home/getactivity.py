import psutil
import win32gui
import win32process
import time
import threading

def get_active_window_name():
    window = win32gui.GetForegroundWindow()
    return win32gui.GetWindowText(window)

def get_active_process_name():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None

def track_active_applications(interval=5):
    try:
        arr=[]
        while True:
            active_window_name = get_active_window_name()
            active_process_name = get_active_process_name()
            if active_window_name and active_process_name:
                if active_window_name!=arr[-1]:
                    arr.append(active_window_name)
            time.sleep(interval)
        return arr
    except KeyboardInterrupt:
        return []

stop_event=threading.Event()
active_apps = {}
def track_active_applications2(stop_event, interval=5):
    try:
        global active_apps
        current_app = None
        start_time = None

        while not stop_event.is_set():
            active_window_name = get_active_window_name()
            active_process_name = get_active_process_name()

            if active_window_name and active_process_name:
                if active_window_name != current_app:
                    # If there's a currently tracked application, update its total time
                    if current_app and start_time:
                        elapsed_time = time.time() - start_time
                        if current_app in active_apps:
                            active_apps[current_app] += elapsed_time
                        else:
                            active_apps[current_app] = elapsed_time

                    # Start tracking the new active application
                    current_app = active_window_name
                    start_time = time.time()
            print(active_apps)
            time.sleep(interval)

        return active_apps

    except KeyboardInterrupt:
        # Ensure the last active application is updated before exiting
        if current_app and start_time:
            elapsed_time = time.time() - start_time
            if current_app in active_apps:
                active_apps[current_app] += elapsed_time
            else:
                active_apps[current_app] = elapsed_time
        return active_apps

track_Thread = threading.Thread(target=track_active_applications2, args=(stop_event, 5, ))
