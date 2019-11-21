import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox as msgbox
from tkinter import filedialog
import winreg
import sys
import os
import subprocess
import requests as req
import gettext
import locale
import psutil
import re
import threading
import queue as q
import zipfile as zf
import shutil
from packaging import version
from time import sleep
from ruamel.yaml import YAML

system_locale = locale.getdefaultlocale()[0]

print('App Start')

BRANCH = 'master'

__VERSION__ = '1.7.2'

if getattr(sys, 'frozen', False):
    print('Running in a bundle')
    BUNDLE = True
    if os.path.isdir('updater'):
        try:
            shutil.rmtree('updater')
        except OSError:
            pass
else:
    print('Running in a Python interpreter')
    BUNDLE = False

config_dict = {}


def error_msg(title, content):
    '''Show error message and exit'''
    root = tk.Tk()
    root.withdraw()
    msgbox.showerror(title, content)
    root.destroy()
    sys.exit(1)


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

try:  # Open config.yml and save values to config_dict
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
    with open('config.yml', 'r') as cfg:
        config_dict = yaml.load(cfg)

except FileNotFoundError:
    reset_config()

if config_dict['locale'] in ('ko_KR', 'en_US'):
    LOCALE = config_dict['locale']
else:
    LOCALE = 'en_US'

print('Using locale', LOCALE)

t = gettext.translation('steamswitcher',
                        localedir='locale',
                        languages=[LOCALE],
                        fallback=True)
_ = t.gettext

print('Running on', os.getcwd())

URL = ('https://raw.githubusercontent.com/sw2719/steam-account-switcher/%s/version.yml'  # NOQA
       % BRANCH)


HKCU = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)


def start_checkupdate():
    '''Check if application has update'''
    update_frame = tk.Frame(main)
    update_frame.pack(side='bottom')

    if not BUNDLE:
        update_label = tk.Label(update_frame, text=_('Using source file'))
        update_label.pack()
        return

    checking_label = tk.Label(update_frame, text=_('Checking for updates...'))
    checking_label.pack()
    main.update()

    def update(sv_version, changelog):
        updatewindow = tk.Toplevel(main)
        updatewindow.title(_('Update'))
        updatewindow.geometry("400x300+650+300")
        updatewindow.resizable(False, False)

        button_frame = tk.Frame(updatewindow)
        button_frame.pack(side=tk.BOTTOM, pady=3)

        cancel_button = ttk.Button(button_frame, text=_('Cancel'),
                                   command=updatewindow.destroy)
        update_button = ttk.Button(button_frame, text=_('Update now'))

        text_frame = tk.Frame(updatewindow)
        text_frame.pack(side=tk.TOP, pady=3)
        text = tk.Label(text_frame,
                        text=_('New version %s is available.') % sv_version)
        text.pack()

        changelog_box = tk.Text(updatewindow, width=57)
        scrollbar = ttk.Scrollbar(updatewindow, orient=tk.VERTICAL,
                                  command=changelog_box.yview)
        changelog_box.config(yscrollcommand=scrollbar.set)
        changelog_box.insert(tk.CURRENT, changelog)
        changelog_box.configure(state=tk.DISABLED)
        changelog_box.pack(padx=5)

        def start_update():
            nonlocal button_frame
            nonlocal cancel_button
            nonlocal update_button

            cancel_button.destroy()
            update_button.destroy()

            dl_p = tk.IntVar()
            dl_p.set(0)
            dl_pbar = ttk.Progressbar(button_frame,
                                      length=180,
                                      orient=tk.HORIZONTAL,
                                      variable=dl_p)
            dl_pbar.pack()
            main.update()

            download_q = q.Queue()
            dl_url = f'https://github.com/sw2719/steam-account-switcher/releases/download/v{sv_version}/Steam_Account_Switcher_v{sv_version}.zip'  # NOQA

            def download(url):
                nonlocal download_q
                with open('update.zip', "wb") as f:
                    response = req.get(url, stream=True)
                    total_length = response.headers.get('content-length')

                    if total_length is None:
                        f.write(response.content)
                    else:
                        dl = 0
                        total_length = int(total_length)
                        for data in response.iter_content(chunk_size=4096):
                            dl += len(data)
                            f.write(data)
                            done = int(100 * dl / total_length)
                            download_q.put(done)

            def update_pbar():
                nonlocal download_q
                nonlocal dl_p
                while True:
                    try:
                        done = download_q.get_nowait()
                        p = int(done)
                        dl_p.set(p)
                        main.update()
                        if p == 100:
                            return
                    except q.Empty:
                        main.update()

            dl_thread = threading.Thread(target=lambda url=dl_url: download(url))  # NOQA
            dl_thread.start()

            update_pbar()

            try:
                archive = os.path.join(os.getcwd(), 'update.zip')

                f = zf.ZipFile(archive, mode='r')
                f.extractall(members=(member for member in f.namelist() if 'updater' in member)) # NOQA

                subprocess.run('start updater/updater.exe', shell=True)
                sys.exit(0)
            except (FileNotFoundError, zf.BadZipfile, OSError):
                error_msg(_('Error'), _("Couldn't perform automatic update.") + '\n' + # NOQA
                        _('Update manually by extracting update.zip file.'))

        update_button['command'] = start_update
        cancel_button.pack(side='left', padx=1.5)
        update_button.pack(side='left', padx=1.5)

    queue = q.Queue()

    def checkupdate():
        '''Fetch version information from GitHub and
        return different update codes'''
        print('Update check start')
        update = None
        try:
            response = req.get(URL)
            response.encoding = 'utf-8'
            text = response.text
            version_data = yaml.load(text)
            sv_version_str = str(version_data['version'])
            if LOCALE == 'ko_KR':
                changelog = version_data['changelog_ko']
            else:
                changelog = version_data['changelog_en']
            try:
                critical_msg = version_data['msg'][str(__VERSION__)]
                if critical_msg:
                    if LOCALE == 'ko_KR':
                        msgbox.showinfo(_('Info'),
                                        critical_msg['ko'])
                    else:
                        msgbox.showinfo(_('Info'),
                                        critical_msg['en'])
            except KeyError:
                pass
            print('Server version is', sv_version_str)
            print('Client version is', __VERSION__)

            sv_version = version.parse(sv_version_str)
            cl_version = version.parse(__VERSION__)

            if sv_version > cl_version:
                update = 'avail'
            elif sv_version == cl_version:
                update = 'latest'
            elif sv_version < cl_version:
                update = 'dev'

        except Exception:
            update = 'error'
            sv_version_str = '0'
            changelog = None
        queue.put((update, sv_version_str, changelog))

    update_code = None
    sv_version = None
    changelog = None

    def get_output():
        '''Get version info from checkupdate() and draw UI accordingly.'''
        nonlocal update_code
        nonlocal sv_version
        nonlocal changelog
        nonlocal checking_label
        try:
            v = queue.get_nowait()
            update_code = v[0]
            sv_version = v[1]
            changelog = v[2]
            checking_label.destroy()

            if update_code == 'avail':
                print('Update Available')

                update_label = tk.Label(update_frame,
                                        text=_('New update available'))  # NOQA
                update_label.pack(side='left', padx=5)

                update_button = ttk.Button(update_frame,
                                            text=_('Update'),
                                            width=10,
                                            command=lambda: update(sv_version=sv_version, changelog=changelog))  # NOQA

                update_button.pack(side='right', padx=5)
            elif update_code == 'latest':
                print('On latest version')

                update_label = tk.Label(update_frame,
                                        text=_('Using the latest version'))
                update_label.pack(side='bottom')
            elif update_code == 'dev':
                print('Development version')

                update_label = tk.Label(update_frame,
                                        text=_('Development version'))
                update_label.pack(side='bottom')
            else:
                print('Exception while getting server version')

                update_label = tk.Label(update_frame,
                                        text=_('Failed to check for updates'))  # NOQA
                update_label.pack(side='bottom')
        except q.Empty:
            main.after(300, get_output)

    t = threading.Thread(target=checkupdate)
    t.start()
    main.after(300, get_output)


def afterupdate():
    if os.path.isfile('update.zip'):
        try:
            os.remove('update.zip')
        except OSError:
            pass


def check_running(process_name):
    '''Check if given process is running and return boolean value.
    :param process_name: Name of process to check
    '''
    for process in psutil.process_iter():
        try:
            if process_name.lower() in process.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied,
                psutil.ZombieProcess):
            pass
    return False


def fetch_reg(key):
    '''Return given key's value from steam registry path.
    :param key: 'username', 'autologin', 'steamexe', 'steampath'
    '''
    if key == 'username':
        key_name = 'AutoLoginUser'
    elif key == 'autologin':
        key_name = 'RememberPassword'
    elif key == 'steamexe':
        key_name = 'SteamExe'
    elif key == 'steampath':
        key_name = 'SteamPath'

    try:
        reg_key = winreg.OpenKey(HKCU, r"Software\Valve\Steam")
        value_buffer = winreg.QueryValueEx(reg_key, key_name)
        value = value_buffer[0]
        winreg.CloseKey(reg_key)
    except OSError:
        error_msg(_('Registry Error'),
                  _('Failed to read registry value.') + '\n' +
                  _('Make sure that Steam is installed.'))
    return value


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


def autologinstr():
    '''Return autologin status messages according to current config.'''
    value = fetch_reg('autologin')
    if value == 1:
        return_str = _('Auto-login Enabled')
    elif value == 0:
        return_str = _('Auto-login Disabled')
    return return_str


print('Fetching registry values...')
if fetch_reg('autologin') != 2:
    print('Autologin value is ' + str(fetch_reg('autologin')))
else:
    print('Could not fetch autologin status!')
if fetch_reg('autologin'):
    print('Current autologin user is ' + str(fetch_reg('username')))
else:
    print('Could not fetch autologin user information!')


def convert_to_yaml():
    try:
        with open('accounts.txt', 'r') as txt:
            namebuffer = txt.read().splitlines()

        dump_dict = {}
        accounts = [item for item in namebuffer if item.strip()]

        for i, v in enumerate(accounts):
            dump_dict[i] = {'accountname': v}

        with open('accounts.yml', 'w') as acc:
            yaml = YAML()
            yaml.dump(dump_dict, acc)

        os.remove('accounts.txt')
    except Exception:
        msgbox.showinfo(_('Information'),
                        _('With version 1.6, data format has been changed.') + '\n'  # NOQA
                      + _('Attempt to convert your account data has failed.') + '\n'  # NOQA
                      + _('Please add them manually or try again by restarting app.'))  # NOQA
        pass


if os.path.isfile('accounts.txt'):
    if not os.path.isfile('accounts.yml'):
        convert_to_yaml()

try:
    with open('accounts.yml', 'r') as acc:
        acc_dict = yaml.load(acc)
        accounts = []
        if acc_dict:
            for x in range(len(acc_dict)):  # to preserve the order
                try:
                    cur_dict = acc_dict[x]
                    accounts.append(cur_dict['accountname'])
                except KeyError:
                    break
        else:
            raise FileNotFoundError
    if not accounts:
        raise FileNotFoundError
except (FileNotFoundError, TypeError):
    acc = open('accounts.yml', 'w')
    acc.close()
    accounts = []
    acc_dict = {}

print('Detected ' + str(len(accounts)) + ' accounts:')

if accounts:
    print('------------------')
    for username in accounts:
        print(username)
    print('------------------')


def fetchuser():
    '''Fetch accounts.yml file, add accountnames to list accounts
    and save it to global list accounts'''
    global acc_dict
    global accounts
    with open('accounts.yml', 'r') as acc:
        acc_dict = yaml.load(acc)
        accounts = []
        if acc_dict:
            for x in range(len(acc_dict)):  # to preserve the order
                try:
                    cur_dict = acc_dict[x]
                    accounts.append(cur_dict['accountname'])
                except KeyError:
                    break
        else:
            acc_dict = {}


def setkey(key_name, value, value_type):
    '''Change given key's value to given value.
    :param key_name: Name of key to change value of
    :param value: Value to change to
    :param value_type: Registry value type
    '''
    try:
        reg_key = winreg.OpenKey(HKCU, r"Software\Valve\Steam", 0,
                                 winreg.KEY_ALL_ACCESS)

        winreg.SetValueEx(reg_key, key_name, 0, value_type, value)
        winreg.CloseKey(reg_key)
        print("Changed %s's value to %s" % (key_name, str(value)))
    except OSError:
        error_msg(_('Registry Error'), _('Failed to change registry value.'))


def toggleAutologin():
    '''Toggle autologin registry value between 0 and 1'''
    if fetch_reg('autologin') == 1:
        value = 0
    elif fetch_reg('autologin') == 0:
        value = 1
    setkey('RememberPassword', value, winreg.REG_DWORD)
    refresh()


def about():
    '''Open about window'''
    aboutwindow = tk.Toplevel(main)
    aboutwindow.title(_('About'))
    aboutwindow.geometry("360x250+650+300")
    aboutwindow.resizable(False, False)
    about_row = tk.Label(aboutwindow, text=_('Made by sw2719 (Myeuaa)'))
    about_steam = tk.Label(aboutwindow,
                           text='Steam: https://steamcommunity.com/'
                           + 'id/muangmuang')
    about_email = tk.Label(aboutwindow, text='E-mail: sw2719@naver.com')
    about_disclaimer = tk.Label(aboutwindow,
                                text=_('Warning: The developer of this application is not responsible for')  # NOQA
                                + '\n' + _('data loss or any other damage from the use of this app.'))  # NOQA
    about_steam_trademark = tk.Label(aboutwindow, text=_('STEAM is a registered trademark of Valve Corporation.'))  # NOQA
    copyright_label = tk.Label(aboutwindow, text='Copyright (c) sw2719 | All Rights Reserved\n'  # NOQA
                               + 'Licensed under the MIT License.')
    version = tk.Label(aboutwindow,
                       text='Steam Account Switcher | Version ' + __VERSION__)

    def close():
        aboutwindow.destroy()

    button_exit = ttk.Button(aboutwindow,
                             text=_('Close'),
                             width=8,
                             command=close)
    about_row.pack(pady=8)
    about_steam.pack()
    about_email.pack()
    about_disclaimer.pack(pady=5)
    about_steam_trademark.pack()
    copyright_label.pack(pady=5)
    version.pack()
    button_exit.pack(side='bottom', pady=5)


def addwindow():
    '''Open add accounts window'''
    global accounts
    global acc_dict

    addwindow = tk.Toplevel(main)
    addwindow.title(_("Add"))
    addwindow.geometry("300x150+650+300")
    addwindow.resizable(False, False)

    topframe_add = tk.Frame(addwindow)
    topframe_add.pack(side='top', anchor='center')

    bottomframe_add = tk.Frame(addwindow)
    bottomframe_add.pack(side='bottom', anchor='e')

    addlabel_row1 = tk.Label(topframe_add,
                             text=_('Enter accounts(s) to add.'))
    addlabel_row2 = tk.Label(topframe_add,
                             text=_("In case of adding multiple accounts,") +
                             '\n' + _("seperate each account with '/' (slash)."))  # NOQA

    account_entry = ttk.Entry(bottomframe_add, width=29)

    addwindow.grab_set()
    addwindow.focus()
    account_entry.focus()

    print('Opened add window.')

    def adduser(userinput):
        global acc_dict
        '''Write accounts from user's input to accounts.txt
        :param userinput: Account names to add
        '''
        if userinput.strip():
            cfg = open('accounts.yml', 'w')
            name_buffer = userinput.split("/")

            for name_to_write in name_buffer:
                if name_to_write.strip():
                    if name_to_write not in accounts:
                        acc_dict[len(acc_dict)] = {
                            'accountname': name_to_write
                            }
                    else:
                        print('Alert: Account %s already exists!'
                              % name_to_write)
                        msgbox.showinfo(_('Duplicate Alert'),
                                        _('Account %s already exists.')
                                        % name_to_write)
            with open('accounts.yml', 'w') as acc:
                yaml = YAML()
                yaml.dump(acc_dict, acc)

            cfg.close()
            refresh()
        addwindow.destroy()

    def close():
        addwindow.destroy()

    def enterkey(event):
        adduser(account_entry.get())

    addwindow.bind('<Return>', enterkey)
    button_add = ttk.Button(bottomframe_add, width=9, text=_('Add'),
                            command=lambda: adduser(account_entry.get()))
    button_addcancel = ttk.Button(addwindow, width=9,
                                  text=_('Cancel'), command=close)
    addlabel_row1.pack(pady=10)
    addlabel_row2.pack()

    account_entry.pack(side='left', padx=3, pady=3)
    button_add.pack(side='left', anchor='e', padx=3, pady=3)
    button_addcancel.pack(side='bottom', anchor='e', padx=3)


def importwindow():
    '''Open import accounts window'''
    global accounts
    global acc_dict
    if loginusers():
        AccountName, PersonaName = loginusers()
    else:
        try_manually = msgbox.askyesno(_('Alert'), _('Could not load loginusers.vdf.')  # NOQA
                               + '\n' + _('This may be because Steam directory defined')  # NOQA
                               + '\n' + _('in registry is invalid.')  # NOQA
                               + '\n\n' + _('Do you want to select Steam directory manually?'))  # NOQA
        if try_manually:
            while True:
                input_dir = filedialog.askdirectory()
                if loginusers(steam_path=input_dir):
                    AccountName, PersonaName = loginusers(steam_path=input_dir)
                    with open('steam_path.txt', 'w') as path:
                        path.write(input_dir)
                    break
                else:
                    try_again = msgbox.askyesno(_('Warning'),
                                                    _('Steam directory is invalid.')  # NOQA
                                                    + '\n' + _('Try again?'))
                    if try_again:
                        continue
                    else:
                        return
        else:
            return

    importwindow = tk.Toplevel(main)
    importwindow.title(_("Import"))
    importwindow.geometry("280x300+650+300")
    importwindow.resizable(False, False)

    importwindow.grab_set()
    importwindow.focus()

    bottomframe_imp = tk.Frame(importwindow)
    bottomframe_imp.pack(side='bottom')

    importlabel = tk.Label(importwindow, text=_('Select accounts to import.')
                           + '\n' + _("Added accounts don't show up."))
    importlabel.pack(side='top',
                     padx=5,
                     pady=5)
    print('Opened import window.')

    def close():
        importwindow.destroy()

    def onFrameConfigure(canvas):
        '''Reset the scroll region to encompass the inner frame'''
        canvas.configure(scrollregion=canvas.bbox("all"))

    canvas = tk.Canvas(importwindow, borderwidth=0, highlightthickness=0)
    check_frame = tk.Frame(canvas)
    scroll_bar = ttk.Scrollbar(importwindow,
                               orient="vertical",
                               command=canvas.yview)

    canvas.configure(yscrollcommand=scroll_bar.set)

    scroll_bar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.create_window((4, 4), window=check_frame, anchor="nw")

    check_frame.bind("<Configure>", lambda event,
                     canvas=canvas: onFrameConfigure(canvas))

    def _on_mousewheel(event):
        '''Scroll window on mousewheel input'''
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas.bind("<MouseWheel>", _on_mousewheel)

    check_dict = {}

    for i, v in enumerate(AccountName):
        if v not in accounts:
            tk_var = tk.IntVar()
            checkbutton = ttk.Checkbutton(check_frame,
                                          text=v + f' ({PersonaName[i]})',
                                          variable=tk_var)
            checkbutton.bind("<MouseWheel>", _on_mousewheel)
            checkbutton.pack(side='top', padx=2, anchor='w')
            check_dict[v] = tk_var

    def import_user():
        global acc_dict
        for key, value in check_dict.items():
            if value.get() == 1:
                acc_dict[len(acc_dict)] = {'accountname': key}
        with open('accounts.yml', 'w') as acc:
            yaml = YAML()
            yaml.dump(acc_dict, acc)
        refresh()
        close()

    import_cancel = ttk.Button(bottomframe_imp,
                               text=_('Cancel'),
                               command=close,
                               width=9)
    import_ok = ttk.Button(bottomframe_imp,
                           text=_('Import'),
                           command=import_user,
                           width=9)

    import_cancel.pack(side='left', padx=5, pady=3)
    import_ok.pack(side='left', padx=5, pady=3)


def removewindow():
    '''Open remove accounts window'''
    global accounts
    if not accounts:
        msgbox.showinfo(_('No Accounts'),
                        _("There's no account to remove."))
        return
    removewindow = tk.Toplevel(main)
    removewindow.title(_("Remove"))
    removewindow.geometry("230x320+650+300")
    removewindow.resizable(False, False)
    bottomframe_rm = tk.Frame(removewindow)
    bottomframe_rm.pack(side='bottom')
    removewindow.grab_set()
    removewindow.focus()
    removelabel = tk.Label(removewindow, text=_('Select accounts to remove.'))
    removelabel.pack(side='top',
                     padx=5,
                     pady=5)
    print('Opened remove window.')

    def close():
        removewindow.destroy()

    def onFrameConfigure(canvas):
        '''Reset the scroll region to encompass the inner frame'''
        canvas.configure(scrollregion=canvas.bbox("all"))

    canvas = tk.Canvas(removewindow, borderwidth=0, highlightthickness=0)
    check_frame = tk.Frame(canvas)
    scroll_bar = ttk.Scrollbar(removewindow,
                               orient="vertical",
                               command=canvas.yview)

    canvas.configure(yscrollcommand=scroll_bar.set)

    scroll_bar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.create_window((4, 4), window=check_frame, anchor="nw")

    def _on_mousewheel(event):
        '''Scroll window on mousewheel input'''
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    check_frame.bind("<Configure>", lambda event,
                     canvas=canvas: onFrameConfigure(canvas))
    canvas.bind("<MouseWheel>", _on_mousewheel)

    check_dict = {}

    for v in accounts:
        tk_var = tk.IntVar()
        checkbutton = ttk.Checkbutton(check_frame,
                                      text=v,
                                      variable=tk_var)
        checkbutton.bind("<MouseWheel>", _on_mousewheel)
        checkbutton.pack(side='top', padx=2, anchor='w')
        check_dict[v] = tk_var

    def removeuser():
        '''Write accounts to accounts.txt except the
        ones user wants to delete'''
        print('Remove function start')
        to_remove = []
        for v in accounts:
            if check_dict.get(v).get() == 1:
                to_remove.append(v)
                print('%s is to be removed.' % v)
            else:
                continue

        dump_dict = {}

        print('Removing selected accounts...')
        with open('accounts.yml', 'w') as acc:
            for username in accounts:
                if username not in to_remove:
                    dump_dict[len(dump_dict)] = {'accountname': username}
            yaml = YAML()
            yaml.dump(dump_dict, acc)
        refresh()
        close()

    remove_cancel = ttk.Button(bottomframe_rm,
                               text=_('Cancel'),
                               command=close,
                               width=9)
    remove_ok = ttk.Button(bottomframe_rm,
                           text=_('Remove'),
                           command=removeuser,
                           width=9)

    remove_cancel.pack(side='left', padx=5, pady=3)
    remove_ok.pack(side='left', padx=5, pady=3)


def orderwindow():
    '''Open order change window'''
    global accounts

    orderwindow = tk.Toplevel(main)
    orderwindow.title("")
    orderwindow.geometry("210x300+650+300")
    orderwindow.resizable(False, False)

    bottomframe_windowctrl = tk.Frame(orderwindow)
    bottomframe_windowctrl.pack(side='bottom', padx=3, pady=3)

    bottomframe_orderctrl = tk.Frame(orderwindow)
    bottomframe_orderctrl.pack(side='bottom', padx=3, pady=3)

    labelframe = tk.Frame(orderwindow)
    labelframe.pack(side='bottom', padx=3)

    orderwindow.grab_set()
    orderwindow.focus()

    lbframe = tk.Frame(orderwindow)

    class DragDropListbox(tk.Listbox):
        '''Listbox with drag reordering of entries'''
        def __init__(self, master, **kw):
            kw['selectmode'] = tk.SINGLE
            tk.Listbox.__init__(self, master, kw)
            self.bind('<Button-1>', self.setCurrent)
            self.bind('<B1-Motion>', self.shiftSelection)
            self.curIndex = None

        def setCurrent(self, event):
            self.curIndex = self.nearest(event.y)

        def shiftSelection(self, event):
            i = self.nearest(event.y)
            if i < self.curIndex:
                x = self.get(i)
                self.delete(i)
                self.insert(i+1, x)
                self.curIndex = i
            elif i > self.curIndex:
                x = self.get(i)
                self.delete(i)
                self.insert(i-1, x)
                self.curIndex = i

    scrollbar = ttk.Scrollbar(lbframe)
    scrollbar.pack(side='right', fill='y')

    lb = DragDropListbox(lbframe, height=12, width=26,
                         highlightthickness=0,
                         yscrollcommand=scrollbar.set)

    scrollbar["command"] = lb.yview

    def _on_mousewheel(event):
        '''Scroll window on mousewheel input'''
        lb.yview_scroll(int(-1*(event.delta/120)), "units")

    lb.bind("<MouseWheel>", _on_mousewheel)
    lb.pack(side='left')

    for i, v in enumerate(accounts):
        lb.insert(i, v)

    lb.select_set(0)
    lbframe.pack(side='top', pady=5)

    lb_label1 = tk.Label(labelframe, text=_('Drag or use buttons below'))
    lb_label2 = tk.Label(labelframe, text=_('to change order.'))

    lb_label1.pack()
    lb_label2.pack()

    def down():
        i = lb.curselection()[0]
        if i == lb.size() - 1:
            return
        x = lb.get(i)
        lb.delete(i)
        lb.insert(i+1, x)
        lb.select_set(i+1)

    def up():
        i = lb.curselection()[0]
        if i == 0:
            return
        x = lb.get(i)
        lb.delete(i)
        lb.insert(i-1, x)
        lb.select_set(i-1)

    def apply():
        order = lb.get(0, tk.END)
        print('New order is', order)

        buffer_dict = {}

        for item in acc_dict.items():
            i = order.index(item[1]['accountname'])
            buffer_dict[i] = item[1]

        dump_dict = {}

        for x in range(len(buffer_dict)):
            dump_dict[x] = buffer_dict[x]

        with open('accounts.yml', 'w') as acc:
            yaml = YAML()
            yaml.dump(dump_dict, acc)
        refresh()

    def close():
        orderwindow.destroy()

    def ok():
        apply()
        close()

    button_up = ttk.Button(bottomframe_orderctrl,
                           text=_('Up'), command=up)
    button_up.pack(side='left', padx=2)

    button_down = ttk.Button(bottomframe_orderctrl,
                             text=_('Down'), command=down)
    button_down.pack(side='right', padx=2)

    button_ok = ttk.Button(bottomframe_windowctrl,
                           width=8, text=_('OK'), command=ok)
    button_ok.pack(side='left')
    button_cancel = ttk.Button(bottomframe_windowctrl,
                               width=8, text=_('Cancel'), command=close)
    button_cancel.pack(side='left', padx=3)

    button_apply = ttk.Button(bottomframe_windowctrl,
                              width=8, text=_('Apply'))

    def applybutton():
        nonlocal button_apply

        def enable():
            button_apply['state'] = 'normal'

        apply()
        button_apply['state'] = 'disabled'
        orderwindow.after(500, enable)

    button_apply['command'] = applybutton

    button_apply.pack(side='left')


def settingswindow():
    '''Open settings window'''
    global config_dict
    settingswindow = tk.Toplevel(main)
    settingswindow.title(_("Settings"))
    settingswindow.geometry("260x240+650+300")
    settingswindow.resizable(False, False)
    bottomframe_set = tk.Frame(settingswindow)
    bottomframe_set.pack(side='bottom')
    settingswindow.grab_set()
    settingswindow.focus()
    print('Opened settings window.')

    localeframe = tk.Frame(settingswindow)
    localeframe.pack(side='top', padx=10, pady=14)
    locale_label = tk.Label(localeframe, text=_('Language'))
    locale_label.pack(side='left', padx=3)
    locale_cb = ttk.Combobox(localeframe,
                             state="readonly",
                             values=['English',  # 0
                                     '한국어 (Korean)'])  # 1
    if config_dict['locale'] == 'en_US':
        locale_cb.current(0)
    elif config_dict['locale'] == 'ko_KR':
        locale_cb.current(1)

    locale_cb.pack(side='left', padx=3)

    restart_frame = tk.Frame(settingswindow)
    restart_frame.pack(side='top')

    restart_label = tk.Label(restart_frame,
                             text=_('Restart app to apply language settings.'))
    restart_label.pack()

    showpnames_frame = tk.Frame(settingswindow)
    showpnames_frame.pack(fill='x', side='top', padx=10, pady=19)

    showpnames_label = tk.Label(showpnames_frame, text=_('Show profile names'))
    showpnames_label.pack(side='left', padx=3)
    showpnames_cb = ttk.Combobox(showpnames_frame,
                                 state="readonly",
                                 values=[_('Use bar - |'),  # 0
                                         _('Use brackets - ( )'),  # 1
                                         _('Off')])  # 1
    if config_dict['show_profilename'] == 'bar':
        showpnames_cb.current(0)
    elif config_dict['show_profilename'] == 'bracket':
        showpnames_cb.current(1)
    elif config_dict['show_profilename'] == 'false':
        showpnames_cb.current(2)

    showpnames_cb.pack(side='left', padx=3)

    softshutdwn_frame = tk.Frame(settingswindow)
    softshutdwn_frame.pack(fill='x', side='top', padx=12, pady=1)

    soft_chkb = ttk.Checkbutton(softshutdwn_frame,
                                text=_('Try to soft shutdown Steam client'))

    soft_chkb.state(['!alternate'])

    if config_dict['try_soft_shutdown'] == 'true':
        soft_chkb.state(['selected'])
    else:
        soft_chkb.state(['!selected'])

    soft_chkb.pack(side='left')

    autoexit_frame = tk.Frame(settingswindow)
    autoexit_frame.pack(fill='x', side='top', padx=12, pady=18)

    autoexit_chkb = ttk.Checkbutton(autoexit_frame,
                                    text=_('Exit app upon Steam restart'))

    autoexit_chkb.state(['!alternate'])
    if config_dict['autoexit'] == 'true':
        autoexit_chkb.state(['selected'])
    else:
        autoexit_chkb.state(['!selected'])

    autoexit_chkb.pack(side='left')

    def close():
        settingswindow.destroy()

    def apply():
        global config_dict
        '''Write new config values to config.txt'''
        with open('config.yml', 'w') as cfg:
            locale = ('en_US', 'ko_KR')
            show_pname = ('bar', 'bracket', 'false')

            if 'selected' in soft_chkb.state():
                soft_shutdown = 'true'
            else:
                soft_shutdown = 'false'

            if 'selected' in autoexit_chkb.state():
                autoexit = 'true'
            else:
                autoexit = 'false'

            config_dict = {'locale': locale[locale_cb.current()],
                           'try_soft_shutdown': soft_shutdown,
                           'show_profilename': show_pname[showpnames_cb.current()],  # NOQA
                           'autoexit': autoexit}

            yaml = YAML()
            yaml.dump(config_dict, cfg)

        refresh()

    def ok():
        apply()
        close()

    settings_ok = ttk.Button(bottomframe_set,
                             text=_('OK'),
                             command=ok,
                             width=10)

    settings_cancel = ttk.Button(bottomframe_set,
                                 text=_('Cancel'),
                                 command=close,
                                 width=10)

    settings_apply = ttk.Button(bottomframe_set,
                                text=_('Apply'),
                                command=apply,
                                width=10)

    settings_ok.pack(side='left', padx=3, pady=3)
    settings_cancel.pack(side='left', padx=3, pady=3)
    settings_apply.pack(side='left', padx=3, pady=3)


def exit_after_restart():
    '''Restart Steam client and exit application.
    If autoexit is disabled, app won't exit.'''
    try:
        if config_dict['try_soft_shutdown'] == 'false':
            raise FileNotFoundError
        if check_running('Steam.exe'):
            print('Soft shutdown mode')
            r_path = fetch_reg('steamexe')
            r_path_items = r_path.split('/')
            path_items = []
            for item in r_path_items:
                if ' ' in item:
                    path_items.append(f'"{item}"')
                else:
                    path_items.append(item)
            steam_exe = "\\".join(path_items)
            print('Steam.exe path:', steam_exe)
            subprocess.run(f"start {steam_exe} -shutdown", shell=True,
                           creationflags=0x08000000, check=True)
            print('Shutdown command sent. Waiting for Steam...')
            sleep(2)
            for x in range(8):
                if check_running('Steam.exe'):
                    print('Steam is still running after %s seconds' % str(2+x*2))  # NOQA
                    if x < 8:
                        sleep(1.5)
                        continue
                    else:
                        msg = msgbox.askyesno(_('Alert'),
                                            _('After soft shutdown attempt,') + '\n' +  # NOQA
                                            _('Steam appears to be still running.') + '\n\n' +   # NOQA
                                            _('Do you want to force shutdown Steam?'))  # NOQA
                        if msg:
                            raise FileNotFoundError
                        else:
                            error_msg(_('Error'),
                                      _('Could not soft shutdown Steam.')
                                      + '\n' + _('App will now exit.'))
                else:
                    break
        else:
            print('Steam is not running.')
    except (FileNotFoundError, subprocess.CalledProcessError):
        print('Hard shutdown mode')
        try:
            subprocess.run("TASKKILL /F /IM Steam.exe",
                           creationflags=0x08000000, check=True)
            print('TASKKILL command sent.')
            sleep(1)
        except subprocess.CalledProcessError:
            pass
    try:
        print('Launching Steam...')
        subprocess.run("start steam://open/main",
                       shell=True, check=True)
    except subprocess.CalledProcessError:
        msgbox.showerror(_('Error'),
                         _('Could not start Steam automatically')
                         + '\n' + _('for unknown reason.'))
    if config_dict['autoexit'] == 'true':
        main.quit()


def window_height():
    global accounts
    '''Return window height according to number of accounts'''
    if accounts:
        to_multiply = len(accounts) - 1
    else:
        to_multiply = 0
    height_int = 160 + 31 * to_multiply
    height = str(height_int)
    return height


main = tk.Tk()
main.title(_("Account Switcher"))

main.geometry("300x%s+600+250" %
              window_height())
main.resizable(False, False)

sel_style = ttk.Style(main)
sel_style.configure('sel.TButton', background="#000")

def_style = ttk.Style(main)
def_style.configure(('TButton'))

menubar = tk.Menu(main)
menu = tk.Menu(menubar, tearoff=0)
menu.add_command(label=_('Import accounts from Steam'),
                 command=importwindow)
menu.add_command(label=_("Add accounts"),
                 command=addwindow)
menu.add_command(label=_("Remove accounts"),
                 command=removewindow)
menu.add_command(label=_("Change account order"),
                 command=orderwindow)
menu.add_separator()
menu.add_command(label=_("Settings"),
                 command=settingswindow)
menu.add_command(label=_("About"),
                 command=about)

menubar.add_cascade(label=_("Menu"), menu=menu)

upper_frame = tk.Frame(main)
button_frame = tk.Frame(main)

bottomframe = tk.Frame(main)
bottomframe.pack(side='bottom')

button_toggle = ttk.Button(bottomframe,
                           width=15,
                           text=_('Toggle auto-login'),
                           command=toggleAutologin)

button_quit = ttk.Button(bottomframe,
                         width=5,
                         text=_('Exit'),
                         command=main.quit)

restartbutton_text = tk.StringVar()

if config_dict['autoexit'] == 'true':
    restartbutton_text.set(_('Restart Steam & Exit'))
else:
    restartbutton_text.set(_('Restart Steam'))

button_restart = ttk.Button(bottomframe,
                            width=20,
                            textvariable=restartbutton_text,
                            command=exit_after_restart)

button_toggle.pack(side='left', padx=3, pady=3)
button_quit.pack(side='left', pady=3)
button_restart.pack(side='right', padx=3, pady=3)

nouser_label = tk.Label(main, text=_('No accounts added'))


def draw_button():
    '''Draw account switch buttons on main window.'''
    global accounts
    global upper_frame
    global button_frame
    global nouser_label

    button_dict = {}

    upper_frame.destroy()
    nouser_label.destroy()
    button_frame.destroy()

    upper_frame = tk.Frame(main)
    upper_frame.pack(side='top', fill='x')

    button_frame = tk.Frame(main)
    button_frame.pack(side='top', fill='x')

    nouser_label = tk.Label(main, text=_('No accounts added'))

    userlabel_1 = tk.Label(upper_frame, text=_('Current Auto-login user:'))
    userlabel_1.pack(side='top')

    user_var = tk.StringVar()
    user_var.set(fetch_reg('username'))

    userlabel_2 = tk.Label(upper_frame, textvariable=user_var)
    userlabel_2.pack(side='top', pady=2)

    auto_var = tk.StringVar()
    auto_var.set(autologinstr())

    autolabel = tk.Label(upper_frame, textvariable=auto_var)
    autolabel.pack(side='top')

    def button_func(username):
        current_user = fetch_reg('username')
        try:
            button_dict[current_user].config(style='TButton', state='normal')
        except KeyError:
            pass
        setkey('AutoLoginUser', username, winreg.REG_SZ)
        button_dict[username].config(style='sel.TButton', state='disabled')
        user_var.set(fetch_reg('username'))

    if not accounts:
        nouser_label.pack(anchor='center', expand=True)
    elif accounts:
        for username in accounts:
            if config_dict['show_profilename'] != 'false':
                if loginusers():
                    AccountName, PersonaName = loginusers()
                else:
                    AccountName, PersonaName = [], []

                if username in AccountName:
                    try:
                        i = AccountName.index(username)
                        profilename = PersonaName[i]
                        n = 37 - len(username)
                    except ValueError:
                        profilename = ''
                else:
                    profilename = ''

                if profilename and n > 4:
                    if config_dict['show_profilename'] == 'bar':
                        if profilename == profilename[:n]:
                            profilename = ' | ' + profilename[:n] + ''
                        else:
                            profilename = ' | ' + profilename[:n] + '..'
                    elif config_dict['show_profilename'] == 'bracket':
                        if profilename == profilename[:n]:
                            profilename = ' (' + profilename[:n] + ')'
                        else:
                            profilename = ' (' + profilename[:n] + '..)'
            else:
                profilename = ''

            if username == fetch_reg('username'):
                button_dict[username] = ttk.Button(button_frame,
                                                   style='sel.TButton',
                                                   text=username + profilename,
                                                   state='disabled',
                                                   command=lambda name=username: button_func(name))  # NOQA
            else:
                button_dict[username] = ttk.Button(button_frame,
                                                   style='TButton',
                                                   text=username + profilename,
                                                   state='normal',
                                                   command=lambda name=username: button_func(name))  # NOQA
            button_dict[username].pack(fill='x', padx=5, pady=3)


def refresh():
    '''Refresh main window widgets'''
    global upper_frame
    global button_frame
    global accounts
    fetchuser()
    upper_frame.destroy()
    button_frame.destroy()
    main.geometry("300x%s" %
                  window_height())
    draw_button()
    if config_dict['autoexit'] == 'true':
        restartbutton_text.set(_('Restart Steam & Exit'))
    else:
        restartbutton_text.set(_('Restart Steam'))
    print('Menu refreshed with %s account(s)' % len(accounts))


print('Init complete. Main app starting.')
draw_button()
main.config(menu=menubar)
main.after(100, start_checkupdate)

if os.path.isfile(os.path.join(os.getcwd(), 'update.zip')):
    main.after(150, afterupdate)
if not accounts:
    main.after(200, importwindow)

main.mainloop()
