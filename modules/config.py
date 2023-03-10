import os
import locale
import gettext
import json
from ruamel.yaml import YAML
from win32api import GetSystemMetrics
from modules.errormsg import error_msg
import darkdetect


def pprint(*args, **kwargs):
    print('[config]', *args, **kwargs)



SYS_LOCALE = locale.getdefaultlocale()[0]

if SYS_LOCALE == 'ko_KR':
    DEFAULT_LOCALE = 'ko_KR'
elif SYS_LOCALE == 'fr_FR':
    DEFAULT_LOCALE = 'fr_FR'
else:
    DEFAULT_LOCALE = 'en_US'

valid_values = {
    'locale':
        ['ko_KR',
         'en_US',
         'fr_FR'],
    'try_soft_shutdown':
        ['true',
         'false'],
    'autoexit':
        ['true',
         'false'],
    'mode':
        ['normal',
         'express'],
    'show_avatar':
        ['true',
         'false'],
    'ui_mode':
        ['list',
         'grid'],
    'theme':
        ['light',
         'dark'],
    'encryption':
        ['true',
         'false']
}

screen_width = GetSystemMetrics(0)
screen_height = GetSystemMetrics(1)

window_width = 310
window_height = 465

x_coordinate = int((screen_width/2) - (window_width/2))
y_coordinate = int((screen_height/2) - (window_height/2))

default_cfg = {'locale': DEFAULT_LOCALE,
               'try_soft_shutdown': 'true',
               'autoexit': 'true',
               'mode': 'normal',
               'show_avatar': 'true',
               'steam_path': 'reg',
               'last_pos': f'{x_coordinate}/{y_coordinate}',
               'ui_mode': 'list',
               'theme': 'light',
               'encryption': 'false'}

if darkdetect.isDark():
    default_cfg['theme'] = 'dark'

missing_values = []

def convert():
    yaml = YAML()
    with open('config.yml', 'r', encoding='utf-8') as f:
        cfg = yaml.load(f)

    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4)

    os.remove('config.yml')
    pprint('Converted config.yml to config.json')

def reset_config():
    '''Initialize config.txt with default values'''
    with open('config.json', 'w') as cfg:
        json.dump(default_cfg, cfg, indent=4)


if not os.path.isfile('config.json'):
    if os.path.isfile('config.yml'):
        convert()
        first_run = False
    else:
        reset_config()
        first_run = True
else:
    with open('config.json') as cfg:
        if not cfg.read().strip():
            reset_config()
            first_run = True
        else:
            first_run = False

with open('config.json', 'r') as cfg:
    test_dict = json.load(cfg)

invalid = False

for key, value in valid_values.items():
    try:
        if test_dict[key] not in valid_values[key] and key not in ('steam_path', 'last_pos'):
            invalid = True
            pprint(f'Config {key} has invalid value "{test_dict[key]}"')
            test_dict[key] = default_cfg[key]
    except KeyError:
        invalid = True
        pprint(f'Config {key} is missing. Creating one with default value..')
        missing_values.append(key)
        test_dict[key] = default_cfg[key]

if invalid:
    with open('config.json', 'w') as cfg:
        json.dump(test_dict, cfg, indent=4)

with open('config.json', 'r') as cfg:
    config_dict = json.load(cfg)

    if config_dict['locale'] in ('ko_KR', 'en_US'):
        LOCALE = config_dict['locale']
    else:
        LOCALE = 'en_US'

del cfg

t = gettext.translation('steamswitcher',
                        localedir='locale',
                        languages=[LOCALE],
                        fallback=True)
_ = t.gettext


def get_config(key):
    try:
        with open('config.json', 'r') as cfg:
            config_dict = json.load(cfg)

        if key == 'all':
            return config_dict
        else:
            return config_dict[key]

    except FileNotFoundError:
        reset_config()
        error_msg(_('Error'), _('Could not load config file.'))


def config_write_dict(config_dict):
    with open('config.json', 'w') as cfg:
        json.dump(config_dict, cfg, indent=4)


def config_write_value(key, value):
    config_dict = {'locale': get_config('locale'),
                   'autoexit': get_config('autoexit'),
                   'mode': get_config('mode'),
                   'try_soft_shutdown': get_config('try_soft_shutdown'),
                   'show_avatar': get_config('show_avatar'),
                   'last_pos': get_config('last_pos'),
                   'steam_path': get_config('steam_path'),
                   'ui_mode': get_config('ui_mode'),
                   'theme': get_config('theme'),
                   'encryption': get_config('encryption')}

    config_dict[key] = value

    with open('config.json', 'w') as cfg:
        json.dump(config_dict, cfg, indent=4)
