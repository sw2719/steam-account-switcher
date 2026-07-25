# nuitka-project: --standalone
# nuitka-project: --enable-plugin=tk-inter
# nuitka-project: --windows-console-mode=disable
# nuitka-project: --output-filename="Steam Account Switcher.exe"
# nuitka-project: --include-data-dir={MAIN_DIRECTORY}/asset=asset
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/theme.json=theme.json
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/theme.json=theme.json
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/locale/en_US/LC_MESSAGES/steamswitcher.mo=locale/en_US/LC_MESSAGES/steamswitcher.mo
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/locale/ko_KR/LC_MESSAGES/steamswitcher.mo=locale/ko_KR/LC_MESSAGES/steamswitcher.mo
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/locale/fr_FR/LC_MESSAGES/steamswitcher.mo=locale/fr_FR/LC_MESSAGES/steamswitcher.mo
# nuitka-project: --windows-icon-from-ico=icon.ico

import sys
import os
import shutil
import logging
import argparse
from modules.log import StreamToLogger

VERSION = '3.1.2'

is_nuitka = "__compiled__" in globals()
logger = logging.getLogger()
logger.addHandler(logging.NullHandler())
parser = argparse.ArgumentParser()

sys.__stdout__ = StreamToLogger(logger, logging.INFO)
sys.__stderr__ = StreamToLogger(logger, logging.ERROR)

parser.add_argument('-debug', action='store_true', help='Run in debug mode')
parser.add_argument('--logfile', action='store_true', help='Log to file')
parser.add_argument('-l', '--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Set log level')

args = parser.parse_args()

log_format = logging.Formatter("{name} - [{levelname}] - {message}", style="{")

if args.logfile or is_nuitka:
    handler = logging.FileHandler('log.txt', 'w', 'utf-8')
else:
    handler = logging.StreamHandler()

handler.setFormatter(log_format)
logger.addHandler(handler)

logger.setLevel(args.log_level)
logger.info(f'Launch arguments: {" ".join(sys.argv)}')

if args.debug:
    BUNDLE = False
elif is_nuitka:
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
    logger.info('Running nuitka-compiled executable')
else:
    BUNDLE = False
    logger.info('Running in a Python interpreter')

from modules.main import MainApp

root = MainApp(VERSION, BUNDLE)
root.mainloop()
