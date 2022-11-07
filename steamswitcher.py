import sys
import os
import shutil
from modules.config import first_run
from modules.update import start_checkupdate
from modules.main import MainApp

VERSION = '3.0'
BRANCH = 'master'
URL = ('https://raw.githubusercontent.com/sw2719/steam-account-switcher/%s/version.yml' % BRANCH)

print('Launch arguments:', sys.argv)

after_update = False

if '-debug' in sys.argv:
    BUNDLE = False
elif getattr(sys, 'frozen', False):
    BUNDLE = True
    if os.path.isdir('updater'):
        try:
            shutil.rmtree('updater')
        except OSError:
            pass
    if os.path.isfile('update.zip'):
        after_update = True
        try:
            os.remove('update.zip')
        except OSError:
            pass
    print('Running in a bundle')
else:
    BUNDLE = False
    print('Running in a Python interpreter')

if '-logfile' in sys.argv:
    std_out = open('log.txt', 'w', encoding='utf-8')
    std_err = std_out
    sys.stdout = std_out
    sys.stderr = std_out
else:
    std_out = sys.__stdout__
    std_err = sys.__stderr__

root = MainApp(VERSION, URL, BUNDLE, std_out, std_err, after_update)
root.after(100, lambda: start_checkupdate(root, VERSION, URL, BUNDLE))

root.mainloop()
