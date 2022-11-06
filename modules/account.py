import os
import re
import json
from modules.config import get_config
from modules.reg import fetch_reg
from ruamel.yaml import YAML
import vdf


def pprint(*args, **kwargs):
    print('[account]', *args, **kwargs)


def convert():
    yaml = YAML()
    with open('accounts.yml', 'r', encoding='utf-8') as f:
        original = yaml.load(f)

    with open('accounts.json', 'w', encoding='utf-8') as f:
        json.dump(original, f, indent=4)

    #os.remove('accounts.yml')
    pprint('Converted accounts.yml to accounts.json')


if not os.path.isfile('accounts.json'):
    with open('accounts.json', 'w', encoding='utf-8') as f:
        json.dump({}, f, indent=4)


class AccountManager:
    def __init__(self):
        try:
            with open('accounts.json', 'r', encoding='utf-8') as acc:
                self.acc_dict = json.load(acc)
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            with open('accounts.json', 'w', encoding='utf-8') as f:
                self.acc_dict = {}
                json.dump(self.acc_dict, f, indent=4)

    @property
    def list(self):
        accounts = []

        for x in range(len(self.acc_dict)):
            accounts.append(self.acc_dict[str(x)]['accountname'])

        return accounts

    @property
    def dict(self):
        return self.acc_dict

    def __bool__(self):
        return bool(self.acc_dict)

    def _find_account_index(self, accountname):
        for x in range(len(self.acc_dict)):
            if self.acc_dict[str(x)]['accountname'] == accountname:
                return str(x)

    def update_dict_numbers(self):
        new_dict = {}
        buffer = []

        for value in self.acc_dict.values():
            buffer.append(value)

        for index, value in enumerate(buffer):
            new_dict[str(index)] = value

        self.acc_dict = new_dict

    def add(self, accountname, password=None, save=True):
        if accountname in self.list:
            pprint(f'Account {accountname} already exists!')
            return False

        self.acc_dict[len(self.acc_dict)] = {'accountname': accountname,
                                             'password': password}
        pprint(f'Added account: {accountname}')
        if save:
            self._save_json()
        return True

    def add_multiple_accounts(self, account_list):
        existing = []
        for account in account_list:
            if not self.add(account, save=False):
                existing.append(account)

        self._save_json()
        return existing

    def remove(self, accountname, save=True):
        i = self._find_account_index(accountname)
        del self.acc_dict[i]
        pprint(f'Removed account: {accountname}')

        if save:
            self._save_json()

    def remove_multiple_accounts(self, account_list):
        for account in account_list:
            self.remove(account, save=False)

        self._save_json()

    def set_password(self, accountname, password):
        i = self._find_account_index(accountname)
        self.acc_dict[i]['password'] = password

        self._save_json()

    def remove_password(self, accountname):
        i = self._find_account_index(accountname)
        del self.acc_dict[i]['password']

        self._save_json()

    def get_customname(self, accountname):
        i = self._find_account_index(accountname)
        try:
            return self.acc_dict[i]['customname']
        except KeyError:
            return None

    def set_customname(self, accountname, customname):
        i = self._find_account_index(accountname)
        self.acc_dict[i]['customname'] = customname

        self._save_json()

    def remove_customname(self, accountname):
        i = self._find_account_index(accountname)
        del self.acc_dict[i]['customname']

        self._save_json()

    def change_dict_order(self, order_list):
        buffer_dict = {}

        for account in self.acc_dict.values():
            i = order_list.index(account['accountname'])
            buffer_dict[i] = account

        new_dict = {}

        for x in range(len(buffer_dict)):
            new_dict[x] = buffer_dict[x]

        self.acc_dict = new_dict
        self._save_json()

    def _save_json(self):
        self.update_dict_numbers()
        with open('accounts.json', 'w', encoding='utf-8') as f:
            json.dump(self.acc_dict, f, indent=4)

        pprint('Saved accounts.json')

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


if os.path.isfile('accounts.yml'):
    convert()