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
        locale_write = 'en_US'

        if system_locale == 'ko_KR':
            locale_write = 'ko_KR'

        default = {'locale': locale_write,
                   'try_soft_shutdown': 'true',
                   'show_profilename': 'bar',
                   'autoexit': 'true'}
        yaml.dump(default, cfg)


if not os.path.isfile('config.yml'):
    reset_config()

try:
    with open('config.yml', 'r') as cfg:
        test_dict = yaml.load(cfg)

    config_invalid = set(['locale', 'try_soft_shutdown', 'show_profilename', 'autoexit']) != set(test_dict)  # NOQA
    value_valid = set(test_dict.values()).issubset(['true', 'false', 'ko_KR', 'en_US', 'bar', 'bracket'])  # NOQA

    no_locale = 'locale' not in set(test_dict)
    if not no_locale:
        locale_invalid = test_dict['locale'] not in ('ko_KR', 'en_US')
    else:
        locale_invalid = True

    no_try_soft = 'try_soft_shutdown' not in set(test_dict)
    if not no_try_soft:
        try_soft_invalid = test_dict['try_soft_shutdown'] not in ('true', 'false')  # NOQA
    else:
        try_soft_invalid = True

    no_show_profilename = 'show_profilename' not in set(test_dict)
    if not no_show_profilename:
        show_profilename_invalid = test_dict['show_profilename'] not in ('bar', 'bracket', 'false')  # NOQA
    else:
        show_profilename_invalid = True

    no_autoexit = 'autoexit' not in set(test_dict)
    if not no_autoexit:
        autoexit_invalid = test_dict['autoexit'] not in ('true', 'false')
    else:
        autoexit_invalid = True

    if config_invalid or not value_valid or show_profilename_invalid:  # NOQA
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
