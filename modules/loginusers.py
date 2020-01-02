import os
import re
from modules.reg import fetch_reg


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
