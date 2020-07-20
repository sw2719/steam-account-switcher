import threading
import psutil
import os
from steam.steamid import SteamID
from modules.reg import fetch_reg


class StoppableThread(threading.Thread):
    def __init__(self, target):
        super(StoppableThread, self).__init__(target=target)
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()


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
    steamid_3 = SteamID(steamid64).as_steam3  # [U:1:xxxxxxxxxx]
    return steamid_3.split(':')[2].replace(']', '')


def open_screenshot(steamid64, steam_path=fetch_reg('steampath')):
    if os.path.isfile('steam_path.txt'):
        with open('steam_path.txt', 'r') as path:
            steam_path = path.read()

    if '/' in steam_path:
        steam_path = steam_path.replace('/', '\\')

    os.startfile(f'{steam_path}\\userdata\\{steam64_to_3(steamid64)}\\760\\remote')
