import os
import locale
import gettext
from ruamel.yaml import YAML
from modules.errormsg import error_msg

SYS_LOCALE = locale.getdefaultlocale()[0]

if SYS_LOCALE == 'ko_KR':
    DEFAULT_LOCALE = 'ko_KR'
elif SYS_LOCALE == 'fr_FR':
    DEFAULT_LOCALE = 'fr_FR'
else:
    DEFAULT_LOCALE = 'en_US'

yaml = YAML()

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
         'dark']
}

DEFAULT_CONFIG = {'locale': DEFAULT_LOCALE,
                  'try_soft_shutdown': 'true',
                  'autoexit': 'true',
                  'mode': 'normal',
                  'show_avatar': 'true',
                  'steam_path': 'reg',
                  'last_pos': '200/100',
                  'ui_mode': 'list',
                  'theme': 'light'}


def reset_config():
    '''Initialize config.txt with default values'''
    with open('config.yml', 'w') as cfg:
        yaml.dump(DEFAULT_CONFIG, cfg)


if not os.path.isfile('config.yml'):
    reset_config()
    first_run = True
else:
    with open('config.yml') as cfg:
        if not cfg.read().strip():
            reset_config()
            first_run = True
        else:
            first_run = False

with open('config.yml', 'r') as cfg:
    test_dict = yaml.load(cfg)

invalid = False

for key, value in valid_values.items():
    try:
        if test_dict[key] not in valid_values[key] and key not in ('steam_path', 'last_pos'):
            invalid = True
            print(f'Config {key} has invalid value "{test_dict[key]}"')
            test_dict[key] = DEFAULT_CONFIG[key]
    except KeyError:
        invalid = True
        print(f'Config {key} is missing. Creating one with default value..')
        test_dict[key] = DEFAULT_CONFIG[key]

if invalid:
    with open('config.yml', 'w') as cfg:
        yaml.dump(test_dict, cfg)

with open('config.yml', 'r') as cfg:
    config_dict = yaml.load(cfg)

    if config_dict['locale'] in ('ko_KR', 'en_US'):
        LOCALE = config_dict['locale']
    else:
        LOCALE = 'en_US'

t = gettext.translation('steamswitcher',
                        localedir='locale',
                        languages=[LOCALE],
                        fallback=True)
_ = t.gettext


def get_config(key):
    try:
        with open('config.yml', 'r') as cfg:
            config_dict = yaml.load(cfg)

        if key == 'all':
            return config_dict
        else:
            return config_dict[key]

    except FileNotFoundError:
        reset_config()
        error_msg(_('Error'), _('Could not load config file.'))


def config_write_dict(config_dict):
    with open('config.yml', 'w') as cfg:
        yaml.dump(config_dict, cfg)


def config_write_value(key, value):
    config_dict = {'locale': get_config('locale'),
                   'autoexit': get_config('autoexit'),
                   'mode': get_config('mode'),
                   'try_soft_shutdown': get_config('try_soft_shutdown'),
                   'show_avatar': get_config('show_avatar'),
                   'last_pos': get_config('last_pos'),
                   'steam_path': get_config('steam_path'),
                   'ui_mode': get_config('ui_mode'),
                   'theme': get_config('theme')}

    config_dict[key] = value

    with open('config.yml', 'w') as cfg:
        yaml.dump(config_dict, cfg)
