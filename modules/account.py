import os
import re
from modules.config import get_config
from modules.reg import fetch_reg
from ruamel.yaml import YAML
import vdf

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


def fetch_loginusers():
    """
    Returns the contents of loginusers.vdf as dict
    :returns: dict
    """
    if get_config('steam_path') == 'reg':
        steam_path = fetch_reg('steampath')
    else:
        steam_path = get_config('steam_path')

    if '/' in steam_path:
        steam_path = steam_path.replace('/', '\\')

    vdf_file = os.path.join(steam_path, 'config', 'loginusers.vdf')

    try:
        with open(vdf_file, 'r', encoding='utf-8') as vdf_file:
            return vdf.load(vdf_file)
    except FileNotFoundError:
        return {}


def loginusers_accountnames():
    """
    Returns a list of account names from loginusers.vdf
    :returns: list
    """
    loginusers = fetch_loginusers()
    accounts = []
    for user in loginusers['users'].values():
        accounts.append(user['AccountName'])
    return accounts


def loginusers_steamid():
    """
    Returns a list of SteamIDs from loginusers.vdf
    :returns: list
    """
    loginusers = fetch_loginusers()
    steamid_list = []
    for steamid in loginusers['users'].keys():
        steamid_list.append(steamid)
    return steamid_list


def loginusers_personanames():
    """
    Returns a list of personanames from loginusers.vdf
    :returns: list
    """
    loginusers = fetch_loginusers()
    personanames = []
    for user in loginusers['users'].values():
        personanames.append(user['PersonaName'])
    return personanames


def check_autologin_availability(username):
    """
    Checks if the username is available for autologin
    :param username: str
    :returns: bool
    """
    loginusers_dict = fetch_loginusers()

    for user in loginusers_dict['users'].values():
        if user['AccountName'] == username:
            return user['AllowAutoLogin'] == '1'
        else:
            continue

    return False
