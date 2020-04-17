import winreg
import gettext
from modules.errormsg import error_msg
from modules.config import get_config

LOCALE = get_config('locale')

t = gettext.translation('steamswitcher',
                        localedir='locale',
                        languages=[LOCALE],
                        fallback=True)
_ = t.gettext


HKCU = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)


def fetch_reg(key):
    '''Return given key's value from steam registry path.'''

    if key in ('pid', 'ActiveUser'):
        reg_path = r"Software\Valve\Steam\ActiveProcess"
    else:
        reg_path = r"Software\Valve\Steam"

    try:
        reg_key = winreg.OpenKey(HKCU, reg_path)
        value_buffer = winreg.QueryValueEx(reg_key, key)
        value = value_buffer[0]
        winreg.CloseKey(reg_key)
    except OSError:
        error_msg(_('Registry Error'),
                  _('Failed to read registry value.') + '\n' +
                  _('Make sure that Steam is installed.'))
    return value


def setkey(key_name, value, value_type, path=r"Software\Valve\Steam"):
    '''Change given key's value to given value.
    :param key_name: Name of key to change value of
    :param value: Value to change to
    :param value_type: Registry value type
    '''
    try:
        reg_key = winreg.OpenKey(HKCU, path, 0,
                                 winreg.KEY_ALL_ACCESS)

        winreg.SetValueEx(reg_key, key_name, 0, value_type, value)
        winreg.CloseKey(reg_key)
        print("Changed %s's value to %s" % (key_name, str(value)))
    except OSError:
        error_msg(_('Registry Error'), _('Failed to change registry value.'))


for key in ('AutoLoginUser', 'RememberPassword', 'SteamExe', 'SteamPath', 'pid', 'ActiveUser'):
    print(f'{key}:', fetch_reg(key))
