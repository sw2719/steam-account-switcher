import os
import re
import gettext
from ruamel.yaml import YAML
from modules.reg import fetch_reg

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


t = gettext.translation('loginusers',
                        localedir='../locale',
                        languages=[LOCALE],
                        fallback=True)
_ = t.gettext


def loginusers(steam_path=fetch_reg('steampath')):
    '''
    Fetch loginusers.vdf and return AccountName and
    PersonaName values as lists.
    :param steam_path: Steam installation path override
    '''
    if os.path.isfile('steam_path.txt'):
        with open('steam_path.txt', 'r') as path:
            steam_path = path.read()

    if '/' in steam_path:
        steam_path = steam_path.replace('/', '\\')

    vdf_file = os.path.join(steam_path, 'config', 'loginusers.vdf')

    try:
        with open(vdf_file, 'r', encoding='utf-8') as vdf_file:
            vdf = vdf_file.read().splitlines()
    except FileNotFoundError:
        return False

    AccountName = []
    PersonaName = []

    rep = {"\t": "", '"': ""}
    rep = dict((re.escape(k), v) for k, v in rep.items())
    pattern = re.compile("|".join(rep.keys()))

    for i, v in enumerate(vdf):
        if v == "\t{":
            account = pattern.sub(lambda m: rep[re.escape(m.group(0))], vdf[i+1])  # NOQA
            persona = pattern.sub(lambda m: rep[re.escape(m.group(0))], vdf[i+2])  # NOQA
            AccountName.append(account.replace("AccountName", ""))
            PersonaName.append(persona.replace("PersonaName", ""))
    return AccountName, PersonaName
