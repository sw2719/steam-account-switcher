import threading
import psutil
import os
import zipfile as zf
import sys
import winshell
import logging
from modules.reg import fetch_reg
from modules.config import config_manager as cm

logger = logging.getLogger(__name__)


class StoppableThread(threading.Thread):
    def __init__(self, target):
        super(StoppableThread, self).__init__(target=target)
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.is_set()


def check_steam_dir(force_reg=False):
    if force_reg:
        return os.path.isfile(fetch_reg('SteamPath') + '\\Steam.exe')

    if cm.get('steam_path') == 'reg' and os.path.isfile(fetch_reg('SteamPath') + '\\Steam.exe'):
        return True
    elif os.path.isfile(cm.get('steam_path') + '\\Steam.exe'):
        return True
    else:
        return False


def create_shortcut():
    desktop = winshell.desktop()

    with winshell.shortcut(os.path.join(desktop, "Steam Account Switcher.lnk")) as shortcut:
        shortcut.path = sys.argv[0]
        shortcut.icon = sys.argv[0], 0
        shortcut.working_directory = os.getcwd()


def launch_updater():
    try:
        archive = os.path.join(os.getcwd(), 'update.zip')

        f = zf.ZipFile(archive, mode='r')
        f.extractall(members=(member for member in f.namelist() if 'updater' in member))

        os.execv('updater/updater.exe', sys.argv)

    except (FileNotFoundError, zf.BadZipfile, OSError):
        print('Exception while launching updater')


def test():
    logger.info('Verifying Steam.exe location...')

    if check_steam_dir(force_reg=True) and cm.get('steam_path') != 'reg':
        logger.info('SteamPath registry key is valid but config is not set to use it')
        logger.info('Setting config to use registry key')
        cm.set('steam_path', 'reg')

    if cm.get('steam_path') == 'reg' and check_steam_dir():
        logger.info(f'Steam located at {fetch_reg("steampath")}')
    elif check_steam_dir():
        logger.info(f'Steam located at {cm.get("steam_path")} (Manually set)')
    else:
        logger.info('Steam directory invalid')
        return False
    return True


def raise_exception():
    raise Exception


def get_center_pos(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    center_x = int((screen_width/2) - (width/2))
    center_y = int((screen_height/2) - (height/2))

    return center_x, center_y


def check_running(process_name):
    '''Check if given process is running and return boolean value.
    :param process_name: Name of process to check
    '''
    for process in psutil.process_iter():
        try:
            if process_name.lower() in process.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied,
                psutil.ZombieProcess):
            pass
    return False


def steam_running():
    """Check if Steam is running"""
    steam_pid = fetch_reg('pid')

    if steam_pid == 0:
        return False

    try:
        process = psutil.Process(pid=steam_pid)
        name = process.name()

        if name.lower() == 'steam.exe':
            return True
        else:
            return False
    except psutil.NoSuchProcess:
        return False
