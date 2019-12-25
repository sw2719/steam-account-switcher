import tkinter as tk
from tkinter import messagebox as msgbox
import sys
import os
import gettext
import shutil
from ruamel.yaml import YAML
from modules.config import get_config
from modules.update import start_checkupdate
from modules.ui import main, importwindow
from modules.reg import fetch_reg
from modules.account import acc_getlist

print('App Start')

BRANCH = 'master'
__VERSION__ = '1.8'
URL = ('https://raw.githubusercontent.com/sw2719/steam-account-switcher/%s/version.yml' % BRANCH)


if getattr(sys, 'frozen', False):
    print('Running in a bundle')
    BUNDLE = True
    if os.path.isdir('updater'):
        try:
            shutil.rmtree('updater')
        except OSError:
            pass
else:
    print('Running in a Python interpreter')
    BUNDLE = False


def error_msg(title, content):
    '''Show error message and exit'''
    root = tk.Tk()
    root.withdraw()
    msgbox.showerror(title, content)
    root.destroy()
    sys.exit(1)


yaml = YAML()

LOCALE = get_config('locale')

print('Using locale', LOCALE)

t = gettext.translation('steamswitcher',
                        localedir='locale',
                        languages=[LOCALE],
                        fallback=True)
_ = t.gettext

print('Running on', os.getcwd())


def afterupdate():
    if os.path.isfile('update.zip'):
        try:
            os.remove('update.zip')
        except OSError:
            pass


print('Fetching registry values...')

if fetch_reg('autologin') != 2:
    print('Autologin value is ' + str(fetch_reg('autologin')))
else:
    print('ERROR: Could not fetch autologin status!')
if fetch_reg('autologin'):
    print('Current autologin user is ' + str(fetch_reg('username')))
else:
    print('ERROR: Could not fetch current autologin user!')

main = main(__VERSION__, URL, BUNDLE)
main.draw_button()
main.after(100, lambda: start_checkupdate(main, __VERSION__, URL, BUNDLE))

if os.path.isfile(os.path.join(os.getcwd(), 'update.zip')):
    main.after(150, afterupdate)
if not acc_getlist():
    main.after(200, lambda: importwindow(main))

main.mainloop()
