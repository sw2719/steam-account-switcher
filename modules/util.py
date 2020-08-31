import threading
import psutil
import os
import zipfile as zf
import sys
from modules.reg import fetch_reg
from modules.config import get_config
from modules.steamid import steam64_to_32


class StoppableThread(threading.Thread):
    def __init__(self, target):
        super(StoppableThread, self).__init__(target=target)
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()


def check_steam_dir():
    if get_config('steam_path') == 'reg' and os.path.isfile(fetch_reg('SteamPath') + '\\Steam.exe'):
        return True
    elif os.path.isfile(get_config('steam_path') + '\\Steam.exe'):
        return True
    else:
        return False


def launch_updater():
    try:
        archive = os.path.join(os.getcwd(), 'update.zip')

        f = zf.ZipFile(archive, mode='r')
        f.extractall(members=(member for member in f.namelist() if 'updater' in member))

        os.execv('updater/updater.exe', sys.argv)

    except (FileNotFoundError, zf.BadZipfile, OSError):
        print('Exception while launching updater')


def test():
    print('Listing current config...')
    print('locale:', get_config('locale'))
    print('autoexit:', get_config('autoexit'))
    print('mode:', get_config('mode'))
    print('try_soft_shutdown:', get_config('try_soft_shutdown'))
    print('show_avatar:', get_config('show_avatar'))
    print('steam_path:', get_config('steam_path'))

    print('Checking registry...')
    for key in ('AutoLoginUser', 'RememberPassword', 'SteamExe', 'SteamPath', 'pid', 'ActiveUser'):
        print(f'{key}:', fetch_reg(key))

    print('Checking Steam.exe location...')
    if check_steam_dir() and get_config('steam_path') == 'reg':
        print('Steam located at', fetch_reg('steampath'))
    elif check_steam_dir():
        print('Steam located at', get_config('steam_path'), '(Manually set)')
    else:
        print('Steam directory invalid')
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


def open_screenshot(steamid64, steam_path=get_config('steam_path')):
    if steam_path == 'reg':
        steam_path = fetch_reg('steampath')

    if '/' in steam_path:
        steam_path = steam_path.replace('/', '\\')

    os.startfile(f'{steam_path}\\userdata\\{steam64_to_32(steamid64)}\\760\\remote')
