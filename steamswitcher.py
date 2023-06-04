import sys
import os
import shutil
import logging
import argparse
from modules.main import MainApp

VERSION = '3.1'

logger = logging.getLogger()
parser = argparse.ArgumentParser()

parser.add_argument('-debug', action='store_true', help='Run in debug mode')
parser.add_argument('-logfile', action='store_true', help='Log to file')
parser.add_argument('-l', '--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Set log level')

args = parser.parse_args()

if args.logfile:
    logger.addHandler(logging.FileHandler('log.txt', 'w', 'utf-8'))

logger.setLevel(args.log_level)
logger.info(f'Launch arguments: {" ".join(sys.argv)}')

if args.debug:
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
    logger.info('Running on an executable')
else:
    BUNDLE = False
    logger.info('Running in a Python interpreter')

root = MainApp(VERSION, BUNDLE)
root.mainloop()
