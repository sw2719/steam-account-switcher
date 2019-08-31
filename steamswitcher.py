import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import winreg
import sys
import os
import subprocess
import requests as req
import gettext
import locale
import psutil
from time import sleep


locale_buf = locale.getdefaultlocale()
locale_value = locale_buf[0]
if locale_value != 'ko_KR':
    locale_value = 'en_US'

t = gettext.translation('sw', localedir='locale',
                        languages=[locale_value])
_ = t.gettext

print('Running on ', os.getcwd())

VERSION = '1.3'
BRANCH = 'master'
URL = ('https://raw.githubusercontent.com/sw2719/steam-account-switcher/%s/version.txt'  # NOQA
       % BRANCH)


def checkupdate():
    update_avail = None
    try:
        response = req.get(URL)
        sv_version = response.text.splitlines()[-1]
        print(sv_version)

        if float(sv_version) > float(VERSION):
            update_avail = 1
        else:
            update_avail = 0
    except req.exceptions.RequestException:
        update_avail = 2
    return update_avail


def start_checkupdate():
    update_frame = tk.Frame(main)
    update_frame.pack(side='bottom')
    update_code = checkupdate()

    if update_code == 1:
        print('Update Available')

        update_label = tk.Label(update_frame, text=_('Update available'))
        update_label.pack(side='left', padx=5)

        def open_github():
            os.startfile('https://github.com/sw2719/steam-account-switcher/releases')  # NOQA

        update_button = ttk.Button(update_frame,
                                   text=_('Visit GitHub'),
                                   width=12,
                                   command=open_github)

        update_button.pack(side='right', padx=5)
    elif update_code == 0:
        print('On latest version')

        update_label = tk.Label(update_frame, text=_('Using the latest version'))
        update_label.pack(side='bottom')
    elif update_code == 2:
        print('Exception while getting server version')

        update_label = tk.Label(update_frame, text=_('Failed to check for updates'))
        update_label.pack(side='bottom')


def check_running(process_name):
    for process in psutil.process_iter():
        try:
            if process_name.lower() in process.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied,
                psutil.ZombieProcess):
            pass
    return False


HCU = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)


def error_msg(title, content):  # 오류 메시지 표시후 종료
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(title, content)
    root.destroy()
    sys.exit(1)


def fetch_reg(key):  # 레지스트리에서 값 확인
    if key == 'username':
        key_name = 'AutoLoginUser'
    elif key == 'autologin':
        key_name = 'RememberPassword'
    elif key == 'installpath':
        key_name = 'SteamExe'

    try:
        reg_key = winreg.OpenKey(HCU, r"Software\Valve\Steam")
        value_buffer = winreg.QueryValueEx(reg_key, key_name)
        value = value_buffer[0]
        winreg.CloseKey(reg_key)
    except OSError:
        error_msg(_('Failed to load registry'),
                  _('Failed to fetch registry value.') + '\n' +
                  _('Make sure that Steam is installed.'))
    return value


def autologinstr():  # autologin 함수 값을 불러와 문자열 출력
    value = fetch_reg('autologin')
    if value == 1:
        retstr = _('Auto-login Enabled')
    elif value == 0:
        retstr = _('Auto-login Disabled')
    return retstr


print('Fetching registry values...')  # 콘솔에 레지스트리 값 출력
if fetch_reg('autologin') != 2:
    print('Autologin value is ' + str(fetch_reg('autologin')))
else:
    print('Could not fetch autologin status!')
if fetch_reg('autologin'):
    print('Current autologin user is ' + str(fetch_reg('autologin')))
else:
    print('Could not fetch autologin user information!')


def setupwindow():
    removewindow = tk.Toplevel(main)
    removewindow.title(_("Welcome"))
    removewindow.geometry("250x320+650+300")
    removewindow.resizable(False, False)
    removewindow.grab_set()
    removewindow.focus()
    print('Opened remove window.')

    def close():
        removewindow.destroy()


try:
    with open('accounts.txt', 'r') as txt:
        namebuffer = txt.read().splitlines()

    accounts = [item for item in namebuffer if not item.strip() == '']

    if not accounts:
        raise FileNotFoundError
except FileNotFoundError:  # 계정 파일이 없거나 계정 정보가 없을 경우
    with open('accounts.txt', 'w') as txt:
        if fetch_reg('username'):
            print('No account found! Adding current user...')
            txt.write(fetch_reg('username') + '\n')
    accounts = [fetch_reg('username')]

print('Detected ' + str(len(accounts)) + ' accounts:')  # 콘솔에 계정 출력

if accounts:
    print('------------------')
    for username in accounts:
        print(username)
    print('------------------')

if len(accounts) > 12:  # 계정 갯수가 12개를 초과할 경우
    error_msg(_('Account limit exceeded'), _('You exceeded the maximum number of accounts.') + '\n' +
              _('You have %s accounts and limit is 12.') % len(accounts))


def fetchuser():  # 계정 파일 다시 불러오기
    global accounts
    txt = open('accounts.txt', 'r')
    namebuffer = txt.read().splitlines()
    txt.close()
    accounts = [item for item in namebuffer if not item.strip() == '']


def setkey(name, value, value_type):  # 레지스트리 값 변경 (이름, 값, 값 유형)
    try:
        reg_key = winreg.OpenKey(HCU, r"Software\Valve\Steam", 0,  # 키 열가
                                 winreg.KEY_ALL_ACCESS)
        # 값 지정 (키, 값 이름, 0, 값 종류, 값)
        winreg.SetValueEx(reg_key, name, 0, value_type, value)
        winreg.CloseKey(reg_key)  # 키 닫기
        print("Changed %s's value to %s" % (name, str(value)))  # 콘솔 출력
    except OSError:
        error_msg(_('Registry Error'), _('Failed to change registry value.'))


def toggleAutologin():  # 자동로그인 레지스트리 값 0 1 토글
    if fetch_reg('autologin') == 1:
        value = 0
    elif fetch_reg('autologin') == 0:
        value = 1
    setkey('RememberPassword', value, winreg.REG_DWORD)
    refresh()


def about():  # 정보 창
    aboutwindow = tk.Toplevel(main)
    aboutwindow.title(_('About'))
    aboutwindow.geometry("400x210+650+300")
    aboutwindow.resizable(False, False)
    about_row = tk.Label(aboutwindow, text=_('Made by Myeuaa (sw2719)'))
    about_steam = tk.Label(aboutwindow,
                           text='Steam: https://steamcommunity.com/'
                           + 'id/muangmuang')
    about_email = tk.Label(aboutwindow, text='E-mail: sw2719@naver.com')
    about_discord = tk.Label(aboutwindow, text='Discord: 꺔먕#6678')
    about_disclaimer = tk.Label(aboutwindow,
                                text=_('Warning: The developer of this program is not responsible for')
                                + '\n' + _('data loss or any other damage from the use of this program.'))  # NOQA

    def close():  # 창 닫기
        aboutwindow.destroy()

    button_exit = ttk.Button(aboutwindow,
                             text=_('Close'),
                             width=8,
                             command=close)
    about_row.pack(pady=15)
    about_steam.pack()
    about_email.pack()
    if locale_value == 'ko_KR':
        about_discord.pack()
    about_disclaimer.pack(pady=8)
    button_exit.pack(side='bottom', pady=5)


def addwindow():  # 계정 추가 창
    global accounts
    if len(accounts) == 12:
        messagebox.showwarning(_('Account limit reached'),
                               _('Maximum number of accounts reached.'))
        return

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
                             text=_("In case of adding multiple accounts,") + '\n' +
                             _("seperate each account with '/' (slash)."))

    account_entry = ttk.Entry(bottomframe_add, width=28)
    account_entry.pack(side='left', padx=5, pady=3)

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
                if len(accounts) < 12:  # 계정 갯수가 한도내인지 확인
                    if name_to_write.strip():  # 올바른 입력값인지 확인
                        if name_to_write not in accounts:  # 중복된 계정이 아닌지 확인
                            print('Writing ' + name_to_write)
                            txt.write(prefix + name_to_write.strip() + '\n')
                            accounts.append(name_to_write.strip())
                        else:
                            print('Alert: Account %s already exists!'
                                  % name_to_write)
                            messagebox.showinfo(_('Duplicate Error'),
                                                _('Account %s already exists.')
                                                % name_to_write)
                elif len(accounts) == 12:
                    messagebox.showwarning(_('계정 한도 도달'),
                                           _("Couldn't add %s because you've reached account limit.")
                                           % name_to_write)

            txt.close()
            refresh()
        addwindow.destroy()

    def close():
        addwindow.destroy()

    def enterkey(event):  # Enter 키 입력을 감지
        adduser(account_entry.get())

    addwindow.bind('<Return>', enterkey)
    button_add = ttk.Button(bottomframe_add, width=9, text=_('Add'),
                            command=lambda: adduser(account_entry.get()))
    button_addcancel = ttk.Button(addwindow, width=9,
                                  text=_('Cancel'), command=close)
    addlabel_row1.pack(pady=10)
    addlabel_row2.pack()

    account_entry.pack(side='left', padx=5, pady=3)
    button_add.pack(side='left', anchor='e', padx=5, pady=3)
    button_addcancel.pack(side='bottom', anchor='e', padx=5, pady=3)


def removewindow():
    global accounts
    if not accounts:
        messagebox.showinfo(_('No Accounts'), _("There's no account to remove."))
        return
    removewindow = tk.Toplevel(main)
    removewindow.title(_("Remove"))
    removewindow.geometry("250x320+650+300")
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

    check_dict = {}  # 딕셔너리 선언

    for v in accounts:
        tk_var = tk.IntVar()  # Tkinter 체크버튼 값 변수
        checkbutton = ttk.Checkbutton(removewindow,  # 체크버튼 만들기
                                      text=v,
                                      variable=tk_var)

        checkbutton.pack(side='top', padx=2, anchor='w')
        check_dict[v] = tk_var  # 딕셔너리에 체크버튼 변수 저장

    def removeuser():
        print('Remove function start')
        to_remove = []
        for v in accounts:
            if check_dict.get(v).get() == 1:  # 계정이 딕셔너리에 있는지 확인
                to_remove.append(v)  # 삭제할 계정 리스트에 추가
                print('%s is to be removed.' % v)
            else:
                continue

        print('Removing selected accounts...')
        with open('accounts.txt', 'w') as txt:
            for username in accounts:
                if username not in to_remove:  # 삭제할 계정이 아닌지 확인
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


def exit_after_restart(graceful):  # Steam을 재시작
    try:
        if graceful is False:
            raise FileNotFoundError
        if check_running('Steam.exe'):
            print('Soft shutdown mode')
            r_path = fetch_reg('installpath')
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
        subprocess.run("start steam://open/main",  # Steam 실행
                       shell=True, check=True)
    except subprocess.CalledProcessError:
        messagebox.showerror(_('Error'), _('Could not start Steam automatically') + '\n' +
                             _('for unknown reason.'))
    main.quit()


def window_height(accounts):  # 버튼의 갯수에 따라 창의 높이를 반환
    if accounts:
        to_multiply = len(accounts) - 1
    else:
        to_multiply = 0
    height_int = 160 + 32 * to_multiply
    height = str(height_int)
    return height


print('--PHASE 5: Drawing UI--')
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
account_menu = tk.Menu(menubar, tearoff=0)  # 상단 메뉴
account_menu.add_command(label=_("Add accounts"), command=addwindow)
account_menu.add_command(label=_("Remove accounts"), command=removewindow)
account_menu.add_separator()
account_menu.add_command(label=_("About"), command=about)
menubar.add_cascade(label=_("Menu"), menu=account_menu)

upper_frame = tk.Frame(main)
upper_frame.pack(side='top', fill='x')

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
    global nouser_label

    button_dict = {}

    upper_frame.destroy()
    nouser_label.destroy()

    upper_frame = tk.Frame(main)
    upper_frame.pack(side='top', fill='x')

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
                button_dict[username] = ttk.Button(upper_frame,
                                                   style='sel.TButton',
                                                   text=username,
                                                   state='disabled',
                                                   command=lambda name=username: button_func(name))  # NOQA
            else:
                button_dict[username] = ttk.Button(upper_frame,
                                                   style='TButton',
                                                   text=username,
                                                   state='normal',
                                                   command=lambda name=username: button_func(name))  # NOQA
            button_dict[username].pack(fill='x', padx=5, pady=3)


def refresh():
    global upper_frame
    global accounts
    fetchuser()
    upper_frame.destroy()
    main.geometry("300x%s" %
                  window_height(accounts))
    draw_button(accounts)
    print('Menu refreshed with %s account(s)' % len(accounts))


print('Init complete. Main app starting.')
draw_button(accounts)
main.config(menu=menubar)
main.after(100, start_checkupdate)
main.mainloop()
