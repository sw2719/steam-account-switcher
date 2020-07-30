import os
import tkinter as tk
from tkinter import messagebox as msgbox

# This function is seperated to a module to prevent circular import.


def error_msg(title, content):
    '''Show error message and exit. New Tk instance is created and immediately withdrawn
    so that error message can be displayed without opening a Tk window when there's no Tk instance.'''
    root = tk.Tk()
    root.withdraw()

    msgbox.showerror(title, content)
    os._exit(1)
