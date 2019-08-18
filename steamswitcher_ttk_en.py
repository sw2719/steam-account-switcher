import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import winreg
import sys
import subprocess
from time import sleep


print('--PHASE 1: Import complete')
print('--PHASE 2: Getting registry values--')

HCU = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)


def error_msg(title, content):
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(title, content)
    root.destroy()
    sys.exit(0)


def getuser():
    try:
        reg_key = winreg.OpenKey(HCU, r"Software\Valve\Steam")
        value_buffer = winreg.QueryValueEx(reg_key, "AutoLoginUser")
        value = value_buffer[0]
        winreg.CloseKey(reg_key)
    except OSError:
        error_msg('Registry Error',
                  'Failed to fetch username value from registry.\n' +
                  'Please make sure that Steam is installed.')
    return value


def autologin():
    try:
        reg_key = winreg.OpenKey(HCU, r"Software\Valve\Steam")
        value_buffer = winreg.QueryValueEx(reg_key, "RememberPassword")
        value = value_buffer[0]
        winreg.CloseKey(reg_key)
    except OSError:
        error_msg('Registry Error',
                  'Failed to fetch auto-login value from registry.\n' +
                  'Please make sure that Steam is installed.')
    return value


def autologinstr():
    value = autologin()
    if value == 1:
        retstr = 'Auto-login is Enabled'
    elif value == 0:
        retstr = 'Auto-login is Disabled'
    return retstr


print('Fetching registry values...')
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
except FileNotFoundError:
    with open('accounts.txt', 'w') as txt:
        if getuser():
            print('No account found! Adding current user...')
            txt.write(getuser() + '\n')
    accounts = [getuser()]

print('Detected ' + str(len(accounts)) + ' accounts:')

if accounts:
    print('------------------')
    for username in accounts:
        print(username)
    print('------------------')

if len(accounts) > 12:
    error_msg('Account Error', 'Account limit exceeded.\n' +
              'You have %s accounts. (limit is 12)' % len(accounts))

print('--PHASE 4: Defining functions--')


def setkey(name, value, value_type):
    try:
        reg_key = winreg.OpenKey(HCU, r"Software\Valve\Steam", 0,
                                 winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(reg_key, name, 0, value_type, value)
        winreg.CloseKey(reg_key)
        print("Changed %s's value to %s" % (name, str(value)))
    except OSError:
        messagebox.showerror('Error', 'Registry operation failed.\n' +
                             'If this keeps happening, contact developer.\n' +
                             'Contact information available in About')
        sys.exit(0)


def setuser(username):
    setkey('AutoLoginUser', username, winreg.REG_SZ)
    refresh()


def fetchuser():
    global accounts
    txt = open('accounts.txt', 'r')
    namebuffer = txt.read().splitlines()
    txt.close()
    accounts = [item for item in namebuffer if not item.strip() == '']


def about():
    aboutwindow = tk.Toplevel(main)
    aboutwindow.title("About")
    aboutwindow.geometry("400x180+650+300")
    aboutwindow.resizable(False, False)
    about_row = tk.Label(aboutwindow, text='Made by Myeuaa (sw2719)')
    about_steam = tk.Label(aboutwindow,
                           text='Steam: https://steamcommunity.com/'
                           + 'id/muangmuang')
    about_email = tk.Label(aboutwindow, text='E-mail: sw2719@naver.com')
    about_disclaimer = tk.Label(aboutwindow,
                                text='Warning: I am not responsible for\n'
                                + 'any data loss or damage ' +
                                'caused by using this program.')

    def close():
        aboutwindow.destroy()

    button_exit = ttk.Button(aboutwindow, text='Close', width=8, command=close)
    about_row.pack(pady=15)
    about_steam.pack()
    about_email.pack()
    about_disclaimer.pack(pady=8)
    button_exit.pack(side='bottom', pady=5)


def addwindow():
    global accounts
    if len(accounts) == 12:
        messagebox.showwarning('Account Error',
                               'You have reached account limit (12).')
        return

    addwindow = tk.Toplevel(main)
    addwindow.title("Add accounts")
    addwindow.geometry("300x150+650+300")
    addwindow.resizable(False, False)
    topframe_add = tk.Frame(addwindow)
    topframe_add.pack(side='top', anchor='center')
    bottomframe_add = tk.Frame(addwindow)
    bottomframe_add.pack(side='bottom', anchor='e')
    addlabel_row1 = tk.Label(topframe_add,
                             text='Enter account(s) to add.')
    addlabel_row2 = tk.Label(topframe_add,
                             text="In case of adding multiple accounts,\n"
                             + "seperate each account with '/' (slash).")
    account_entry = ttk.Entry(bottomframe_add, width=28)
    account_entry.pack(side='left', padx=5, pady=3)
    addwindow.grab_set()
    addwindow.focus()
    account_entry.focus()
    print('Opened add window.')

    def adduser(userinput):
        if userinput.strip():
            with open('accounts.txt', 'r') as txt:
                lastname_buffer = txt.readlines()
                try:
                    lastname = lastname_buffer[-1]
                    if '\n' not in lastname:
                        prefix = '\n'
                    else:
                        prefix = ''
                except IndexError:
                    prefix = ''

            txt = open('accounts.txt', 'a')
            name_buffer = userinput.split("/")
            for name_to_write in name_buffer:
                if len(accounts) < 12:
                    if name_to_write.strip():
                        if name_to_write not in accounts:
                            print('Writing ' + name_to_write)
                            txt.write(prefix + name_to_write.strip() + '\n')
                        else:
                            print('Alert: Account %s already exists!'
                                  % name_to_write)
                            messagebox.showinfo('Account Alert',
                                                'Account %s already exists!'
                                                % name_to_write)
                elif len(accounts) == 12:
                    messagebox.showwarning('Account Error',
                                           'Could not add %s because\n'
                                           % name_to_write +
                                           'you have reached account limit.')
            txt.close()
            refresh()
        addwindow.destroy()

    def close():
        addwindow.destroy()

    def enterkey(event):
        adduser(account_entry.get())

    addwindow.bind('<Return>', enterkey)
    button_add = ttk.Button(bottomframe_add, width=9, text='Add',
                            command=lambda: adduser(account_entry.get()))
    button_addcancel = ttk.Button(addwindow, width=9,
                                  text='Cancel', command=close)
    addlabel_row1.pack(pady=10)
    addlabel_row2.pack()

    account_entry.pack(side='left', padx=5, pady=3)
    button_add.pack(side='left', anchor='e', padx=5, pady=3)
    button_addcancel.pack(side='bottom', anchor='e', padx=5, pady=3)


def removewindow():
    global accounts
    if not accounts:
        messagebox.showinfo('Account Alert', 'No accounts added!')
        return
    removewindow = tk.Toplevel(main)
    removewindow.title("Remove accounts")
    removewindow.geometry("250x320+650+300")
    removewindow.resizable(False, False)
    bottomframe_rm = tk.Frame(removewindow)
    bottomframe_rm.pack(side='bottom')
    removewindow.grab_set()
    removewindow.focus()
    removelabel = tk.Label(removewindow, text='Select accounts to remove.')
    removelabel.pack(side='top', padx=5, pady=5)
    print('Opened remove window.')

    def close():
        removewindow.destroy()

    check_dict = {}

    for v in accounts:
        var_buffer = tk.IntVar()
        checkbutton = ttk.Checkbutton(removewindow,
                                      text=v,
                                      variable=var_buffer)
        checkbutton.pack(side='top', padx=2, anchor='w')
        check_dict[v] = var_buffer

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
        txt = open('accounts.txt', 'w')
        for username in accounts:
            if username not in to_remove:
                txt.write(username + '\n')
        txt.close()
        refresh()
        close()

    remove_cancel = ttk.Button(bottomframe_rm, text='Cancel',
                               command=close, width=9)
    remove_ok = ttk.Button(bottomframe_rm, text='Remove',
                           command=removeuser, width=9)
    remove_cancel.pack(side='left', padx=5, pady=3)
    remove_ok.pack(side='left', padx=5, pady=3)


def restart_then_quit():
    try:
        subprocess.run("TASKKILL /F /IM Steam.exe",
                       creationflags=0x08000000, check=True)
        sleep(1)
    except subprocess.CalledProcessError:
        pass
    try:
        subprocess.run("start steam://open/main",
                       shell=True, check=True)
    except subprocess.CalledProcessError:
        messagebox.showerror('Error', 'Could not start Steam\n' +
                             'for unknown reason.')
    main.quit()


def window_height(accounts):
    if accounts:
        to_multiply = len(accounts) - 1
    else:
        to_multiply = 0
    height_int = 150 + 32 * to_multiply
    height = str(height_int)
    return height


def toggleAutologin():
    if autologin() == 1:
        value = 0
    elif autologin() == 0:
        value = 1
    setkey('RememberPassword', value, winreg.REG_DWORD)
    refresh()


print('--PHASE 5: Drawing UI--')
main = tk.Tk()
main.title("Account Switcher")

main.geometry("300x%s+600+250" %
              window_height(accounts))
main.resizable(False, False)

menubar = tk.Menu(main)
account_menu = tk.Menu(menubar, tearoff=0)
account_menu.add_command(label="Add accounts", command=addwindow)
account_menu.add_command(label="Remove accounts", command=removewindow)
account_menu.add_separator()
account_menu.add_command(label="About", command=about)
menubar.add_cascade(label="Menu", menu=account_menu)

topframe = ttk.Frame(main)
topframe.pack(side='top', fill='x')

bottomframe = ttk.Frame(main)
bottomframe.pack(side='bottom')

nouserlabel = ttk.Label(main, text='No accounts added')

style = ttk.Style(main)
style.configure('c.TButton', background="#000")


button_toggle = ttk.Button(bottomframe, width=14, text='Toggle auto-login',
                           command=toggleAutologin)
button_quit = ttk.Button(bottomframe, width=5, text='Exit', command=main.quit)
button_restart = ttk.Button(bottomframe, width=18, text='Restart Steam & exit',
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

    nouserlabel = tk.Label(main, text='No accounts added')
    usertext_row1 = 'Current Auto-login user:'
    usertext_row2 = getuser()

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
main.mainloop()
