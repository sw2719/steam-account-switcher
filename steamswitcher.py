import sys
import os
import shutil
from modules.config import first_run
from modules.update import start_checkupdate
from modules.ui import MainApp
from modules.reg import fetch_reg

print('Init start')

__VERSION__ = '2.0'
BRANCH = 'master'
URL = ('https://raw.githubusercontent.com/sw2719/steam-account-switcher/%s/version.yml' % BRANCH)

if getattr(sys, 'frozen', False):
    print('Running in a bundle')
    BUNDLE = True
    if os.path.isdir('updater'):
        try:
            shutil.rmtree('updater')
        except OSError:
            pass
    if os.path.isfile('update.zip'):
        try:
            os.remove('update.zip')
        except OSError:
            pass
else:
    print('Running in a Python interpreter')
    BUNDLE = False

if fetch_reg('autologin') != 2:
    print('Autologin value is ' + str(fetch_reg('autologin')))
else:
    print('ERROR: Could not fetch autologin status!')
if fetch_reg('autologin'):
    print('Current autologin user is ' + str(fetch_reg('username')))
else:
    print('ERROR: Could not fetch current autologin user!')

root = MainApp(__VERSION__, URL, BUNDLE)
root.draw_button()
root.after(100, lambda: start_checkupdate(root, __VERSION__, URL, BUNDLE))

if first_run:
    root.after(200, root.welcomewindow)

print('Init complete.')
root.mainloop()
