import winreg
from modules.reg import fetch_reg

HKCU = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)


def steam_running():
    """Check if Steam is running using registry key 'pid'"""
    if fetch_reg('pid') == 0:
        return False
    else:
        return True
