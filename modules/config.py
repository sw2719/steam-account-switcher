import os
import locale
import gettext
import sys
from ruamel.yaml import YAML
from modules.misc import error_msg

system_locale = locale.getdefaultlocale()[0]

yaml = YAML()


def reset_config():
    '''Initialize config.txt with default values'''
    with open('config.yml', 'w') as cfg:

        if system_locale == 'ko_KR':
            locale_write = 'ko_KR'
        elif system_locale == 'fr_FR':
            locale_write = 'fr_FR'
        else:
            locale_write = 'en_US'

        default = {'locale': locale_write,
                   'try_soft_shutdown': 'true',
                   'show_profilename': 'bar',
                   'autoexit': 'true',
                   'mode': 'normal'}
        yaml.dump(default, cfg)


if not os.path.isfile('config.yml'):
    reset_config()
    first_run = True
else:
    first_run = False

try:
    with open('config.yml', 'r') as cfg:
        test_dict = yaml.load(cfg)

    config_invalid = set(['locale', 'try_soft_shutdown',
                          'show_profilename', 'autoexit',
                          'mode']) != set(test_dict)
    value_valid = set(test_dict.values()).issubset(['true', 'false', 'ko_KR',
                                                    'en_US', 'fr_FR', 'bar',
                                                    'bracket', 'normal', 'express'])

    no_locale = 'locale' not in set(test_dict)
    if not no_locale:
        locale_invalid = test_dict['locale'] not in ('ko_KR', 'en_US', 'fr_FR')
    else:
        locale_invalid = True

    no_try_soft = 'try_soft_shutdown' not in set(test_dict)
    if not no_try_soft:
        try_soft_invalid = test_dict['try_soft_shutdown'] not in ('true', 'false')
    else:
        try_soft_invalid = True

    no_show_profilename = 'show_profilename' not in set(test_dict)
    if not no_show_profilename:
        show_profilename_invalid = test_dict['show_profilename'] not in ('bar', 'bracket', 'false')
    else:
        show_profilename_invalid = True

    no_autoexit = 'autoexit' not in set(test_dict)
    if not no_autoexit:
        autoexit_invalid = test_dict['autoexit'] not in ('true', 'false')
    else:
        autoexit_invalid = True

    no_mode = 'mode' not in set(test_dict)
    if not no_mode:
        mode_invalid = test_dict['mode'] not in ('normal', 'express')
    else:
        mode_invalid = True

    if config_invalid or not value_valid or show_profilename_invalid:
        cfg_write = {}
        if no_locale or locale_invalid:
            locale_write = 'en_US'

            if system_locale == 'ko_KR':
                locale_write = 'ko_KR'
            cfg_write['locale'] = locale_write
        else:
            cfg_write['locale'] = test_dict['locale']
        if no_try_soft or try_soft_invalid:
            cfg_write['try_soft_shutdown'] = 'true'
        else:
            cfg_write['try_soft_shutdown'] = test_dict['try_soft_shutdown']
        if no_show_profilename or show_profilename_invalid:
            cfg_write['show_profilename'] = 'bar'
        else:
            cfg_write['show_profilename'] = test_dict['show_profilename']
        if no_autoexit or autoexit_invalid:
            cfg_write['autoexit'] = 'true'
        else:
            cfg_write['autoexit'] = test_dict['autoexit']
        if no_mode or mode_invalid:
            cfg_write['mode'] = 'normal'
        else:
            cfg_write['mode'] = test_dict['mode']
        with open('config.yml', 'w') as cfg:
            yaml.dump(cfg_write, cfg)
        del cfg_write
        del test_dict
except FileNotFoundError:
    reset_config()
    sys.exit(1)

try:
    with open('config.yml', 'r') as cfg:
        config_dict = yaml.load(cfg)
    if config_dict['locale'] in ('ko_KR', 'en_US'):
        LOCALE = config_dict['locale']
    else:
        LOCALE = 'en_US'
except Exception:
    LOCALE = 'en_US'

t = gettext.translation('steamswitcher',
                        localedir='locale',
                        languages=[LOCALE],
                        fallback=True)
_ = t.gettext


if not os.path.isfile('config.yml'):
    reset_config()


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
