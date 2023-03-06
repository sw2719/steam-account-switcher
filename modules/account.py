import os
import json
import vdf
import base64
import win32con, win32api
from ruamel.yaml import YAML
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import InvalidToken
from modules.config import get_config
from modules.reg import fetch_reg


def pprint(*args, **kwargs):
    print('[account]', *args, **kwargs)


def convert():
    yaml = YAML()
    with open('accounts.yml', 'r', encoding='utf-8') as f:
        original = yaml.load(f)

    if not original:
        with open('accounts.json', 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4)
        return

    new_dict = {}

    for x in range(len(original)):
        new_dict[str(x)] = original[x]

    with open('accounts.json', 'w', encoding='utf-8') as f:
        json.dump(original, f, indent=4)

    os.remove('accounts.yml')
    pprint('Converted accounts.yml to accounts.json')


class AccountManager:
    def __init__(self, password=None):
        try:
            with open('accounts.json', 'r', encoding='utf-8') as f:
                self.acc_dict = json.load(f)
        except json.decoder.JSONDecodeError:
            if get_config('encryption') == 'true':
                if password is None:
                    raise ValueError('Password is required to decrypt accounts.json')
                else:
                    with open('salt', 'rb') as f:
                        salt = f.read()

                    kdf = PBKDF2HMAC(
                        algorithm=hashes.SHA256(),
                        length=32,
                        salt=salt,
                        iterations=600000,
                    )

                    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
                    self.fernet = Fernet(key)

                    with open('accounts.json', 'rb') as f:
                        secret = self.fernet.decrypt(f.read())
                        self.acc_dict = json.loads(secret.decode('utf-8'))
                        pprint('Decrypted accounts.json successfully')
            else:
                self.acc_dict = {}
                self.reset_json()

        except FileNotFoundError:
            self.reset_json()

        pprint('AccountManager initialized')

    @staticmethod
    def verify_password(password):
        with open('salt', 'rb') as f:
            salt = f.read()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        fernet = Fernet(key)

        try:
            with open('accounts.json', 'rb') as f:
                secret = fernet.decrypt(f.read())
                json.loads(secret.decode('utf-8'))
                pprint('Password authentication success')
                return True
        except (InvalidToken, json.decoder.JSONDecodeError):
            pprint('Password authentication fail')
            return False

    @staticmethod
    def reset_json():
        with open('accounts.json', 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4)
        pprint('New account.json created')

    @staticmethod
    def generate_salt():
        salt = os.urandom(16)
        with open('salt', 'wb') as f:
            f.write(salt)
        pprint('Generated salt')

        return salt

    def set_master_password(self, password):
        salt = self.generate_salt()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.fernet = Fernet(key)

        with open('accounts.json', 'wb') as f:
            enc_dict = self.fernet.encrypt(json.dumps(self.acc_dict).encode())
            f.write(enc_dict)
            pprint('Set master password')

    def disable_encryption(self):
        with open('accounts.json', 'w', encoding='utf-8') as f:
            json.dump(self.acc_dict, f, indent=4)

            os.remove('salt')
            pprint('Disabled encryption')

    @staticmethod
    def create_encrypted_json_file(password):
        with open('salt', 'wb') as f:
            salt = os.urandom(16)
            f.write(salt)

        if os.path.isfile('accounts.json'):
            with open('accounts.json', 'r') as f:
                d = json.load(f)
        else:
            d = {}

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        fernet = Fernet(key)

        with open('accounts.json', 'wb') as f:
            enc_dict = fernet.encrypt(json.dumps(d).encode())
            f.write(enc_dict)

        pprint('Created encrypted accounts.json')

    @property
    def list(self):
        accounts = []

        if self.acc_dict:
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
        else:
            return None

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

        self.acc_dict[str(len(self.acc_dict))] = {'accountname': accountname}
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
        try:
            i = self._find_account_index(accountname)
            del self.acc_dict[i]['password']

            self._save_json()
        except KeyError:
            pass

    def get_password(self, accountname):
        i = self._find_account_index(accountname)
        try:
            return self.acc_dict[i]['password']
        except KeyError:
            return None

    def get_customname(self, accountname):
        i = self._find_account_index(accountname)
        try:
            return self.acc_dict[i]['customname']
        except KeyError:
            return ''

    def set_customname(self, accountname, customname):
        i = self._find_account_index(accountname)
        self.acc_dict[i]['customname'] = customname

        self._save_json()

    def remove_customname(self, accountname):
        try:
            i = self._find_account_index(accountname)
            del self.acc_dict[i]['customname']

            self._save_json()
        except KeyError:
            pass

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

        if get_config('encryption') == 'true':
            with open('accounts.json', 'wb') as f:
                enc_dict = self.fernet.encrypt(json.dumps(self.acc_dict).encode())
                f.write(enc_dict)
        else:
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