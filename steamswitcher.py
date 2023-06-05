import sys
import os
import shutil
import logging
import argparse
from modules.log import StreamToLogger

VERSION = '3.1'

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

if args.logfile or getattr(sys, 'frozen', False):
    handler = logging.FileHandler('log.txt', 'w', 'utf-8')
else:
    handler = logging.StreamHandler()

handler.setFormatter(log_format)
logger.addHandler(handler)

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

from modules.main import MainApp

root = MainApp(VERSION, BUNDLE)
root.mainloop()
