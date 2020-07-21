import os
import re
from modules.config import get_config
from modules.reg import fetch_reg
from ruamel.yaml import YAML

yaml = YAML()

if not os.path.isfile('accounts.yml'):
    acc = open('accounts.yml', 'w')
    acc.close()


def acc_getlist():
    with open('accounts.yml', 'r', encoding='utf-8') as acc:
        acc_dict = yaml.load(acc)

    accounts = []
    if acc_dict:
        for x in range(len(acc_dict)):  # to preserve the order
            try:
                cur_dict = acc_dict[x]
                accounts.append(cur_dict['accountname'])
            except KeyError:
                break
    return accounts


def acc_getdict():
    with open('accounts.yml', 'r', encoding='utf-8') as acc:
        acc_dict = yaml.load(acc)
    if not acc_dict:
        acc_dict = {}

    return acc_dict


def loginusers():
    '''
    Fetch loginusers.vdf and return SteamID64, AccountName,
    PersonaName values as lists.
    :param steam_path: Steam installation path override
    '''
    if get_config('steam_path') == 'reg':
        steam_path = fetch_reg('steam_path')
    else:
        steam_path = get_config('steam_path')

    if '/' in steam_path:
        steam_path = steam_path.replace('/', '\\')

    vdf_file = os.path.join(steam_path, 'config', 'loginusers.vdf')

    try:
        with open(vdf_file, 'r', encoding='utf-8') as vdf_file:
            vdf = vdf_file.read().splitlines()
    except FileNotFoundError:
        return [], [], []

    steam64_list = []
    account_name = []
    persona_name = []

    rep = {"\t": "", '"': ""}
    rep = dict((re.escape(k), v) for k, v in rep.items())
    pattern = re.compile("|".join(rep.keys()))

    for i, v in enumerate(vdf):
        if v == "\t{":
            steam64 = pattern.sub(lambda m: rep[re.escape(m.group(0))], vdf[i-1])
            account = pattern.sub(lambda m: rep[re.escape(m.group(0))], vdf[i+1])
            persona = pattern.sub(lambda m: rep[re.escape(m.group(0))], vdf[i+2])
            steam64_list.append(steam64)
            account_name.append(account.replace("AccountName", ""))
            persona_name.append(persona.replace("PersonaName", ""))
    return steam64_list, account_name, persona_name
