import winreg
import gettext
from modules.ui import error_msg
from ruamel.yaml import YAML

yaml = YAML()

with open('config.yml', 'r') as cfg:
    config_dict = yaml.load(cfg)

try:
    if config_dict['locale'] in ('ko_KR', 'en_US'):
        LOCALE = config_dict['locale']
    else:
        LOCALE = 'en_US'
except Exception:
    LOCALE = 'en_US'


t = gettext.translation('reg',
                        localedir='../locale',
                        languages=[LOCALE],
                        fallback=True)
_ = t.gettext


HKCU = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)


def fetch_reg(key):
    '''Return given key's value from steam registry path.
    :param key: 'username', 'autologin', 'steamexe', 'steampath'
    '''
    if key == 'username':
        key_name = 'AutoLoginUser'
    elif key == 'autologin':
        key_name = 'RememberPassword'
    elif key == 'steamexe':
        key_name = 'SteamExe'
    elif key == 'steampath':
        key_name = 'SteamPath'

    try:
        reg_key = winreg.OpenKey(HKCU, r"Software\Valve\Steam")
        value_buffer = winreg.QueryValueEx(reg_key, key_name)
        value = value_buffer[0]
        winreg.CloseKey(reg_key)
    except OSError:
        error_msg(_('Registry Error'),
                  _('Failed to read registry value.') + '\n' +
                  _('Make sure that Steam is installed.'))
    return value


def setkey(key_name, value, value_type):
    '''Change given key's value to given value.
    :param key_name: Name of key to change value of
    :param value: Value to change to
    :param value_type: Registry value type
    '''
    try:
        reg_key = winreg.OpenKey(HKCU, r"Software\Valve\Steam", 0,
                                 winreg.KEY_ALL_ACCESS)

        winreg.SetValueEx(reg_key, key_name, 0, value_type, value)
        winreg.CloseKey(reg_key)
        print("Changed %s's value to %s" % (key_name, str(value)))
    except OSError:
        error_msg(_('Registry Error'), _('Failed to change registry value.'))
