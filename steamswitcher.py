import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
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
from packaging import version
from time import sleep

print('Program Start')

if getattr(sys, 'frozen', False):
    print('Running in a bundle')
    BUNDLE = True
else:
    print('Running in a Python interpreter')
    BUNDLE = False

__VERSION__ = '1.3'

locale_buf = locale.getdefaultlocale()
LOCALE = locale_buf[0]
print('System locale is', LOCALE)

t = gettext.translation('steamswitcher',
                        localedir='locale',
                        languages=[LOCALE],
                        fallback=True)
_ = t.gettext

print('Running on', os.getcwd())

BRANCH = 'update_1.5'
URL = ('https://raw.githubusercontent.com/sw2719/steam-account-switcher/%s/version.txt'  # NOQA
       % BRANCH)


HKCU = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)


def start_checkupdate():
    update_frame = tk.Frame(main)
    update_frame.pack(side='bottom')
    checking_label = tk.Label(update_frame, text='Checking for updates...')
    checking_label.pack()
    main.update()

    def update(sv_version):
        nonlocal update_frame
        update_frame.destroy()
        update_frame = tk.Frame(main)
        update_frame.pack(side='bottom')

        dl_url = f'https://github.com/sw2719/steam-account-switcher/releases/download/v{sv_version}/Steam_Account_Switcher_v{sv_version}.zip'  # NOQA
        try:
            update_text = tk.StringVar()
            update_text.set(_('Downloading update file...'))
            update_label = tk.Label(update_frame, textvariable=update_text)
            update_label.pack()
            main.update()
            response = req.get(dl_url)
        except req.exceptions.RequestException:
            return
        with open('update.zip', 'wb') as f:
            f.write(response.content)
        subprocess.run('start updater/updater.exe', shell=True)
        sys.exit(0)

    queue = q.Queue()

    def checkupdate():
        print('Update check start')
        update_code = None
        try:
            response = req.get(URL)
            text = response.text.splitlines()
            auto_updatable = text[-2]
            sv_version_str = text[-1]
            print('Server version is', sv_version_str)
            print('Client version is', __VERSION__)

            sv_version = version.parse(sv_version_str)
            cl_version = version.parse(__VERSION__)
            if auto_updatable == 'false':
                update_code = 2
            else:
                if sv_version > cl_version:
                    update_code = 1
                elif sv_version == cl_version:
                    update_code = 0
                elif sv_version < cl_version:
                    update_code = 3

        except req.exceptions.RequestException:
            update_code = 4
            sv_version_str = '0'
        queue.put((update_code, sv_version_str))

    update_code = None
    sv_version = None

    def get_output():
        nonlocal update_code
        nonlocal sv_version
        nonlocal checking_label
        try:
            v = queue.get_nowait()
            update_code = v[0]
            sv_version = v[1]
            checking_label.destroy()

            if not BUNDLE:
                update_label = tk.Label(update_frame,
                                        text=f'Using source file: sv {sv_version} / cl {__VERSION__}')  # NOQA
                update_label.pack(side='left', padx=5)
                update_button = ttk.Button(update_frame,
                                           text='Update',
                                           width=8,
                                           command=lambda: update(sv_version=sv_version))  # NOQA
                update_button.pack(side='right', padx=5)
            else:
                if update_code == 1:
                    print('Update Available')

                    update_label = tk.Label(update_frame,
                                            text=_('New version %s is available.')  # NOQA
                                            % sv_version)
                    update_label.pack(side='left', padx=5)

                    update_button = ttk.Button(update_frame,
                                               text=_('Update'),
                                               width=8,
                                               command=lambda: update(sv_version=sv_version))  # NOQA

                    update_button.pack(side='right', padx=5)
                if update_code == 2:
                    print('Update Available')

                    update_label = tk.Label(update_frame,
                                            text=_('Manual update %s is available.')  # NOQA
                                            % sv_version)
                    update_label.pack(side='left', padx=5)

                    def open_github():
                        os.startfile('https://github.com/sw2719/steam-account-switcher/releases')  # NOQA

                    update_button = ttk.Button(update_frame,
                                               text=_('Open GitHub'),
                                               width=12,
                                               command=open_github)

                    update_button.pack(side='right', padx=5)
                elif update_code == 0:
                    print('On latest version')

                    update_label = tk.Label(update_frame,
                                            text=_('Using the latest version'))
                    update_label.pack(side='bottom')
                elif update_code == 3:
                    print('Development version')

                    update_label = tk.Label(update_frame,
                                            text=_('Development version'))
                    update_label.pack(side='bottom')
                elif update_code == 4:
                    print('Exception while getting server version')

                    update_label = tk.Label(update_frame,
                                            text=_('Failed to check for updates'))  # NOQA
                    update_label.pack(side='bottom')
        except q.Empty:
            main.after(300, get_output)

    t = threading.Thread(target=checkupdate)
    t.start()
    main.after(300, get_output)


def check_running(process_name):
    for process in psutil.process_iter():
        try:
            if process_name.lower() in process.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied,
                psutil.ZombieProcess):
            pass
    return False


def error_msg(title, content):
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(title, content)
    root.destroy()
    sys.exit(1)


def fetch_reg(key):
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
    if os.path.isfile('steam_path.txt'):
        with open('steam_path.txt', 'r') as path:
            steam_path = path.read()

    if '/' in steam_path:
        steam_path = steam_path.replace('/', '\\')

    vdf_file = os.path.join(steam_path, 'config', 'loginusers.vdf')

    try:
        with open(vdf_file, 'r') as vdf_file:
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


try:
    with open('accounts.txt', 'r') as txt:
        namebuffer = txt.read().splitlines()

    accounts = [item for item in namebuffer if not item.strip() == '']

    if not accounts:
        raise FileNotFoundError
except FileNotFoundError:
    txt = open('accounts.txt', 'w')
    txt.close()
    accounts = []

print('Detected ' + str(len(accounts)) + ' accounts:')

if accounts:
    print('------------------')
    for username in accounts:
        print(username)
    print('------------------')


def fetchuser():
    global accounts
    txt = open('accounts.txt', 'r')
    namebuffer = txt.read().splitlines()
    txt.close()
    accounts = [item for item in namebuffer if not item.strip() == '']


def setkey(name, value, value_type):
    try:
        reg_key = winreg.OpenKey(HKCU, r"Software\Valve\Steam", 0,
                                 winreg.KEY_ALL_ACCESS)

        winreg.SetValueEx(reg_key, name, 0, value_type, value)
        winreg.CloseKey(reg_key)
        print("Changed %s's value to %s" % (name, str(value)))
    except OSError:
        error_msg(_('Registry Error'), _('Failed to change registry value.'))


def toggleAutologin():
    if fetch_reg('autologin') == 1:
        value = 0
    elif fetch_reg('autologin') == 0:
        value = 1
    setkey('RememberPassword', value, winreg.REG_DWORD)
    refresh()


def about():  # 정보 창
    aboutwindow = tk.Toplevel(main)
    aboutwindow.title(_('About'))
    aboutwindow.geometry("360x270+650+300")
    aboutwindow.resizable(False, False)
    about_row = tk.Label(aboutwindow, text=_('Made by sw2719 (Myeuaa)'))
    about_steam = tk.Label(aboutwindow,
                           text='Steam: https://steamcommunity.com/'
                           + 'id/muangmuang')
    about_email = tk.Label(aboutwindow, text='E-mail: sw2719@naver.com')
    if LOCALE == 'ko_KR':
        about_discord = tk.Label(aboutwindow, text='Discord: 꺔먕#6678')
    about_disclaimer = tk.Label(aboutwindow,
                                text=_('Warning: The developer of this program is not responsible for')  # NOQA
                                + '\n' + _('data loss or any other damage from the use of this program.'))  # NOQA
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
    if LOCALE == 'ko_KR':
        about_discord.pack()
    about_disclaimer.pack(pady=5)
    about_steam_trademark.pack()
    copyright_label.pack(pady=5)
    version.pack()
    button_exit.pack(side='bottom', pady=5)


def addwindow():  # 계정 추가 창
    global accounts

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
        if userinput.strip():
            try:
                with open('accounts.txt', 'r') as txt:
                    lastname = txt.readlines()[-1]
                    if '\n' not in lastname:
                        prefix = '\n'
                    else:
                        raise IndexError
            except IndexError:
                prefix = ''

            txt = open('accounts.txt', 'a')
            name_buffer = userinput.split("/")

            for name_to_write in name_buffer:
                if name_to_write.strip():
                    if name_to_write not in accounts:
                        print('Writing ' + name_to_write)
                        txt.write(prefix + name_to_write.strip() + '\n')
                        accounts.append(name_to_write.strip())
                    else:
                        print('Alert: Account %s already exists!'
                              % name_to_write)
                        messagebox.showinfo(_('Duplicate Alert'),
                                            _('Account %s already exists.')
                                            % name_to_write)

            txt.close()
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
    global accounts
    if loginusers():
        AccountName, PersonaName = loginusers()
    else:
        try_manually = messagebox.askyesno(_('Warning'), _('Could not load loginusers.vdf.')  # NOQA
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
                    try_again = messagebox.askyesno(_('Warning'),
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

    check_dict = {}

    for i, v in enumerate(AccountName):
        if v not in accounts:
            tk_var = tk.IntVar()
            checkbutton = ttk.Checkbutton(check_frame,
                                          text=v + f' ({PersonaName[i]})',
                                          variable=tk_var)

            checkbutton.pack(side='top', padx=2, anchor='w')
            check_dict[v] = tk_var

    def import_user():
        with open('accounts.txt', 'a') as txt:
            for key, value in check_dict.items():
                if value.get() == 1:
                    txt.write(key + '\n')
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
    global accounts
    if not accounts:
        messagebox.showinfo(_('No Accounts'),
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

    check_dict = {}

    for v in accounts:
        tk_var = tk.IntVar()
        checkbutton = ttk.Checkbutton(removewindow,
                                      text=v,
                                      variable=tk_var)

        checkbutton.pack(side='top', padx=2, anchor='w')
        check_dict[v] = tk_var

    def removeuser():
        print('Remove function start')
        to_remove = []
        for v in accounts:
            if check_dict.get(v).get() == 1:
                to_remove.append(v)
                print('%s is to be removed.' % v)
            else:
                continue

        print('Removing selected accounts...')
        with open('accounts.txt', 'w') as txt:
            for username in accounts:
                if username not in to_remove:
                    txt.write(username + '\n')
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


def exit_after_restart(graceful):
    try:
        if graceful is False:
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
            sleep(2.5)
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
        messagebox.showerror(_('Error'),
                             _('Could not start Steam automatically')
                             + '\n' + _('for unknown reason.'))
    main.quit()


def window_height(accounts):
    if accounts:
        to_multiply = len(accounts) - 1
    else:
        to_multiply = 0
    height_int = 160 + 31 * to_multiply
    height = str(height_int)
    return height


main = tk.Tk()
main.title(_("Account Switcher"))

main.geometry("300x%s+600+250" %  # 기본 창 높이 140 버튼 1개당 32 증가
              window_height(accounts))  # window_height 함수 참조
main.resizable(False, False)

sel_style = ttk.Style(main)
sel_style.configure('sel.TButton', background="#000")

def_style = ttk.Style(main)
def_style.configure(('TButton'))

menubar = tk.Menu(main)
account_menu = tk.Menu(menubar, tearoff=0)
account_menu.add_command(label=_('Import accounts from Steam'),
                         command=importwindow)
account_menu.add_command(label=_("Add accounts"), command=addwindow)
account_menu.add_command(label=_("Remove accounts"), command=removewindow)
account_menu.add_separator()
account_menu.add_command(label=_("About"), command=about)
menubar.add_cascade(label=_("Menu"), menu=account_menu)

upper_frame = tk.Frame(main)
upper_frame.pack(side='top', fill='x')

button_frame = tk.Frame(main)
button_frame.pack(side='top', fill='x')

bottomframe = tk.Frame(main)
bottomframe.pack(side='bottom')

button_toggle = ttk.Button(bottomframe,
                           width=14,
                           text=_('Toggle auto-login'),
                           command=toggleAutologin)

button_quit = ttk.Button(bottomframe,
                         width=5,
                         text=_('Exit'),
                         command=main.quit)

button_restart = ttk.Button(bottomframe,
                            width=18,
                            text=_('Restart Steam & exit'),
                            command=lambda: exit_after_restart(True))

button_toggle.pack(side='left', padx=4, pady=3)
button_quit.pack(side='left', padx=4, pady=3)
button_restart.pack(side='right', padx=4, pady=3)

nouser_label = tk.Label(main, text=_('No accounts added'))


def draw_button(accounts):
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
        button_dict[current_user].config(style='TButton', state='normal')
        setkey('AutoLoginUser', username, winreg.REG_SZ)
        button_dict[username].config(style='sel.TButton', state='disabled')
        user_var.set(fetch_reg('username'))

    if not accounts:
        nouser_label.pack(anchor='center', expand=True)
    elif accounts:
        for username in accounts:
            if username == fetch_reg('username'):
                button_dict[username] = ttk.Button(button_frame,
                                                   style='sel.TButton',
                                                   text=username,
                                                   state='disabled',
                                                   command=lambda name=username: button_func(name))  # NOQA
            else:
                button_dict[username] = ttk.Button(button_frame,
                                                   style='TButton',
                                                   text=username,
                                                   state='normal',
                                                   command=lambda name=username: button_func(name))  # NOQA
            button_dict[username].pack(fill='x', padx=5, pady=3)


def refresh():
    global upper_frame
    global button_frame
    global accounts
    fetchuser()
    upper_frame.destroy()
    button_frame.destroy()
    main.geometry("300x%s" %
                  window_height(accounts))
    draw_button(accounts)
    print('Menu refreshed with %s account(s)' % len(accounts))


print('Init complete. Main app starting.')
draw_button(accounts)
main.config(menu=menubar)
main.after(100, start_checkupdate)
if not accounts:
    main.after(150, importwindow)
main.mainloop()
