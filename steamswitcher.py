import sys
import os
import shutil
import logging
from modules.main import MainApp

VERSION = '3.1'
BRANCH = 'master'

logger = logging.getLogger()

if '-logfile' in sys.argv:
    logging.basicConfig(level=logging.INFO, filename='log.txt')
else:
    logging.basicConfig(level=logging.INFO)

logger.info(f'Launch arguments: {" ".join(sys.argv)}')

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
        try:
            os.remove('update.zip')
        except OSError:
            pass
    logger.info('Running in a bundle')
else:
    BUNDLE = False
    logger.info('Running in a Python interpreter')


root = MainApp(VERSION, BUNDLE)

root.mainloop()
