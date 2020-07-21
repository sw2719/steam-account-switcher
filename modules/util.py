import threading
import psutil
import os
from steam.steamid import SteamID
from modules.reg import fetch_reg
from modules.config import get_config


class StoppableThread(threading.Thread):
    def __init__(self, target):
        super(StoppableThread, self).__init__(target=target)
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()


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
    if check_steam_dir and get_config('steam_path') == 'reg':
        print('Steam located at', fetch_reg('steampath'))
    elif check_steam_dir:
        print('Steam located at', get_config('steam_path'))
    else:
        print('Steam directory invalid')
        return False
    return True


def raise_exception():
    raise Exception


def check_steam_dir():
    if get_config('steam_path') == 'reg' and os.path.isfile(fetch_reg('SteamPath') + '\\Steam.exe'):
        return True
    elif os.path.isfile(get_config('steam_path') + '\\Steam.exe'):
        return True
    else:
        return False


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
    """Check if Steam is running using registry key 'pid'.
    Since Steam does not change pid value to 0 when you force quit,
    previous psutil method is currently used."""
    if fetch_reg('pid') == 0:
        return False
    else:
        return True


def steam64_to_3(steamid64):
    return SteamID(steamid64).as_steam3


def steam64_to_32(steamid64):
    return SteamID(steamid64).as_32


def steam64_to_2(steamid64):
    return SteamID(steamid64).as_steam2


def open_screenshot(steamid64, steam_path=fetch_reg('steampath')):
    if os.path.isfile('steam_path.txt'):
        with open('steam_path.txt', 'r') as path:
            steam_path = path.read()

    if '/' in steam_path:
        steam_path = steam_path.replace('/', '\\')

    os.startfile(f'{steam_path}\\userdata\\{steam64_to_32(steamid64)}\\760\\remote')
