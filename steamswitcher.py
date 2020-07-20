import sys
import os
import shutil
from modules.config import first_run, no_avatar, avatar_invalid
from modules.update import start_checkupdate
from modules.main import MainApp
from modules.avatar import download_avatar

VERSION = '2.4'
BRANCH = 'master'
URL = ('https://raw.githubusercontent.com/sw2719/steam-account-switcher/%s/version.yml' % BRANCH)

after_update = False

if getattr(sys, 'frozen', False):
    print('Running in a bundle')
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
else:
    print('Running in a Python interpreter')
    BUNDLE = False

root = MainApp(VERSION, URL, BUNDLE)
root.after(100, lambda: start_checkupdate(root, VERSION, URL, BUNDLE))

if no_avatar or avatar_invalid:
    download_avatar()

if first_run or after_update:
    root.after(200, root.welcomewindow)

print('Init complete.')
root.mainloop()
