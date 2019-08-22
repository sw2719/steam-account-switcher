import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import winreg
import sys
import os
import subprocess
import requests as req
from time import sleep

print('Running on ', os.getcwd())

VERSION = '1.2'
BRANCH = 'master'
URL = ('https://raw.githubusercontent.com/sw2719/steam-account-switcher/%s/version.txt'  # NOQA
       % BRANCH)

update_avail = False


def checkupdate():
    global update_avail
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

        update_label = tk.Label(update_frame, text='업데이트 사용 가능')
        update_label.pack(side='left', padx=5)

        def open_github():
            os.startfile('https://github.com/sw2719/steam-account-switcher/releases')  # NOQA

        update_button = ttk.Button(update_frame,
                                   text='GitHub 방문',
                                   width=12,
                                   command=open_github)

        update_button.pack(side='right', padx=5)
    elif update_code == 0:
        print('On latest version')

        update_label = tk.Label(update_frame, text='최신 버전 사용 중')
        update_label.pack(side='bottom')
    elif update_code == 2:
        print('Exception while getting server version')

        update_label = tk.Label(update_frame, text="업데이트 확인 실패")
        update_label.pack(side='bottom')


print('--PHASE 1: Import complete')
print('--PHASE 2: Getting registry values--')

HCU = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)


def error_msg(title, content):  # 오류 메시지 표시후 종료
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(title, content)
    root.destroy()
    sys.exit(1)


def getuser():  # 레지스트리에서 AutoLoginUser 값 확인
    try:
        reg_key = winreg.OpenKey(HCU, r"Software\Valve\Steam")
        value_buffer = winreg.QueryValueEx(reg_key, "AutoLoginUser")
        value = value_buffer[0]
        winreg.CloseKey(reg_key)
    except OSError:
        error_msg('레지스트리 불러오기 실패',
                  '레지스트리에서 계정 정보를 불러오는데 실패했습니다.\n' +
                  '스팀이 설치되어 있는지 확인하십시오.')
    return value


def autologin():  # 레지스트리에서 RememberPassword 값 확인
    try:
        reg_key = winreg.OpenKey(HCU, r"Software\Valve\Steam")
        value_buffer = winreg.QueryValueEx(reg_key, "RememberPassword")
        value = value_buffer[0]
        winreg.CloseKey(reg_key)
    except OSError:
        error_msg('레지스트리 불러오기 실패',
                  '레지스트리에서 설정 값을 불러오는데 실패했습니다.\n' +
                  '스팀이 설치되어 있는지 확인하십시오.')
    return value


def autologinstr():  # autologin 함수 값을 불러와 문자열 출력
    value = autologin()
    if value == 1:
        retstr = '자동로그인 활성화'
    elif value == 0:
        retstr = '자동로그인 비활성화'
    return retstr


print('Fetching registry values...')  # 콘솔에 레지스트리 값 출력
if autologin() != 2:
    print('Autologin value is ' + str(autologin()))
else:
    print('Could not fetch autologin status!')
if getuser():
    print('Current autologin user is ' + getuser())
else:
    print('Could not fetch autologin user information!')

print('--PHASE 3: Fetching accounts--')

try:
    with open('accounts.txt', 'r') as txt:
        namebuffer = txt.read().splitlines()

    accounts = [item for item in namebuffer if not item.strip() == '']

    if not accounts:
        raise FileNotFoundError
except FileNotFoundError:  # 계정 파일이 없거나 계정 정보가 없을 경우
    with open('accounts.txt', 'w') as txt:
        if getuser():
            print('No account found! Adding current user...')
            txt.write(getuser() + '\n')
    accounts = [getuser()]

print('Detected ' + str(len(accounts)) + ' accounts:')  # 콘솔에 계정 출력

if accounts:
    print('------------------')
    for username in accounts:
        print(username)
    print('------------------')

if len(accounts) > 12:  # 계정 갯수가 12개를 초과할 경우
    error_msg('계정 한도 초과', '계정 갯수가 한도를 초과했습니다.\n' +
              '현재 계정 수는 %s개 이고, 제한은 12개 입니다.' % len(accounts))

print('--PHASE 4: Defining functions--')


def setkey(name, value, value_type):  # 레지스트리 값 변경 (이름, 값, 값 유형)
    try:
        reg_key = winreg.OpenKey(HCU, r"Software\Valve\Steam", 0,  # 키 열가
                                 winreg.KEY_ALL_ACCESS)
        # 값 지정 (키, 값 이름, 0, 값 종류, 값)
        winreg.SetValueEx(reg_key, name, 0, value_type, value)
        winreg.CloseKey(reg_key)  # 키 닫기
        print("Changed %s's value to %s" % (name, str(value)))  # 콘솔 출력
    except OSError:
        error_msg('오류', '레지스트리 작업에 실패했습니다.')


def setuser(username):  # 버튼 지정용 함수
    setkey('AutoLoginUser', username, winreg.REG_SZ)
    refresh()


def fetchuser():  # 계정 파일 다시 불러오기
    global accounts
    txt = open('accounts.txt', 'r')
    namebuffer = txt.read().splitlines()
    txt.close()
    accounts = [item for item in namebuffer if not item.strip() == '']


def about():  # 정보 창
    aboutwindow = tk.Toplevel(main)
    aboutwindow.title("정보")
    aboutwindow.geometry("400x210+650+300")
    aboutwindow.resizable(False, False)
    about_row = tk.Label(aboutwindow, text='Made by 꺔먕 (Myeuaa)')
    about_steam = tk.Label(aboutwindow,
                           text='Steam: https://steamcommunity.com/'
                           + 'id/muangmuang')
    about_email = tk.Label(aboutwindow, text='E-mail: sw2719@naver.com')
    about_discord = tk.Label(aboutwindow, text='Discord: 꺔먕#6678')
    about_disclaimer = tk.Label(aboutwindow,
                                text='경고: 본 프로그램의 사용으로 인한 '
                                + '데이터 손실 및 기타 손해 등\n' +
                                '어떠한 사고나 문제에 대해서 제작자는 책임을 지지 않습니다.')

    def close():  # 창 닫기
        aboutwindow.destroy()

    button_exit = ttk.Button(aboutwindow,
                             text='닫기',
                             width=8,
                             command=close)
    about_row.pack(pady=15)
    about_steam.pack()
    about_email.pack()
    about_discord.pack()
    about_disclaimer.pack(pady=8)
    button_exit.pack(side='bottom', pady=5)


def addwindow():  # 계정 추가 창
    global accounts
    if len(accounts) == 12:
        messagebox.showwarning('계정 한도 도달',
                               '계정 갯수가 한도에 도달했습니다. (12개)')
        return

    addwindow = tk.Toplevel(main)
    addwindow.title("계정 추가")
    addwindow.geometry("300x150+650+300")
    addwindow.resizable(False, False)

    topframe_add = tk.Frame(addwindow)
    topframe_add.pack(side='top', anchor='center')

    bottomframe_add = tk.Frame(addwindow)
    bottomframe_add.pack(side='bottom', anchor='e')

    addlabel_row1 = tk.Label(topframe_add,
                             text='추가할 계정을 입력하세요.')
    addlabel_row2 = tk.Label(topframe_add,
                             text="다수의 계정을 입력할 경우에는\n"
                             + "'/'(슬래시)로 구분합니다.")

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
                            messagebox.showinfo('계정 중복됨',
                                                '계정 %s은 이미 추가되어 있습니다.'
                                                % name_to_write)
                elif len(accounts) == 12:
                    messagebox.showwarning('계정 한도 도달',
                                           '계정 한도에 도달하여 계정 %s를 추가할 수 없습니다.'
                                           % name_to_write)

            txt.close()
            refresh()
        addwindow.destroy()

    def close():
        addwindow.destroy()

    def enterkey(event):  # Enter 키 입력을 감지
        adduser(account_entry.get())

    addwindow.bind('<Return>', enterkey)
    button_add = ttk.Button(bottomframe_add, width=9, text='추가',
                            command=lambda: adduser(account_entry.get()))
    button_addcancel = ttk.Button(addwindow, width=9,
                                  text='취소', command=close)
    addlabel_row1.pack(pady=10)
    addlabel_row2.pack()

    account_entry.pack(side='left', padx=5, pady=3)
    button_add.pack(side='left', anchor='e', padx=5, pady=3)
    button_addcancel.pack(side='bottom', anchor='e', padx=5, pady=3)


def removewindow():
    global accounts
    if not accounts:
        messagebox.showinfo('계정 없음', '추가된 계정이 없습니다.')
        return
    removewindow = tk.Toplevel(main)
    removewindow.title("계정 삭제")
    removewindow.geometry("250x320+650+300")
    removewindow.resizable(False, False)
    bottomframe_rm = tk.Frame(removewindow)
    bottomframe_rm.pack(side='bottom')
    removewindow.grab_set()
    removewindow.focus()
    removelabel = tk.Label(removewindow, text='삭제할 계정을 선택하세요.')
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
                               text='취소',
                               command=close,
                               width=9)
    remove_ok = ttk.Button(bottomframe_rm,
                           text='삭제',
                           command=removeuser,
                           width=9)

    remove_cancel.pack(side='left', padx=5, pady=3)
    remove_ok.pack(side='left', padx=5, pady=3)


def restart_then_quit():  # Steam을 재시작
    try:
        subprocess.run("TASKKILL /F /IM Steam.exe",  # Steam.exe 프로세스 끝내기
                       creationflags=0x08000000, check=True)
        sleep(1)
    except subprocess.CalledProcessError:
        pass
    try:
        subprocess.run("start steam://open/main",  # Steam 실행
                       shell=True, check=True)
    except subprocess.CalledProcessError:
        messagebox.showerror('경고', '알 수 없는 오류로 인해\n' +
                             '스팀을 시작할 수 없습니다.')
    main.quit()


def window_height(accounts):  # 버튼의 갯수에 따라 창의 높이를 반환
    if accounts:
        to_multiply = len(accounts) - 1
    else:
        to_multiply = 0
    height_int = 160 + 32 * to_multiply
    height = str(height_int)
    return height


def toggleAutologin():  # 자동로그인 레지스트리 값 0 1 토글
    if autologin() == 1:
        value = 0
    elif autologin() == 0:
        value = 1
    setkey('RememberPassword', value, winreg.REG_DWORD)
    refresh()


print('--PHASE 5: Drawing UI--')
main = tk.Tk()
main.title("스팀 계정 전환기")

main.geometry("300x%s+600+250" %  # 기본 창 높이 140 버튼 1개당 32 증가
              window_height(accounts))  # window_height 함수 참조
main.resizable(False, False)

style = ttk.Style(main)
style.configure('c.TButton', background="#000")

menubar = tk.Menu(main)
account_menu = tk.Menu(menubar, tearoff=0)  # 상단 메뉴
account_menu.add_command(label="계정 추가", command=addwindow)
account_menu.add_command(label="계정 삭제", command=removewindow)
account_menu.add_separator()
account_menu.add_command(label="정보", command=about)
menubar.add_cascade(label="메뉴", menu=account_menu)

nouserlabel = tk.Label(main, text='추가된 계정 없음')
topframe = tk.Frame(main)
topframe.pack(side='top', fill='x')

bottomframe = tk.Frame(main)
bottomframe.pack(side='bottom')

button_toggle = ttk.Button(bottomframe,
                           width=14,
                           text='자동로그인 토글',
                           command=toggleAutologin)

button_quit = ttk.Button(bottomframe,
                         width=5,
                         text='종료',
                         command=main.quit)

button_restart = ttk.Button(bottomframe,
                            width=16,
                            text='스팀 재시작후 종료',
                            command=restart_then_quit)

button_toggle.pack(side='left', padx=4, pady=3)
button_quit.pack(side='left', padx=4, pady=3)
button_restart.pack(side='right', padx=4, pady=3)


def draw_button(accounts):
    global topframe
    global nouserlabel
    topframe.destroy()
    nouserlabel.destroy()

    topframe = tk.Frame(main)
    topframe.pack(side='top', fill='x')

    nouserlabel = tk.Label(main, text='추가된 계정 없음')
    usertext_row1 = '현재 자동로그인 계정은'
    usertext_row2 = '%s 입니다.' % getuser()

    userlabel_1 = tk.Label(topframe, text=usertext_row1)
    userlabel_1.pack(side='top')
    userlabel_2 = tk.Label(topframe, text=usertext_row2)
    userlabel_2.pack(side='top', pady=2)
    autolabel = tk.Label(topframe, text=autologinstr())
    autolabel.pack(side='top')

    if not accounts:
        nouserlabel.pack(anchor='center', expand=True)
    elif accounts:
        for v in accounts:
            if v == getuser():
                button = ttk.Button(topframe,
                                    style='c.TButton',
                                    text=v,
                                    state='disabled')
            else:
                button = ttk.Button(topframe,
                                    text=v,
                                    command=lambda name=v: setuser(name))
            button.pack(fill='x', padx=5, pady=3)


def refresh():
    global topframe
    global accounts
    fetchuser()
    topframe.destroy()
    main.geometry("300x%s" %
                  window_height(accounts))
    draw_button(accounts)
    print('Menu refreshed with %s account(s)' % len(accounts))


print('Init complete. Main app starting.')
draw_button(accounts)
main.config(menu=menubar)
main.after(100, start_checkupdate)
main.mainloop()
