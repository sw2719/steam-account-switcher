import tkinter as tk
from tkinter import messagebox as msgbox
import sys
import psutil


def error_msg(title, content):
    '''Show error message and exit'''
    root = tk.Tk()
    root.withdraw()
    msgbox.showerror(title, content)
    root.destroy()
    sys.exit(1)


def check_running(process_name):
    '''Check if given process is running and return boolean value.
    :param process_name: Name of process to check
    '''
    for process in psutil.process_iter():
        try:
            if process_name.lower() in process.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied,
                psutil.ZombieProcess):
            pass
    return False
