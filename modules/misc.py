import tkinter as tk
from tkinter import messagebox as msgbox
import sys


def error_msg(title, content):
    '''Show error message and exit'''
    root = tk.Tk()
    root.withdraw()
    msgbox.showerror(title, content)
    root.destroy()
    sys.exit(1)
