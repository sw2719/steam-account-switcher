import psutil
import winreg
from modules.reg import fetch_reg

HKCU = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)


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
    """Check if Steam is running using registry key 'pid'"""
    if fetch_reg('pid') == 0:
        return False
    else:
        return True
