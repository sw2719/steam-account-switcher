import sys
import tkinter as tk
from tkinter import messagebox as msgbox


def error_msg(title, content, master=None):
    '''Show error message and exit'''
    if master is None:
        root = tk.Tk()
        root.withdraw()
    else:
        root = master

    msgbox.showerror(title, content)
    root.destroy()
    sys.exit(1)
