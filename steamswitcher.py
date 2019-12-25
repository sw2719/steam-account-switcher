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
import threading
import queue as q
import zipfile as zf
import shutil
from packaging import version
from time import sleep
from ruamel.yaml import YAML
from modules.loginusers import loginusers
from modules.reg import fetch_reg, setkey
from modules.account import acc_getlist, acc_getdict

system_locale = locale.getdefaultlocale()[0]

print('App Start')

BRANCH = 'master'

__VERSION__ = '1.8'

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


def start_checkupdate(debug=False):
    '''Check if application has update'''
    update_frame = tk.Frame(main)
    update_frame.pack(side='bottom')

    if not BUNDLE and not debug:
        return

    checking_label = tk.Label(update_frame, text=_('Checking for updates...'))
    checking_label.pack()
    main.update()

    def update(sv_version, changelog):
        nonlocal debug

        updatewindow = tk.Toplevel(main)
        updatewindow.title(_('Update'))
        updatewindow.geometry("400x300+650+300")
        updatewindow.resizable(False, False)

        button_frame = tk.Frame(updatewindow)
        button_frame.pack(side=tk.BOTTOM, pady=3, fill='x')

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

        updatewindow.grab_set()

        def start_update():
            nonlocal button_frame
            nonlocal cancel_button
            nonlocal update_button
            nonlocal debug

            main.withdraw()
            try:
                os.remove('update.zip')
            except OSError:
                pass

            install = True

            if not BUNDLE and debug:
                if not msgbox.askyesno('', 'Install update?'): # NOQA
                    install = False

            cancel_button.destroy()
            update_button.destroy()

            dl_p = tk.IntVar()
            dl_p.set(0)
            dl_pbar = ttk.Progressbar(button_frame,
                                      length=150,
                                      orient=tk.HORIZONTAL,
                                      variable=dl_p)
            dl_pbar.pack(side='left', padx=5)

            dl_prog_var = tk.StringVar()
            dl_prog_var.set('-------- / --------')
            dl_prog = tk.Label(button_frame, textvariable=dl_prog_var)

            dl_speed_var = tk.StringVar()
            dl_speed_var.set('---------')
            dl_speed = tk.Label(button_frame, textvariable=dl_speed_var)

            dl_prog.pack(side='right', padx=5)
            dl_speed.pack(side='right', padx=5)
            main.update()

            download_q = q.Queue()
            dl_url = f'https://github.com/sw2719/steam-account-switcher/releases/download/v{sv_version}/Steam_Account_Switcher_v{sv_version}.zip'  # NOQA

            def download(URL):
                nonlocal download_q
                try:
                    r = req.get(URL, stream=True)
                    total_size = int(r.headers.get('content-length'))
                    total_in_MB = round(total_size / 1048576, 1)
                except req.RequestException:
                    msgbox.showerror(_('Error'),
                                     _('Error occured while downloading update.'))  # NOQA

                if round(total_in_MB, 1).is_integer():
                    total_in_MB = int(total_in_MB)

                def save():
                    nonlocal r
                    with open('update.zip', 'wb') as f:
                        shutil.copyfileobj(r.raw, f)

                dl_thread = threading.Thread(target=save)  # NOQA
                dl_thread.start()

                last_size = 0

                while True:
                    try:
                        current_size = os.path.getsize('update.zip')
                        current_in_MB = round(current_size / 1048576, 1)

                        if round(current_in_MB, 1).is_integer():
                            current_in_MB = int(current_in_MB)

                        size_delta = current_size - last_size
                        bps = size_delta * 2

                        if bps >= 1048576:
                            dl_spd = bps / 1048576
                            if round(dl_spd, 1).is_integer():
                                dl_spd = int(dl_spd)
                            else:
                                dl_spd = round(dl_spd, 1)
                            dl_spd_str = f'{dl_spd}MB/s'
                        elif bps >= 1024:
                            dl_spd = bps / 1024
                            if round(dl_spd, 1).is_integer():
                                dl_spd = int(dl_spd)
                            else:
                                dl_spd = round(dl_spd, 1)
                            dl_spd_str = f'{dl_spd}KB/s'
                        else:
                            dl_spd = bps
                            dl_spd_str = f'{dl_spd}B/s'

                        perc = int(current_size / total_size * 100)

                        prog = f'{current_in_MB}MB / {total_in_MB}MB'

                        download_q.put((perc, prog, dl_spd_str))
                        if perc == 100:
                            break
                        else:
                            last_size = current_size
                            sleep(0.5)
                    except OSError:
                        sleep(0.5)
                        continue

            def update_pbar():
                nonlocal download_q
                nonlocal dl_p
                nonlocal dl_speed_var
                nonlocal dl_prog_var
                while True:
                    try:
                        q_tuple = download_q.get_nowait()
                        p = q_tuple[0]
                        dl_p.set(p)
                        dl_prog = q_tuple[1]
                        dl_prog_var.set(dl_prog)
                        dl_spd = q_tuple[2]
                        dl_speed_var.set(dl_spd)
                        main.update()
                        if p == 100:
                            return
                    except q.Empty:
                        main.update()

            dl_thread = threading.Thread(target=lambda url=dl_url: download(url))  # NOQA
            dl_thread.start()

            update_pbar()
            if install:
                try:
                    archive = os.path.join(os.getcwd(), 'update.zip')

                    f = zf.ZipFile(archive, mode='r')
                    f.extractall(members=(member for member in f.namelist() if 'updater' in member)) # NOQA

                    subprocess.run('start updater/updater.exe', shell=True)
                    sys.exit(0)
                except (FileNotFoundError, zf.BadZipfile, OSError):
                    error_msg(_('Error'), _("Couldn't perform automatic update.") + '\n' + # NOQA
                            _('Update manually by extracting update.zip file.'))  # NOQA

        update_button['command'] = start_update
        cancel_button.pack(side='left', padx=(110, 0))
        update_button.pack(side='right', padx=(0, 110))

        def cancel():
            if msgbox.askokcancel(_('Cancel'), _('Are you sure to cancel?')):
                sys.exit(0)

        updatewindow.protocol("WM_DELETE_WINDOW", cancel)

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
            except (KeyError, TypeError):
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

        except (req.RequestException, req.ConnectionError,
                req.Timeout, req.ConnectTimeout):
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
        nonlocal debug
        try:
            v = queue.get_nowait()
            update_code = v[0]
            sv_version = v[1]
            changelog = v[2]
            checking_label.destroy()

            if debug:
                print('Update debug mode')
                update_label = tk.Label(update_frame,
                                        text=f'sv: {sv_version} cl: {str(__VERSION__)} output: {update_code}')  # NOQA
                update_label.pack(side='left', padx=5)

                update_button = ttk.Button(update_frame,
                                            text='Open UI',
                                            width=10,
                                            command=lambda: update(sv_version=sv_version, changelog=changelog))  # NOQA
                update_button.pack(side='right', padx=5)
                return

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

if not os.path.isfile('accounts.yml'):
    acc = open('accounts.yml', 'w')
    acc.close()


def toggleAutologin():
    '''Toggle autologin registry value between 0 and 1'''
    if fetch_reg('autologin') == 1:
        value = 0
    elif fetch_reg('autologin') == 0:
        value = 1
    setkey('RememberPassword', value, winreg.REG_DWORD)
    main.refresh()


def about():
    '''Open about window'''
    aboutwindow = tk.Toplevel(main)
    aboutwindow.title(_('About'))
    aboutwindow.geometry("360x250+650+300")
    aboutwindow.resizable(False, False)
    about_row = tk.Label(aboutwindow, text=_('Made by sw2719 (Myeuaa)'))
    about_steam = tk.Label(aboutwindow,
                           text='Steam: https://steamcommunity.com/' +
                           'id/muangmuang')
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
        '''Write accounts from user's input to accounts.yml
        :param userinput: Account names to add
        '''
        accounts = acc_getlist()
        acc_dict = acc_getdict()
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
            main.refresh()
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
    accounts = acc_getlist()
    acc_dict = acc_getdict()

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
        for key, value in check_dict.items():
            if value.get() == 1:
                acc_dict[len(acc_dict)] = {'accountname': key}
        with open('accounts.yml', 'w') as acc:
            yaml = YAML()
            yaml.dump(acc_dict, acc)
        main.refresh()
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


class removewindow(tk.Toplevel):
    '''Open remove accounts window'''
    def __init__(self, master, **kw):
        self.accounts = acc_getlist()
        if not self.accounts:
            msgbox.showinfo(_('No Accounts'),
                            _("There's no account to remove."))
            return
        tk.Toplevel.__init__(self, master, kw)
        self.title(_("Remove"))
        self.geometry("230x320+650+300")
        self.resizable(False, False)
        self.grab_set()
        self.focus()

        bottomframe_rm = tk.Frame(self)
        bottomframe_rm.pack(side='bottom')

        self.removelabel = tk.Label(self, text=_('Select accounts to remove.'))
        self.removelabel.pack(side='top',
                              padx=5,
                              pady=5)

        def _on_mousewheel(event):
            '''Scroll window on mousewheel input'''
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.canvas.bind("<MouseWheel>", _on_mousewheel)
        scroll_bar = ttk.Scrollbar(self,
                                   orient="vertical",
                                   command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll_bar.set)

        check_frame = tk.Frame(self.canvas)
        check_frame.bind("<Configure>", lambda event,
                         canvas=self.canvas: self.onFrameConfigure())

        scroll_bar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((4, 4), window=check_frame, anchor="nw")

        self.check_dict = {}

        for v in self.accounts:
            tk_var = tk.IntVar()
            checkbutton = ttk.Checkbutton(check_frame,
                                          text=v,
                                          variable=tk_var)
            checkbutton.bind("<MouseWheel>", _on_mousewheel)
            checkbutton.pack(side='top', padx=2, anchor='w')
            self.check_dict[v] = tk_var

        remove_cancel = ttk.Button(bottomframe_rm,
                                   text=_('Cancel'),
                                   command=self.close,
                                   width=9)
        remove_ok = ttk.Button(bottomframe_rm,
                               text=_('Remove'),
                               command=self.removeuser,
                               width=9)

        remove_cancel.pack(side='left', padx=5, pady=3)
        remove_ok.pack(side='left', padx=5, pady=3)
        print('Opened remove window.')

    def close(self):
        self.destroy()

    def removeuser(self):
        '''Write accounts to accounts.txt except the
        ones user wants to delete'''
        print('Remove function start')
        to_remove = []
        for v in self.accounts:
            if self.check_dict.get(v).get() == 1:
                to_remove.append(v)
                print('%s is to be removed.' % v)
            else:
                continue

        dump_dict = {}

        print('Removing selected accounts...')
        with open('accounts.yml', 'w') as acc:
            for username in self.accounts:
                if username not in to_remove:
                    dump_dict[len(dump_dict)] = {'accountname': username}
            yaml = YAML()
            yaml.dump(dump_dict, acc)
        main.refresh()
        self.close()

    def onFrameConfigure(self):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


def orderwindow():
    '''Open order change window'''
    accounts = acc_getlist()
    acc_dict = acc_getdict()

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
        main.refresh()

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

        main.refresh()

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
    '''Return window height according to number of accounts'''
    accounts = acc_getlist()
    if accounts:
        to_multiply = len(accounts) - 1
    else:
        to_multiply = 0
    height_int = 160 + 31 * to_multiply
    height = str(height_int)
    return height


class main(tk.Tk):
    '''Draw main window.'''

    def __init__(self):
        self.accounts = acc_getlist()
        self.acc_dict = acc_getdict()
        tk.Tk.__init__(self)
        self.title(_("Account Switcher"))

        self.geometry("300x%s+600+250" %
                      window_height())
        self.resizable(False, False)

        sel_style = ttk.Style(self)
        sel_style.configure('sel.TButton', background="#000")

        def_style = ttk.Style(self)
        def_style.configure('TButton')

        menubar = tk.Menu(self)
        menu = tk.Menu(menubar, tearoff=0)
        menu.add_command(label=_('Import accounts from Steam'),
                         command=importwindow)
        menu.add_command(label=_("Add accounts"),
                         command=addwindow)
        menu.add_command(label=_("Remove accounts"),
                         command=lambda: removewindow(self))
        menu.add_command(label=_("Change account order"),
                         command=orderwindow)
        menu.add_separator()
        menu.add_command(label=_("Settings"),
                         command=settingswindow)
        menu.add_command(label=_("About"),
                         command=about)

        menubar.add_cascade(label=_("Menu"), menu=menu)
        self.config(menu=menubar)

        if not BUNDLE:
            debug_menu = tk.Menu(menubar, tearoff=0)
            debug_menu.add_command(label='Update Debug',
                                command=lambda: self.after(
                                    10, lambda: start_checkupdate(debug=True)))  # NOQA
            menubar.add_cascade(label=_("Debug"), menu=debug_menu)

        bottomframe = tk.Frame(self)
        bottomframe.pack(side='bottom')

        button_toggle = ttk.Button(bottomframe,
                                   width=15,
                                   text=_('Toggle auto-login'),
                                   command=toggleAutologin)

        button_quit = ttk.Button(bottomframe,
                                 width=5,
                                 text=_('Exit'),
                                 command=self.quit)

        self.restartbutton_text = tk.StringVar()

        if config_dict['autoexit'] == 'true':
            self.restartbutton_text.set(_('Restart Steam & Exit'))
        else:
            self.restartbutton_text.set(_('Restart Steam'))

        button_restart = ttk.Button(bottomframe,
                                    width=20,
                                    textvariable=self.restartbutton_text,
                                    command=exit_after_restart)

        button_toggle.pack(side='left', padx=3, pady=3)
        button_quit.pack(side='left', pady=3)
        button_restart.pack(side='right', padx=3, pady=3)

        self.button_dict = {}
        self.frame_dict = {}

        upper_frame = tk.Frame(self)
        upper_frame.pack(side='top', fill='x')

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(side='top', fill='x')

        userlabel_1 = tk.Label(upper_frame, text=_('Current Auto-login user:'))
        userlabel_1.pack(side='top')

        self.user_var = tk.StringVar()
        self.user_var.set(fetch_reg('username'))

        userlabel_2 = tk.Label(upper_frame, textvariable=self.user_var)
        userlabel_2.pack(side='top', pady=2)

        self.auto_var = tk.StringVar()
        self.auto_var.set(autologinstr())

        autolabel = tk.Label(upper_frame, textvariable=self.auto_var)
        autolabel.pack(side='top')

    def configwindow(self, username, profilename):
        configwindow = tk.Toplevel(main)
        configwindow.title('')
        configwindow.geometry("270x140+650+300")
        configwindow.resizable(False, False)

        i = self.accounts.index(username)
        try:
            custom_name = self.acc_dict[i]['customname']
        except KeyError:
            custom_name = ''

        button_frame = tk.Frame(configwindow)
        button_frame.pack(side='bottom', pady=3)

        ok_button = ttk.Button(button_frame, text=_('OK'))
        ok_button.pack(side='right', padx=1.5)

        cancel_button = ttk.Button(button_frame,
                                   text=_('Cancel'),
                                   command=configwindow.destroy)
        cancel_button.pack(side='left', padx=1.5)

        label_frame = tk.Frame(configwindow)
        label_frame.pack(side='top', pady=4)

        label_1 = tk.Label(label_frame, text=_('Set a custom name to display for %s.') % username)  # NOQA
        label_1.pack()
        label_2 = tk.Label(label_frame, text=_('Set it blank to display its profile name.'))  # NOQA
        label_2.pack(pady=(4, 0))

        entry_frame = tk.Frame(configwindow)
        entry_frame.pack(side='bottom', pady=(10, 1))

        name_entry = ttk.Entry(entry_frame, width=26)
        name_entry.insert(0, custom_name)
        name_entry.pack()
        exp_label = tk.Label(entry_frame,
                             text=_('This is an experimental feature.'))
        exp_label.pack()

        configwindow.grab_set()
        configwindow.focus()
        name_entry.focus()

        def ok(username):
            if name_entry.get().strip():
                v = name_entry.get()
                self.acc_dict[i]['customname'] = v
                print(f"Using custom name '{v}' for '{username}'.")
            else:
                self.acc_dict[i].pop('customname', None)
                print(f"Custom name for '{username}' has been removed.")

            with open('accounts.yml', 'w', encoding='utf-8') as f:
                yaml.dump(self.acc_dict, f)
            self.refresh()
            configwindow.destroy()

        def enterkey(event):
            ok(username)

        configwindow.bind('<Return>', enterkey)
        ok_button['command'] = lambda username=username: ok(username)

    def button_func(self, username):
        current_user = fetch_reg('username')
        try:
            self.button_dict[current_user].config(style='TButton', state='normal')  # NOQA
        except KeyError:
            pass
        setkey('AutoLoginUser', username, winreg.REG_SZ)
        self.button_dict[username].config(style='sel.TButton', state='disabled')  # NOQA
        self.user_var.set(fetch_reg('username'))

    def draw_button(self):
        if self.accounts:
            for username in self.accounts:
                if config_dict['show_profilename'] != 'false':
                    if loginusers():
                        AccountName, PersonaName = loginusers()
                    else:
                        AccountName, PersonaName = [], []

                    try:
                        acc_index = self.accounts.index(username)
                        profilename = self.acc_dict[acc_index]['customname']
                    except KeyError:
                        if username in AccountName:
                            try:
                                i = AccountName.index(username)
                                profilename = PersonaName[i]
                                n = 37 - len(username)
                            except ValueError:
                                profilename = ''
                        else:
                            profilename = ''

                    n = 37 - len(username)

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

                self.frame_dict[username] = tk.Frame(self.button_frame)
                self.frame_dict[username].pack(fill='x', padx=5, pady=3)

                config_button = ttk.Button(self.frame_dict[username],
                                        text='⚙',
                                        width=2.6,
                                        command=lambda name=username, pname=profilename: self.configwindow(name, pname))  # NOQA
                config_button.pack(side='right')

                if username == fetch_reg('username'):
                    self.button_dict[username] = ttk.Button(self.frame_dict[username],
                                                    style='sel.TButton',
                                                    text=username + profilename,
                                                    state='disabled',
                                                    command=lambda name=username: self.button_func(name))  # NOQA
                else:
                    self.button_dict[username] = ttk.Button(self.frame_dict[username],
                                                    style='TButton',
                                                    text=username + profilename,
                                                    state='normal',
                                                    command=lambda name=username: self.button_func(name))  # NOQA
                self.button_dict[username].pack(fill='x', padx=(0, 1))

    def refresh(self):
        '''Refresh main window widgets'''
        self.accounts = acc_getlist()
        self.geometry("300x%s" %
                      window_height())
        self.button_frame.destroy()
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(side='top', fill='x')

        self.user_var.set(fetch_reg('username'))
        self.auto_var.set(autologinstr())
        self.draw_button()
        if config_dict['autoexit'] == 'true':
            self.restartbutton_text.set(_('Restart Steam & Exit'))
        else:
            self.restartbutton_text.set(_('Restart Steam'))
        print('Menu refreshed with %s account(s)' % len(self.accounts))


print('Init complete. Main app starting.')
main = main()
main.draw_button()

if os.path.isfile(os.path.join(os.getcwd(), 'update.zip')):
    main.after(150, afterupdate)
if not acc_getlist():
    main.after(200, importwindow)

main.mainloop()
