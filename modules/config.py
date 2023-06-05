import os
import locale
import json
import logging
from ruamel.yaml import YAML
from win32api import GetSystemMetrics
import darkdetect

logger = logging.getLogger(__name__)

SYS_LOCALE = locale.getdefaultlocale()[0]

if SYS_LOCALE == 'ko_KR':
    DEFAULT_LOCALE = 'ko_KR'
elif SYS_LOCALE == 'fr_FR':
    DEFAULT_LOCALE = 'fr_FR'
else:
    DEFAULT_LOCALE = 'en_US'

if darkdetect.isDark():
    DEFAULT_THEME = 'dark'
else:
    DEFAULT_THEME = 'light'

screen_width = GetSystemMetrics(0)
screen_height = GetSystemMetrics(1)

window_width = 310
window_height = 465

x_coordinate = int((screen_width/2) - (window_width/2))
y_coordinate = int((screen_height/2) - (window_height/2))


# Why did I not use boolean values and use true and false as strings? I should've never done that...
CONFIG_DATA = {
    'locale': {
        'default': DEFAULT_LOCALE,
        'valid': ('ko_KR', 'en_US', 'fr_FR')
    },
    'try_soft_shutdown': {
        'default': 'true',
        'valid': ('true', 'false')
    },
    'autoexit': {
        'default': 'true',
        'valid': ('true', 'false')
    },
    'mode': {
        'default': 'normal',
        'valid': ('normal', 'express')
    },
    'show_avatar': {
        'default': 'true',
        'valid': ('true', 'false')
    },
    'steam_path': {
        'default': 'reg'
    },
    'last_pos': {
        'default': f'{x_coordinate}/{y_coordinate}'
    },
    'ui_mode': {
        'default': 'list',
        'valid': ('list', 'grid')
    },
    'theme': {
        'default': DEFAULT_THEME,
        'valid': ('light', 'dark')
    },
    'encryption': {
        'default': 'false',
        'valid': ('true', 'false')
    },
    'steam_options': {
        'default': ''
    }
}


class ConfigManager:
    def __init__(self):
        self.first_run = False

        if os.path.isfile('config.yml'):
            self.convert()

        try:
            with open('config.json') as cfg:
                self.dict = json.load(cfg)

        except json.JSONDecodeError:
            logger.info('Resetting config due to invalid JSON file')
            self.dict = self.reset_config()

        except FileNotFoundError:
            logger.info('Creating a config file...')
            self.dict = self.reset_config()
            self.first_run = True

        self.validate()
        logger.info('ConfigManager initialized')

    def set_dict(self, dict_: dict) -> None:
        for key, value in dict_.items():
            self.dict[key] = value

        self.dump()

    def set(self, key: str, value: str, dump=True) -> None:
        self.dict[key] = value

        if dump:
            self.dump()

    def get(self, key: str) -> str:
        return self.dict[key]

    def dump(self) -> None:
        with open('config.json', 'w') as f:
            json.dump(self.dict, f, indent=2)
        
        logger.info('Dumped current config dict')

    def validate(self) -> None:
        invalid = False

        for key, value in CONFIG_DATA.items():
            if key not in self.dict:
                invalid = True
                logger.info(f'Config {key} is missing.')
                logger.info(f'Creating one with a default value: {CONFIG_DATA[key]["default"]}')
                self.dict[key] = CONFIG_DATA[key]['default']
            elif 'valid' in CONFIG_DATA[key] and self.dict[key] not in CONFIG_DATA[key]['valid']:
                invalid = True
                logger.info(f'Config {key} has invalid value: {self.dict[key]}')
                logger.info(f'Replacing with a default value: {CONFIG_DATA[key]["default"]}')
                self.dict[key] = CONFIG_DATA[key]['default']

            if os.path.isfile('salt') and self.dict['encryption'] == 'false':
                self.dict['encryption'] = 'true'
                logger.info('Setting encryption to true due to salt file existing')

        if invalid:
            self.dump()

    @staticmethod
    def reset_config() -> dict:
        """Create a config.json with default values"""
        with open('config.json', 'w') as cfg:
            default_cfg = {}

            for key, item in CONFIG_DATA.items():
                default_cfg[key] = item['default']

            json.dump(default_cfg, cfg, indent=2)
            return default_cfg

    @staticmethod
    def convert() -> None:
        yaml = YAML()
        with open('config.yml', 'r', encoding='utf-8') as f:
            cfg = yaml.load(f)

        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2)

        os.remove('config.yml')
        logger.info('Converted config.yml to config.json')


config_manager = ConfigManager()
