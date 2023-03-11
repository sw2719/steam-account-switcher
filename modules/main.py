import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkfont
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox as msgbox
import gettext
import winreg
import subprocess
import os
import sys
import queue as q
import traceback
import sv_ttk
import datetime
from time import sleep
from PIL import Image, ImageTk
import win32clipboard
from pynput import keyboard
from modules.account import AccountManager, loginusers_accountnames, loginusers_steamid, \
    loginusers_personanames, check_autologin_availability, set_loginusers_value, remember_password_disabled
from modules.reg import fetch_reg, setkey
from modules.config import get_config, config_write_dict, config_write_value, SYS_LOCALE, first_run
from modules.util import steam_running, StoppableThread, raise_exception, test, get_center_pos, \
    launch_updater, create_shortcut
from modules.update import start_checkupdate, hide_update, show_update, update_frame_color
from modules.ui import DragDropListbox, AccountButton, AccountButtonGrid, SimpleButton, WelcomeWindow, steamid_window, \
    ToolTipWindow, ask_steam_dir, get_color, ManageEncryptionWindow
from modules.avatar import download_avatar
from modules.errormsg import error_msg
from modules.steamid import steam64_to_32

LOCALE = get_config('locale')

t = gettext.translation('steamswitcher',
                        localedir='locale',
                        languages=[LOCALE],
                        fallback=True)
_ = t.gettext

# For ImageTk, global variables must be used to prevent them from being GC'd.
image1 = None
iamge2 = None
image3 = None
image4 = None


def legacy_restart(silent=True):
    '''Legacy steam restart function for refresh function.
    New restarter with threading doesn't seem to work well with refreshing.'''
    try:
        if steam_running():
            if get_config('steam_path') == 'reg':
                raw_path = fetch_reg('steampath')
            else:
                raw_path = get_config('steam_path').replace('\\', '/')
            raw_path_items = raw_path.split('/')
            path_items = []
            for item in raw_path_items:
                if ' ' in item:
                    path_items.append(f'"{item}"')
                else:
                    path_items.append(item)
            steam_exe = "\\".join(path_items) + '\\steam.exe'
            print('Steam.exe path:', steam_exe)
            subprocess.run(f"start {steam_exe} -shutdown", shell=True,
                           creationflags=0x08000000, check=True)
            print('Shutdown command sent. Waiting for Steam...')
            sleep(2)

            counter = 0

            while steam_running():
                print('Steam is still running after %s seconds' % str(2 + counter))
                if counter <= 10:
                    counter += 1
                    sleep(1)
                    continue
                else:
                    msg = msgbox.askyesno(_('Alert'),
                                          _('After soft shutdown attempt,') + '\n' +
                                          _('Steam appears to be still running.') + '\n\n' +
                                          _('Click yes to wait more for 10 seconds or no to force-exit Steam.'))
                    if msg:
                        counter = 0
                        continue
                    else:
                        raise FileNotFoundError
        else:
            print('Steam is not running.')
    except (FileNotFoundError, subprocess.CalledProcessError):
        print('Hard shutdown mode')
        subprocess.run("TASKKILL /F /IM Steam.exe",
                       creationflags=0x08000000, check=True)
        print('TASKKILL command sent.')
        sleep(1)

    if silent:
        print('Launching Steam silently...')
        subprocess.run("start steam://open",
                       shell=True, check=True)
    else:
        print('Launching Steam...')
        subprocess.run("start steam://open/main",
                       shell=True, check=True)


class MainApp(tk.Tk):
    '''Main application'''
    def __init__(self, version, bundle, std_out, std_err, after_update):
        sys.stdout = std_out
        sys.stderr = std_err

        self.accounts = None
        self.demo_mode = False
        self.BUNDLE = bundle
        self.after_update = after_update
        self.version = version

        tk.Tk.__init__(self)

        sv_ttk.set_theme(get_config('theme'))
        self.title(_("Account Switcher"))

        self.window_width = 310
        self.window_height = 465

        center_x, center_y = get_center_pos(self, self.window_width, self.window_height)

        if get_config('last_pos') != '0/0':
            pos_x, pos_y = get_config('last_pos').split('/')
        else:
            pos_x, pos_y = center_x, center_y

        self.geometry(f'{str(self.window_width)}x{str(self.window_height)}+{str(pos_x)}+{str(pos_y)}')
        self.resizable(False, False)
        self.protocol('WM_DELETE_WINDOW', self.exit_app)

        try:
            self.iconbitmap('asset/icon.ico')
        except tk.TclError:
            pass

        self.bold_font = tkfont.Font(weight=tkfont.BOLD, size=16, family='Arial')

        lock_img = Image.open('asset/lock.png').resize((80, 80))
        self.lock_imgtk = ImageTk.PhotoImage(lock_img)

        lock_white_img = Image.open('asset/lock_white.png').resize((80, 80))
        self.lock_white_imgtk = ImageTk.PhotoImage(lock_white_img)

        if first_run or after_update:
            self.open_welcomewindow()
        elif get_config('encryption') == 'true':
            self.lockscreen()
        else:
            self.accounts = AccountManager()
            self.main_menu()

    def lockscreen(self):
        def reset_accounts_data():
            if msgbox.askyesno(_('Reset accounts data'),
                               _('This will reset all accounts data.\nThis action cannot be undone.') + '\n\n' +
                               _('Are you sure?')):
                AccountManager.reset_json()
                config_write_value('encryption', 'false')
                self.accounts = AccountManager()
                self.config(menu='')
                frame.destroy()
                self.main_menu()

        self['bg'] = get_color('window_background')
        menubar = tk.Menu(self)

        if SYS_LOCALE == 'ko_KR':
            menu_font = tkfont.Font(self, size=9, family='맑은 고딕')
            menu = tk.Menu(menubar, tearoff=0, font=menu_font)
        else:
            menu = tk.Menu(menubar, tearoff=0)

        menu.add_command(label=_('Reset accounts data'),
                         command=reset_accounts_data)
        menu.add_separator()
        menu.add_command(label=_('Exit'), command=self.exit_app)
        menubar.add_cascade(label=_('Menu'), menu=menu)
        self.config(menu=menubar)

        frame = ttk.Frame(self)
        pw_var = tk.StringVar()
        pw_var.trace("w", lambda name, index, mode, sv=pw_var: entry_check(sv))

        def check_pw():
            nonlocal frame

            password_match = AccountManager.verify_password(pw_var.get())

            if password_match:
                self.accounts = AccountManager(password=pw_var.get())
                frame.destroy()
                self.config(menu='')
                self.main_menu()
            elif password_match is None:
                prompt['text'] = _('Salt is missing.\nRestore it or reset accounts data.')
                prompt['foreground'] = get_color('autologin_text_unavail')
            else:
                prompt['text'] = _('Incorrect password. Try again.')
                prompt['foreground'] = get_color('autologin_text_unavail')
                pw_var.set('')

        button_frame = tk.Frame(frame)
        exit_button = ttk.Button(button_frame, text=_('Exit'), command=sys.exit)
        exit_button.grid(row=0, column=0, padx=(0, 1.5))
        unlock_button = ttk.Button(button_frame,
                                   text=_('Unlock (Enter)'),
                                   state='disabled',
                                   command=check_pw,
                                   style='Accent.TButton')
        unlock_button.grid(row=0, column=1, padx=(1.5, 0))
        button_frame.grid_rowconfigure(0, weight=1)
        button_frame.pack(side=tk.BOTTOM, padx=3, pady=3)

        def entry_check(sv):
            pw = sv.get()
            try:
                last_ch = pw[-1]
                if last_ch == ' ':
                    sv.set(pw[:-1])
                    return
            except IndexError:
                pass

            if pw:
                unlock_button['state'] = 'normal'
            else:
                unlock_button['state'] = 'disabled'

        pw_entry = ttk.Entry(frame, show="⬤", justify=tk.CENTER, textvariable=pw_var)
        pw_entry.pack(side=tk.BOTTOM, padx=3, fill=tk.X)
        pw_entry.bind('<Return>', lambda e: check_pw())
        pw_entry.focus()

        check_var = tk.IntVar()

        def check_command():
            if check_var.get():
                pw_entry['show'] = ''
            else:
                pw_entry['show'] = '⬤'

        checkbutton = ttk.Checkbutton(frame,
                                      text=_('Show password'),
                                      variable=check_var,
                                      command=check_command)
        checkbutton.pack(side=tk.BOTTOM, padx=3, pady=3)

        lock_icon = tk.Canvas(frame, width=300, height=200, bd=0, highlightthickness=0)

        if get_config('theme') == 'light':
            lock_icon.create_image(150, 100, image=self.lock_imgtk)
        else:
            lock_icon.create_image(150, 100, image=self.lock_white_imgtk)
        lock_icon.pack(expand=True, fill=tk.BOTH)

        ttk.Label(frame, text=_('Welcome'), font=self.bold_font).pack()
        prompt = ttk.Label(frame, text=_('Enter master password to unlock.'), justify='center')
        prompt.pack(expand=True, pady=5)
        frame.pack(fill='both', expand=True)
        self.update_idletasks()

    def main_menu(self):
        if not test():
            ask_steam_dir()

        self['bg'] = get_color('window_background')
        menubar = tk.Menu(self)

        if SYS_LOCALE == 'ko_KR':
            menu_font = tkfont.Font(self, size=9, family='맑은 고딕')
            menu = tk.Menu(menubar, tearoff=0, font=menu_font)
        else:
            menu = tk.Menu(menubar, tearoff=0)

        menu.add_command(label=_('Import accounts from Steam'),
                         command=self.importwindow)
        menu.add_command(label=_("Add accounts"),
                         command=self.addwindow)
        menu.add_command(label=_("Edit account list"),
                         command=self.orderwindow)
        menu.add_command(label=_("Refresh autologin"),
                         command=self.refreshwindow)
        menu.add_command(label=_("Update all avatars"),
                         command=self.update_avatar)
        menu.add_separator()
        menu.add_command(label=_("Settings"),
                         command=self.settingswindow)
        menu.add_command(label=_("Send feedback"),
                         command=lambda: os.startfile('https://github.com/sw2719/steam-account-switcher/issues'))
        menu.add_command(label=_("About"),
                         command=lambda: self.about(self.version))

        menubar.add_cascade(label=_("Menu"), menu=menu)
        self.config(menu=menubar)

        if not self.BUNDLE:
            debug_menu = tk.Menu(menubar, tearoff=0)
            debug_menu.add_command(label='Check for updates with debug mode',
                                   command=lambda: self.after(10, lambda: start_checkupdate(self, self.version, self.BUNDLE, debug=True)))
            debug_menu.add_command(label='Check for updates without debug mode',
                                   command=lambda: self.after(10, lambda: start_checkupdate(self, self.version, True)))
            debug_menu.add_command(label='Check for updates (Force update available)',
                                   command=lambda: self.after(10, lambda: start_checkupdate(self, '1.0', True)))
            debug_menu.add_command(label='Check for updates (Raise error)',
                                   command=lambda: self.after(10, lambda: start_checkupdate(self, self.version, True, exception=True)))
            debug_menu.add_command(label="Download avatar images",
                                   command=download_avatar)
            debug_menu.add_command(label="Open initial setup",
                                   command=lambda: self.open_welcomewindow(debug=True))
            debug_menu.add_command(label="Open initial setup with after_update True",
                                   command=lambda: self.open_welcomewindow(debug=True, update_override=True))
            debug_menu.add_command(label="Toggle demo mode",
                                   command=self.toggle_demo)
            debug_menu.add_command(label="Raise exception",
                                   command=raise_exception)
            debug_menu.add_command(label="Open about window with copyright notice",
                                   command=lambda: self.about(self.version, force_copyright=True))
            debug_menu.add_command(label="Launch updater (update.zip required)",
                                   command=launch_updater)
            debug_menu.add_command(label="Create shortcut",
                                   command=create_shortcut)
            debug_menu.add_command(label="Call error_msg",
                                   command=lambda: error_msg('Test error', 'Test error message'))
            debug_menu.add_command(label="Exit app with sys.exit",
                                   command=sys.exit)
            menubar.add_cascade(label=_("Debug"), menu=debug_menu)

        self.bottomframe = tk.Frame(self, bg=get_color('bottomframe'))
        self.bottomframe.pack(side='bottom', fill='x')

        self.restartbutton_text = tk.StringVar()

        if get_config('autoexit') == 'true':
            self.restartbutton_text.set(_('Restart Steam & Exit'))
        else:
            self.restartbutton_text.set(_('Restart Steam'))

        self.button_exit = SimpleButton(self.bottomframe,
                                        widget='bottom_button',
                                        text=_('Exit'),
                                        command=self.exit_app,
                                        bd=2)

        self.button_restart = SimpleButton(self.bottomframe,
                                           widget='bottom_button',
                                           textvariable=self.restartbutton_text,
                                           command=self.exit_after_restart,
                                           bd=2)

        self.button_exit.grid(row=0, column=0, padx=(3,0), pady=3, sticky='nesw')
        self.button_restart.grid(row=0, column=1, padx=3, pady=3, sticky='nesw')

        self.bottomframe.grid_columnconfigure(0, weight=1)
        self.bottomframe.grid_columnconfigure(1, weight=1)
        self.bottomframe.grid_rowconfigure(0, weight=1)

        self.button_dict = {}

        self.upper_frame = tk.Frame(self, bg=get_color('upperframe'))
        self.upper_frame.pack(side='top', fill='x')

        self.button_frame = tk.Frame(self, bg=get_color('upperframe'))
        self.button_frame.pack(side='top', fill='both', expand=True)

        self.userlabel_1 = tk.Label(self.upper_frame, text=_('Current Auto-login user:'), bg=self.upper_frame['bg'], fg=get_color('text'))
        self.userlabel_1.pack(side='top')

        self.user_var = tk.StringVar()
        self.user_var.set(fetch_reg('AutoLoginUser'))

        self.userlabel_2 = tk.Label(self.upper_frame, textvariable=self.user_var, bg=self.upper_frame['bg'], fg=get_color('text'))
        self.userlabel_2.pack(side='top', pady=2)

        self.auto_var = tk.StringVar()

        if check_autologin_availability(self.user_var.get()):
            self.auto_var.set(_('Auto-login Available'))
            auto_color = get_color('autologin_text_avail')
        else:
            self.auto_var.set(_('Auto-login Unavailable'))
            auto_color = get_color('autologin_text_unavail')

        self.autolabel = tk.Label(self.upper_frame, textvariable=self.auto_var, bg=self.upper_frame['bg'], fg=auto_color)
        self.autolabel.pack(side='top')

        tk.Frame(self.upper_frame, bg='grey').pack(fill='x')

        self.draw_button()

        self.after(100, lambda: start_checkupdate(self, self.version, self.BUNDLE))

    def report_callback_exception(self, exc, val, tb):
        if self.BUNDLE:
            msgbox.showerror(_('Unhandled Exception'),
                             message=traceback.format_exc() + '\n' + _('Please contact the developer if the issue persists.'))
        else:
            traceback.print_exc()

    def get_window_pos(self):
        geo = self.geometry().split('+')
        return geo[1], geo[2]

    def popup_geometry(self, width, height, multiplier=1):
        width_delta = (self.window_width - width) // 2

        main_x, main_y = self.get_window_pos()
        x = int(main_x) + width_delta
        y = int(main_y) + (25 * multiplier)

        return f'{str(width)}x{str(height)}+{str(x)}+{str(y)}'

    def exit_app(self):
        x, y = self.get_window_pos()
        last_pos = f'{x}/{y}'
        config_write_value('last_pos', last_pos)
        sys.exit(0)

    def toggle_demo(self):
        if self.demo_mode:
            self.demo_mode = False
        else:
            self.demo_mode = True

        self.refresh()

    def open_welcomewindow(self, debug=False, update_override=False):
        self.withdraw()

        if update_override:
            welcomewindow = WelcomeWindow(self, self.popup_geometry(320, 300, multiplier=2), True, debug)
        else:
            welcomewindow = WelcomeWindow(self, self.popup_geometry(320, 300, multiplier=2), self.after_update, debug)

        def after_init(pw):
            if get_config('encryption') == 'true' and not update_override:
                if pw:
                    self.accounts = AccountManager(pw)
                    self.main_menu()
                else:
                     self.lockscreen()
            elif not debug:
                self.accounts = AccountManager()
                self.main_menu()
            else:
                self.refresh()
            self.update_idletasks()
            self.deiconify()

        def event_function(event):
            nonlocal welcomewindow
            if str(event.widget) == '.!welcomewindow':
                pw = welcomewindow.pw
                del welcomewindow
                after_init(pw)

        welcomewindow.bind('<Destroy>', event_function)

    def account_settings_window(self, username):
        account_settings_window = tk.Toplevel(self)
        account_settings_window.title('')

        account_settings_window.geometry(self.popup_geometry(250, 270))
        account_settings_window.resizable(False, False)
        account_settings_window.bind('<Escape>', lambda event: account_settings_window.destroy())

        try:
            account_settings_window.iconbitmap('asset/icon.ico')
        except tk.TclError:
            pass

        custom_name = self.accounts.get_customname(username)

        button_frame = tk.Frame(account_settings_window)
        button_frame.pack(side='bottom', pady=3)

        ok_button = ttk.Button(button_frame, text=_('OK'), style='Accent.TButton')
        ok_button.pack(side='right', padx=1.5)

        cancel_button = ttk.Button(button_frame,
                                   text=_('Cancel'),
                                   command=account_settings_window.destroy)
        cancel_button.pack(side='left', padx=1.5)

        top_label = tk.Label(account_settings_window, text=_('Settings for %s') % username)
        top_label.pack(side='top', pady=(8, 3))

        radio_frame1 = tk.Frame(account_settings_window)
        radio_frame1.pack(side='top', padx=(10, 0), pady=(12, 2), fill='x')
        radio_frame2 = tk.Frame(account_settings_window)
        radio_frame2.pack(side='top', padx=(10, 0), pady=(0, 3), fill='x')
        custom_name_var = tk.IntVar()

        if custom_name.strip():
            custom_name_var.set(1)
        else:
            custom_name_var.set(0)

        radio_default = ttk.Radiobutton(radio_frame1,
                                        text=_('Use profile name if available'),
                                        variable=custom_name_var,
                                        value=0)
        radio_custom = ttk.Radiobutton(radio_frame2,
                                       text=_('Use custom name'),
                                       variable=custom_name_var,
                                       value=1)

        radio_default.pack(side='left', pady=2)
        radio_custom.pack(side='left', pady=2)

        name_entry_frame = tk.Frame(account_settings_window)
        name_entry_frame.pack(side='top', pady=4, fill='x')

        name_entry = ttk.Entry(name_entry_frame, justify=tk.CENTER)
        name_entry.insert(0, custom_name)
        name_entry.pack(fill='x', padx=3)

        account_settings_window.grab_set()
        account_settings_window.focus()

        if custom_name_var.get() == 0:
            name_entry['state'] = 'disabled'

        def reset_entry():
            name_entry.delete(0, 'end')
            name_entry['state'] = 'disabled'

        def enable_entry():
            name_entry['state'] = 'normal'
            name_entry.focus()

        radio_default['command'] = reset_entry
        radio_custom['command'] = enable_entry

        save_password_var = tk.IntVar()

        save_password_frame = ttk.Frame(account_settings_window)
        save_password_frame.pack(side='top', padx=(10, 0), pady=(12, 3), fill='x')

        save_password_chkb = ttk.Checkbutton(save_password_frame,
                                          text=_('Save password'),
                                          variable=save_password_var)

        save_password_chkb['state'] = '!alternate'

        set_password = self.accounts.get_password(username)

        save_password_chkb.pack(side='left')

        password_entry_frame = tk.Frame(account_settings_window)
        password_entry_frame.pack(side='top', pady=(2, 0), fill='x')

        password_entry = ttk.Entry(password_entry_frame, justify=tk.CENTER, show='⬤')
        password_entry.pack(side='left', fill='x', expand=True, padx=(3, 3))

        show_var = tk.IntVar()

        checkbutton = ttk.Checkbutton(password_entry_frame,
                                      text=_('Show'),
                                      variable=show_var,
                                      style='Toggle.TButton')
        checkbutton.pack(side=tk.RIGHT, padx=(0, 3))

        password_warn_label = ttk.Label(account_settings_window,
                                        text=_('Warning: Encryption is disabled.\n'
                                               'Password will be stored in plain text!'),
                                        justify='center',
                                        foreground=get_color('autologin_text_unavail'))

        window_larger = False

        def on_password_checkbox():
            nonlocal window_larger

            if save_password_var.get() == 1:
                password_entry['state'] = 'normal'
                checkbutton['state'] = 'normal'

                if get_config('encryption') == 'false':
                    account_settings_window.geometry(
                        f'{str(account_settings_window.winfo_width())}x{str(account_settings_window.winfo_height() + 35)}'
                        f'+{str(account_settings_window.winfo_x())}+{str(account_settings_window.winfo_y())}'
                    )
                    password_warn_label.pack(side='bottom', pady=(0, 3))
                    window_larger = True

                password_entry.focus()
            else:
                password_entry.delete(0, 'end')
                password_entry['state'] = 'disabled'
                checkbutton['state'] = 'disabled'

                if get_config('encryption') == 'false' and window_larger:
                    account_settings_window.geometry(
                        f'{str(account_settings_window.winfo_width())}x{str(account_settings_window.winfo_height() - 35)}'
                        f'+{str(account_settings_window.winfo_x())}+{str(account_settings_window.winfo_y())}'
                    )
                    password_warn_label.pack_forget()
                    window_larger = False

        save_password_chkb['command'] = on_password_checkbox

        def on_show_checkbutton():
            if show_var.get():
                password_entry['show'] = ''
                checkbutton['text'] = _('Hide')
            else:
                password_entry['show'] = '⬤'
                checkbutton['text'] = _('Show')

        checkbutton['command'] = on_show_checkbutton

        if set_password:
            save_password_var.set(1)
            password_entry.insert(0, set_password)
        else:
            password_entry['state'] = 'disabled'
            checkbutton['state'] = 'disabled'

        def ok(username):
            if custom_name_var.get() == 1 and not name_entry.get().strip():
                if save_password_var.get() == 1 and not password_entry.get().strip():
                    msgbox.showwarning(_('Info'), _('Enter a custom profile name and a account password.'),
                                       parent=account_settings_window)
                else:
                    msgbox.showwarning(_('Info'), _('Enter a custom profile name.'),
                                       parent=account_settings_window)
            elif save_password_var.get() == 1 and not password_entry.get().strip():
                msgbox.showwarning(_('Info'), _('Enter a account password.'),
                                   parent=account_settings_window)

            else:
                if custom_name_var.get():
                    self.accounts.set_customname(username, name_entry.get())
                else:
                    self.accounts.remove_customname(username)

                if save_password_var.get():
                    self.accounts.set_password(username, password_entry.get())
                else:
                    self.accounts.remove_password(username)

                self.refresh()
                account_settings_window.destroy()

        def enterkey(event):
            ok(username)

        account_settings_window.bind('<Return>', enterkey)
        ok_button['command'] = lambda username=username: ok(username)

        if save_password_var.get() == 1 and get_config('encryption') == 'false':
            account_settings_window.geometry(
                f'{str(account_settings_window.winfo_width())}x{str(account_settings_window.winfo_height() + 35)}'
                f'+{str(account_settings_window.winfo_x())}+{str(account_settings_window.winfo_y())}'
            )
            password_warn_label.pack(side='bottom', pady=(0, 3))
            window_larger = True

        account_settings_window.wait_window()

    def button_func(self, username):
        current_user = fetch_reg('AutoLoginUser')

        try:
            self.button_dict[current_user].enable()
        except Exception:
            pass

        setkey('AutoLoginUser', username, winreg.REG_SZ)
        self.button_dict[username].disable()
        self.user_var.set(fetch_reg('AutoLoginUser'))

        if check_autologin_availability(self.user_var.get()):
            self.auto_var.set(_('Auto-login Available'))
            auto_color = get_color('autologin_text_avail')
        else:
            self.auto_var.set(_('Auto-login Unavailable'))
            auto_color = get_color('autologin_text_unavail')

        self.autolabel['fg'] = auto_color

        self.focus()

        if get_config('mode') == 'express':
            self.exit_after_restart()

    def remove_user(self, username):
        if msgbox.askyesno(_('Confirm'), _('Are you sure want to remove account %s?') % username):
            print(f'Removing {username}...')
            self.accounts.remove(username)

            self.refresh()

    def open_screenshot(self, steamid64, steam_path=get_config('steam_path')):
        if steam_path == 'reg':
            steam_path = fetch_reg('steampath')

        if '/' in steam_path:
            steam_path = steam_path.replace('/', '\\')

        if os.path.isdir(f'{steam_path}\\userdata\\{steam64_to_32(steamid64)}\\760\\remote'):
            os.startfile(f'{steam_path}\\userdata\\{steam64_to_32(steamid64)}\\760\\remote')
        else:
            msgbox.showinfo(_('No screenshots directory'), _('No screenshots directory was found for this account.'))

    def draw_button(self):
        if get_config('ui_mode') == 'list':
            self.draw_button_list()
        elif get_config('ui_mode') == 'grid':
            self.draw_button_grid()

    def draw_button_grid(self):
        menu_dict = {}
        self.no_user_frame = tk.Frame(self.button_frame, bg=self['bg'])

        def onFrameConfigure(canvas):
            canvas.configure(scrollregion=canvas.bbox("all"))

        if self.demo_mode:
            canvas = tk.Canvas(self.button_frame, borderwidth=0, highlightthickness=0)
            canvas.config(bg=self['bg'])
            buttonframe = tk.Frame(canvas, bg=self['bg'])
            scroll_bar = ttk.Scrollbar(self.button_frame,
                                       orient="vertical",
                                       command=canvas.yview)

            for x in range(0, 13):
                self.button_dict[x] = AccountButtonGrid(buttonframe,
                                                        username='username' + str(x),
                                                        profilename='profilename' + str(x),
                                                        image='default')

                if x == 0:
                    self.button_dict[x].disable()

                row = x // 3
                column = x % 3

                if column == 1:
                    self.button_dict[x].grid(row=row, column=column, padx=0, pady=(9, 0))
                else:
                    self.button_dict[x].grid(row=row, column=column, padx=10, pady=(9, 0))

            buttonframe.grid_propagate(False)
            scroll_bar.pack(side="right", fill="y")
            canvas.pack(side="left", fill='both', expand=True)

            h = 109 * (12 // 3)

            canvas.create_window((0, 0), height=h + 9, width=295, window=buttonframe, anchor="nw")
            canvas.configure(yscrollcommand=scroll_bar.set)
            canvas.configure(width=self.button_frame.winfo_width(), height=self.button_frame.winfo_height())

            def _on_mousewheel(event):
                '''Scroll window on mousewheel input'''
                widget = event.widget.winfo_containing(event.x_root, event.y_root)

                if 'disabled' not in scroll_bar.state() and '!canvas' in str(widget):
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

            buttonframe.bind("<Configure>", lambda event,
                             canvas=canvas: onFrameConfigure(canvas))
            self.bind("<MouseWheel>", _on_mousewheel)

        elif self.accounts:
            canvas = tk.Canvas(self.button_frame, borderwidth=0, highlightthickness=0)
            canvas.config(bg=self['bg'])
            buttonframe = tk.Frame(canvas, bg=self['bg'])
            scroll_bar = ttk.Scrollbar(self.button_frame,
                                       orient="vertical",
                                       command=canvas.yview)

            for index, username in enumerate(self.accounts.list):
                steam64_list = loginusers_steamid()
                account_name = loginusers_accountnames()
                persona_name = loginusers_personanames()

                if username in account_name:
                    i = account_name.index(username)
                else:
                    i = None

                profilename = self.accounts.get_customname(username)

                if not profilename:
                    if i is not None:
                        profilename = persona_name[i]
                    else:
                        profilename = _('N/A')

                if i is not None:
                    steam64 = steam64_list[i]
                    image = steam64
                else:
                    steam64 = None
                    image = 'default'

                    profilename = profilename[:30]

                if SYS_LOCALE == 'ko_KR':
                    menu_font = tkfont.Font(self, size=9, family='맑은 고딕')
                    menu_dict[username] = tk.Menu(self, tearoff=0, font=menu_font)
                else:
                    menu_dict[username] = tk.Menu(self, tearoff=0)

                menu_dict[username].add_command(label=_("Set as auto-login account"),
                                                command=lambda name=username: self.button_func(name))
                menu_dict[username].add_separator()

                if i is not None:
                    menu_dict[username].add_command(label=_('Open profile in browser'),
                                                    command=lambda steamid64=steam64: os.startfile(f'https://steamcommunity.com/profiles/{steamid64}'))
                    menu_dict[username].add_command(label=_('Open screenshots folder'),
                                                    command=lambda steamid64=steam64: self.open_screenshot(steamid64))
                    menu_dict[username].add_command(label=_('Account info'),
                                                    command=lambda username=username, steamid64=steam64: steamid_window(self, username, steamid64, self.popup_geometry(270, 240)))
                    menu_dict[username].add_command(label=_('Update avatar'),
                                                    command=lambda steamid64=steam64: self.update_avatar(steamid_list=[steamid64]))
                    menu_dict[username].add_separator()

                menu_dict[username].add_command(label=_("Account settings"),
                                                command=lambda name=username, pname=profilename: self.account_settings_window(name))
                menu_dict[username].add_command(label=_("Delete"),
                                                command=lambda name=username: self.remove_user(name))

                def popup(username, event):
                    menu_dict[username].tk_popup(event.x_root + 86, event.y_root + 13, 0)

                self.button_dict[username] = AccountButtonGrid(buttonframe,
                                                               username=username,
                                                               profilename=profilename,
                                                               command=lambda name=username: self.button_func(name),
                                                               rightcommand=lambda event, username=username: popup(username, event),
                                                               image=image)

                if username == fetch_reg('AutoLoginUser'):
                    self.button_dict[username].disable(no_fade=True)

                row = index // 3
                column = index % 3

                if column == 1:
                    self.button_dict[username].grid(row=row, column=column, padx=0, pady=(9, 0))
                else:
                    self.button_dict[username].grid(row=row, column=column, padx=10, pady=(9, 0))

            buttonframe.grid_propagate(False)
            scroll_bar.pack(side="right", fill="y")
            canvas.pack(side="left", fill='both', expand=True)

            accounts_count = len(self.accounts.list)

            if accounts_count % 3 == 0:
                h = 109 * (accounts_count // 3)
            else:
                h = 109 * (accounts_count // 3 + 1)

            canvas.create_window((0, 0), height=h + 9, width=295, window=buttonframe, anchor="nw")
            canvas.configure(yscrollcommand=scroll_bar.set)
            canvas.configure(width=self.button_frame.winfo_width(), height=self.button_frame.winfo_height())

            def _on_mousewheel(event):
                '''Scroll window on mousewheel input'''
                widget = event.widget.winfo_containing(event.x_root, event.y_root)

                if 'disabled' not in scroll_bar.state() and '!canvas' in str(widget):
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

            buttonframe.bind("<Configure>", lambda event,
                             canvas=canvas: onFrameConfigure(canvas))
            self.bind("<MouseWheel>", _on_mousewheel)
        else:
            self.no_user_frame.pack(side='top', fill='both', expand=True)
            no_user = tk.Label(self.no_user_frame, text=_('No accounts added'), bg=self['bg'])
            self.unbind("<MouseWheel>")
            no_user.pack(pady=(150, 0))

    def draw_button_list(self):
        menu_dict = {}
        self.no_user_frame = tk.Frame(self.button_frame, bg=self['bg'])

        def onFrameConfigure(canvas):
            canvas.configure(scrollregion=canvas.bbox("all"))

        if self.demo_mode:
            canvas = tk.Canvas(self.button_frame, borderwidth=0, highlightthickness=0)
            canvas.config(bg=self['bg'])
            buttonframe = tk.Frame(canvas)
            scroll_bar = ttk.Scrollbar(self.button_frame,
                                       orient="vertical",
                                       command=canvas.yview)

            for x in range(0, 8):
                self.button_dict[x] = AccountButton(buttonframe,
                                                    username='username' + str(x),
                                                    profilename='profilename' + str(x),
                                                    image='default')

                if x == 0:
                    self.button_dict[x].disable()

                self.button_dict[x].pack(fill='x')
                tk.Frame(buttonframe, bg='#c4c4c4').pack(fill='x')

            scroll_bar.pack(side="right", fill="y")
            canvas.pack(side="left", fill='both', expand=True)
            h = 49 * 8
            canvas.create_window((0, 0), height=h, width=310, window=buttonframe, anchor="nw")
            canvas.configure(yscrollcommand=scroll_bar.set)
            canvas.configure(width=self.button_frame.winfo_width(), height=self.button_frame.winfo_height())

            def _on_mousewheel(event):
                '''Scroll window on mousewheel input'''
                widget = event.widget.winfo_containing(event.x_root, event.y_root)

                if 'disabled' not in scroll_bar.state() and '!canvas' in str(widget):
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

            buttonframe.bind("<Configure>", lambda event,
                             canvas=canvas: onFrameConfigure(canvas))
            self.bind("<MouseWheel>", _on_mousewheel)
        elif self.accounts:
            canvas = tk.Canvas(self.button_frame, borderwidth=0, highlightthickness=0)
            canvas.config(bg=self['bg'])
            buttonframe = tk.Frame(canvas)
            scroll_bar = ttk.Scrollbar(self.button_frame,
                                       orient="vertical",
                                       command=canvas.yview)

            for username in self.accounts.list:
                steam64_list = loginusers_steamid()
                account_name = loginusers_accountnames()
                persona_name = loginusers_personanames()

                if username in account_name:
                    i = account_name.index(username)
                else:
                    i = None

                profilename = self.accounts.get_customname(username)

                if not profilename:
                    if i is not None:
                        profilename = persona_name[i]
                    else:
                        profilename = _('N/A')

                if i is not None:
                    steam64 = steam64_list[i]
                    image = steam64
                else:
                    steam64 = None
                    image = 'default'

                    profilename = profilename[:30]

                if SYS_LOCALE == 'ko_KR':
                    menu_font = tkfont.Font(self, size=9, family='맑은 고딕')
                    menu_dict[username] = tk.Menu(self, tearoff=0, font=menu_font)
                else:
                    menu_dict[username] = tk.Menu(self, tearoff=0)

                menu_dict[username].add_command(label=_("Set as auto-login account"),
                                                command=lambda name=username: self.button_func(name))
                menu_dict[username].add_separator()

                if i is not None:
                    menu_dict[username].add_command(label=_('Open profile in browser'),
                                                    command=lambda steamid64=steam64: os.startfile(f'https://steamcommunity.com/profiles/{steamid64}'))
                    menu_dict[username].add_command(label=_('Open screenshots folder'),
                                                    command=lambda steamid64=steam64: self.open_screenshot(steamid64))
                    menu_dict[username].add_command(label=_('View SteamID'),
                                                    command=lambda username=username, steamid64=steam64: steamid_window(self, username, steamid64, self.popup_geometry(270, 240)))
                    menu_dict[username].add_command(label=_('Update avatar'),
                                                    command=lambda steamid64=steam64: self.update_avatar(steamid_list=[steamid64]))
                    menu_dict[username].add_separator()

                menu_dict[username].add_command(label=_("Account settings"),
                                                command=lambda name=username, pname=profilename: self.account_settings_window(name))
                menu_dict[username].add_command(label=_("Delete"),
                                                command=lambda name=username: self.remove_user(name))

                def popup(username, event):
                    menu_dict[username].tk_popup(event.x_root, event.y_root, 0)

                self.button_dict[username] = AccountButton(buttonframe,
                                                           username=username,
                                                           profilename=profilename,
                                                           command=lambda name=username: self.button_func(name),
                                                           rightcommand=lambda event, username=username: popup(username, event),
                                                           image=image)

                if username == fetch_reg('AutoLoginUser'):
                    self.button_dict[username].disable(no_fade=True)

                self.button_dict[username].pack(fill='x')
                tk.Frame(buttonframe, bg=get_color('seperator')).pack(fill='x')

            scroll_bar.pack(side="right", fill="y")
            canvas.pack(side="left", fill='both', expand=True)
            h = 47 * len(self.accounts.list)
            canvas.create_window((0, 0), height=h, width=295, window=buttonframe, anchor="nw")
            canvas.configure(yscrollcommand=scroll_bar.set)
            canvas.configure(width=self.button_frame.winfo_width(), height=self.button_frame.winfo_height())

            def _on_mousewheel(event):
                '''Scroll window on mousewheel input'''
                widget = event.widget.winfo_containing(event.x_root, event.y_root)

                if 'disabled' not in scroll_bar.state() and '!canvas' in str(widget):
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

            buttonframe.bind("<Configure>", lambda event,
                             canvas=canvas: onFrameConfigure(canvas))
            self.bind("<MouseWheel>", _on_mousewheel)
        else:
            self.no_user_frame.pack(side='top', fill='both', expand=True)
            no_user = tk.Label(self.no_user_frame, text=_('No accounts added'), bg=self['bg'], fg=get_color('text'))
            self.unbind("<MouseWheel>")
            no_user.pack(pady=(150, 0))

    def refresh(self, no_frame=False):
        '''Refresh main window widgets'''
        if not no_frame:
            self.no_user_frame.destroy()
            self.button_frame.destroy()

        self.button_frame = tk.Frame(self, bg=get_color('bottomframe'))
        self.button_frame.pack(side='top', fill='both', expand=True)
        self['bg'] = get_color('window_background')

        self.bottomframe.configure(bg=get_color('bottomframe'))
        self.button_exit.update_color()
        self.button_restart.update_color()
        self.upper_frame.configure(bg=get_color('upperframe'))
        self.userlabel_1.configure(bg=self.upper_frame['bg'], fg=get_color('text'))
        self.userlabel_2.configure(bg=self.upper_frame['bg'], fg=get_color('text'))

        update_frame_color()

        if self.demo_mode:
            self.user_var.set('username0')
        else:
            self.user_var.set(fetch_reg('AutoLoginUser'))

        if self.demo_mode:
            self.auto_var.set(_('Auto-login Available'))
            auto_color = get_color('autologin_text_avail')
        elif check_autologin_availability(self.user_var.get()):
            self.auto_var.set(_('Auto-login Available'))
            auto_color = get_color('autologin_text_avail')
        else:
            self.auto_var.set(_('Auto-login Unavailable'))
            auto_color = get_color('autologin_text_unavail')

        self.autolabel['fg'] = auto_color
        self.autolabel['bg'] = get_color('upperframe')
        self.draw_button()

        if get_config('autoexit') == 'true':
            self.restartbutton_text.set(_('Restart Steam & Exit'))
        else:
            self.restartbutton_text.set(_('Restart Steam'))

        print('Menu refreshed')

    def update_avatar(self, steamid_list=None, no_ui=False):
        label = tk.Label(self, text=_('Please wait while downloading avatars...'), bg=self['bg'], fg=get_color('text'))

        if not no_ui:
            self.no_user_frame.destroy()
            self.button_frame.destroy()
            hide_update()
            self.bottomframe.pack_forget()
            label.pack(expand=True)
            self.update()

        if steamid_list:
            dl_list = steamid_list
        else:
            dl_list = []
            steam64_list = loginusers_steamid()
            account_name = loginusers_accountnames()

            for index, steamid in enumerate(steam64_list):
                if account_name[index] in self.accounts.list:
                    dl_list.append(steamid)

        download_avatar(dl_list)

        if not no_ui:
            label.destroy()
            self.refresh(no_frame=True)
            self.bottomframe.pack(side='bottom', fill='x')
            show_update()

    def about(self, version, force_copyright=False):
        '''Open about window'''

        if LOCALE == 'fr_FR':
            height = 210
        else:
            height = 190

        aboutwindow = tk.Toplevel(self)
        aboutwindow.title(_('About'))
        aboutwindow.geometry(self.popup_geometry(380, height))
        aboutwindow.resizable(False, False)
        aboutwindow.focus()
        aboutwindow.bind('<Escape>', lambda event: aboutwindow.destroy())

        year = str(datetime.datetime.today().year)

        try:
            aboutwindow.iconbitmap('asset/icon.ico')
        except tk.TclError:
            pass

        about_disclaimer = tk.Label(aboutwindow,
                                    text=_('Warning: The developer of this application is not responsible for\n' +
                                           'any incident or damage occurred by using this app.'))
        about_steam_trademark = tk.Label(aboutwindow,
                                         text=_('STEAM is a registered trademark of Valve Corporation.'))
        if self.BUNDLE or force_copyright:
            copyright_label = tk.Label(aboutwindow,
                                        text=f'Copyright (c) {year} sw2719 | All Rights Reserved' + '\n' +
                                             'Read copyright notice for details')
        else:
            copyright_label = tk.Label(aboutwindow,
                                       text=f'Copyright (c) {year} sw2719 | All Rights Reserved' + '\n' +
                                            'Read LICENSE file for details')
        ver = tk.Label(aboutwindow,
                       text='Steam Account Switcher | Version ' + version)

        def copyright_notice():
            cprightwindow = tk.Toplevel(aboutwindow)
            cprightwindow.title(_('Copyright notice'))
            cprightwindow.geometry(self.popup_geometry(630, 350, multiplier=2))
            cprightwindow.resizable(False, False)
            cprightwindow.focus()
            cprightwindow.bind('<Escape>', lambda event: cprightwindow.destroy())

            try:
                cprightwindow.iconbitmap('asset/icon.ico')
            except tk.TclError:
                pass

            ttk.Button(cprightwindow, text=_('Close'), command=cprightwindow.destroy, style="Accent.TButton").pack(side='bottom', pady=3)
            ttk.Separator(cprightwindow, orient=tk.HORIZONTAL).pack(side='bottom', fill='x')

            cpright_text = ScrolledText(cprightwindow, bd=1, relief='flat')

            with open('asset/COPYRIGHT_NOTICE', encoding='utf-8') as txt:
                cpright_text.insert(tk.CURRENT, txt.read())

            cpright_text.configure(state=tk.DISABLED)
            cpright_text.pack(side='top', expand=True, fill='both')

        button_frame = tk.Frame(aboutwindow)
        button_frame.pack(side='bottom', pady=5)

        button_close = ttk.Button(button_frame,
                                  text=_('Close'),
                                  command=aboutwindow.destroy,
                                  style="Accent.TButton")
        button_github = ttk.Button(button_frame,
                                   text=_('GitHub page'),
                                   command=lambda: os.startfile('https://github.com/sw2719/steam-account-switcher'))
        button_copyright = ttk.Button(button_frame,
                                      text=_('Copyright notice'),
                                      command=copyright_notice)

        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        button_frame.grid_rowconfigure(0, weight=1)

        about_disclaimer.pack(pady=8)
        about_steam_trademark.pack()
        copyright_label.pack(pady=5)
        ver.pack()

        button_close.grid(row=0, column=0, padx=2)
        button_github.grid(row=0, column=1, padx=2)

        if self.BUNDLE or force_copyright:
            button_copyright.grid(row=0, column=2, padx=2)

    def refreshwindow(self):
        '''Open remove accounts window'''
        accounts = self.accounts.list
        if not accounts:
            msgbox.showinfo(_('No Accounts'),
                            _("There's no account added."))
            return
        refreshwindow = tk.Toplevel(self)
        refreshwindow.title(_("Refresh"))
        refreshwindow.geometry(self.popup_geometry(230, 320))
        refreshwindow.resizable(False, False)
        refreshwindow.bind('<Escape>', lambda event: refreshwindow.destroy())
        refreshwindow.grab_set()
        refreshwindow.focus()

        try:
            refreshwindow.iconbitmap('asset/icon.ico')
        except tk.TclError:
            pass

        bottomframe_rm = tk.Frame(refreshwindow)
        bottomframe_rm.pack(side='bottom')

        removelabel = tk.Label(refreshwindow, text=_('Select accounts to refresh.'))
        removelabel.pack(side='top', padx=5, pady=5)

        def close():
            refreshwindow.destroy()

        def onFrameConfigure(canvas):
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas = tk.Canvas(refreshwindow, borderwidth=0, highlightthickness=0)
        check_frame = tk.Frame(canvas)
        scroll_bar = ttk.Scrollbar(refreshwindow,
                                   orient="vertical",
                                   command=canvas.yview)

        canvas.configure(yscrollcommand=scroll_bar.set)

        scroll_bar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((4, 4), window=check_frame, anchor="nw")

        def _on_mousewheel(event):
            '''Scroll window on mousewheel input'''
            if 'disabled' not in scroll_bar.state():
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

        def refreshuser():
            refreshwindow.destroy()
            to_refresh = []
            current_user = fetch_reg('AutoLoginUser')

            for v in accounts:
                if check_dict.get(v).get() == 1:
                    to_refresh.append(v)
                else:
                    continue

            self.withdraw()

            msgbox.showinfo('', _('Accounts with expired autologin token will show login prompt.') + '\n\n' +
                                _('Close the prompt or login to continue the process.'))  # NOQA

            popup = tk.Toplevel(self)
            popup.title('')
            popup.geometry(self.popup_geometry(180, 100))
            popup.resizable(False, False)

            popup_var = tk.StringVar()
            popup_var.set(_('Initializing...'))

            popup_uservar = tk.StringVar()
            popup_uservar.set('---------')

            popup_label = tk.Label(popup, textvariable=popup_var)
            popup_user = tk.Label(popup, textvariable=popup_uservar)

            popup_label.pack(pady=17)
            popup_user.pack()

            self.update()

            for username in accounts:
                if username in to_refresh:
                    popup_uservar.set(username)
                    popup_var.set(_('Switching account...'))
                    self.update()

                    setkey('AutoLoginUser', username, winreg.REG_SZ)
                    if username == accounts[-1] and username == current_user:
                        legacy_restart(silent=False)
                    else:
                        legacy_restart()

                    while fetch_reg('pid') == 0:
                        sleep(1)

                    popup_var.set(_('Waiting for Steam...'))
                    self.update()

                    while True:  # Wait for Steam to log in
                        sleep(1)
                        if fetch_reg('ActiveUser') != 0:
                            sleep(4)
                            break

            popup.destroy()
            self.update()

            if current_user != fetch_reg('AutoLoginUser'):
                if msgbox.askyesno('', _('Do you want to start Steam with previous autologin account?')):
                    setkey('AutoLoginUser', current_user, winreg.REG_SZ)
                    legacy_restart(silent=False)
            else:
                subprocess.run("start steam://open/main", shell=True)

            self.deiconify()
            self.refresh()

        refresh_cancel = ttk.Button(bottomframe_rm,
                                    text=_('Cancel'),
                                    command=close,
                                    width=9)
        refresh_ok = ttk.Button(bottomframe_rm,
                                text=_('Refresh'),
                                command=refreshuser,
                                width=9,
                                style="Accent.TButton")

        refresh_cancel.pack(side='left', padx=5, pady=3)
        refresh_ok.pack(side='left', padx=5, pady=3)

    def addwindow(self):
        '''Open add accounts window'''
        steamid_list = []
        account_names = []

        x, y = self.get_window_pos()

        addwindow = tk.Toplevel(self)
        addwindow.title(_("Add"))
        addwindow.geometry(self.popup_geometry(320, 200))
        addwindow.resizable(False, False)
        addwindow.bind('<Escape>', lambda event: addwindow.destroy())

        try:
            addwindow.iconbitmap('asset/icon.ico')
        except tk.TclError:
            pass

        topframe_add = tk.Frame(addwindow)
        topframe_add.pack(side='top', anchor='center')

        bottomframe_add = tk.Frame(addwindow)
        bottomframe_add.pack(side='bottom', anchor='e', fill='x')

        addlabel_row1 = tk.Label(topframe_add, text=_('Enter account(s) to add.'))
        addlabel_row2 = tk.Label(topframe_add, text=_("In case of adding multiple accounts,") + '\n' +
                                                    _("seperate each account with '/' (slash)."))

        account_entry = ttk.Entry(bottomframe_add, width=27)

        addwindow.grab_set()
        addwindow.focus()
        account_entry.focus()

        def disable_close():
            pass

        def adduser(userinput):
            dl_list = []

            if userinput.strip():
                name_buffer = userinput.split("/")
                accounts_to_add = [name.strip() for name in name_buffer if name.strip()]

                existing_accounts = self.accounts.add_multiple_accounts(accounts_to_add)
                if existing_accounts:
                    for existing_account in existing_accounts:
                        msgbox.showinfo(_('Duplicate Alert'),
                                        _('Account %s already exists.')
                                        % existing_account)

                if dl_list and get_config('show_avatar') == 'true':
                    button_addcancel.destroy()
                    bottomframe_add.destroy()
                    topframe_add.destroy()
                    addwindow.protocol("WM_DELETE_WINDOW", disable_close)
                    addwindow.focus()

                    tk.Label(addwindow, text=_('Please wait while downloading avatars...'), bg='white').pack(fill='both', expand=True)
                    self.update()
                    download_avatar(dl_list)

                self.refresh()
            addwindow.destroy()

        def close():
            addwindow.destroy()

        def enterkey(event):
            adduser(account_entry.get())

        addwindow.bind('<Return>', enterkey)
        button_add = ttk.Button(bottomframe_add, width=10, text=_('Add'), style="Accent.TButton",
                                command=lambda: adduser(account_entry.get()))
        button_addcancel = ttk.Button(addwindow, width=10,
                                      text=_('Cancel'), command=close)
        addlabel_row1.pack(pady=10)
        addlabel_row2.pack()

        account_entry.pack(side='left', padx=(3, 0), pady=3, fill='x', expand=True)
        button_add.pack(side='right', anchor='e', padx=3, pady=3)
        button_addcancel.pack(side='bottom', anchor='e', padx=3)

    def importwindow(self):
        '''Open import accounts window'''
        steam64_list = loginusers_steamid()
        account_name = loginusers_accountnames()
        persona_name = loginusers_personanames()

        if set(account_name).issubset(set(self.accounts.list)):
            msgbox.showinfo(_('Info'), _("There's no account left to import."))
            return

        x, y = self.get_window_pos()

        importwindow = tk.Toplevel(self)
        importwindow.title(_("Import"))
        importwindow.geometry(self.popup_geometry(280, 300))
        importwindow.resizable(False, False)
        importwindow.grab_set()
        importwindow.focus()
        importwindow.bind('<Escape>', lambda event: importwindow.destroy())

        try:
            importwindow.iconbitmap('asset/icon.ico')
        except tk.TclError:
            pass

        bottomframe_imp = tk.Frame(importwindow)
        bottomframe_imp.pack(side='bottom')

        import_label = tk.Label(importwindow, text=_('Select accounts to import.') + '\n' +
                                _("Added accounts don't show up."))
        import_label.pack(side='top', padx=5, pady=5)

        def close():
            importwindow.destroy()

        def disable_close():
            pass

        def onFrameConfigure(canvas):
            '''Reset the scroll region to encompass the inner frame'''
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas = tk.Canvas(importwindow, borderwidth=0, highlightthickness=0)
        check_frame = tk.Frame(canvas)
        scroll_bar = ttk.Scrollbar(importwindow, orient="vertical", command=canvas.yview,)

        canvas.configure(yscrollcommand=scroll_bar.set)

        scroll_bar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((4, 4), window=check_frame, anchor="nw")

        check_frame.bind("<Configure>", lambda event,
                         canvas=canvas: onFrameConfigure(canvas))

        def _on_mousewheel(event):
            '''Scroll window on mousewheel input'''
            if 'disabled' not in scroll_bar.state():
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)

        checkbox_dict = {}

        for index, username in enumerate(account_name):
            if username not in self.accounts.list:
                int_var = tk.IntVar()
                checkbutton = ttk.Checkbutton(check_frame,
                                              text=username + f' ({persona_name[index]})',
                                              variable=int_var,
                                              style='Import.TCheckbutton')
                checkbutton.bind("<MouseWheel>", _on_mousewheel)
                checkbutton.pack(side='top', padx=2, anchor='w')
                checkbox_dict[username] = int_var

        def import_user():
            dl_list = []
            accounts_to_add = []

            for key, value in checkbox_dict.items():
                if value.get() == 1:
                    accounts_to_add.append(key)
                    dl_list.append(steam64_list[account_name.index(key)])

            if accounts_to_add:
                self.accounts.add_multiple_accounts(accounts_to_add)

            if get_config('show_avatar') == 'true':
                canvas.destroy()
                import_label.destroy()
                scroll_bar.destroy()
                import_cancel['state'] = 'disabled'
                import_ok['state'] = 'disabled'
                importwindow.protocol("WM_DELETE_WINDOW", disable_close)
                importwindow.focus()

                tk.Label(importwindow, text=_('Please wait while downloading avatars...')).pack(fill='both', expand=True)
                self.update()
                download_avatar(dl_list)

            self.refresh()
            close()

        import_cancel = ttk.Button(bottomframe_imp,
                                   text=_('Cancel'),
                                   command=close,
                                   width=9)
        import_ok = ttk.Button(bottomframe_imp,
                               text=_('Import'),
                               command=import_user,
                               width=9,
                               style="Accent.TButton")

        import_cancel.pack(side='left', padx=5, pady=3)
        import_ok.pack(side='left', padx=5, pady=3)

    def orderwindow(self):
        '''Open order change window'''
        if not self.accounts:
            msgbox.showinfo(_('No Accounts'),
                            _("There's no account added."))
            return

        x, y = self.get_window_pos()

        orderwindow = tk.Toplevel(self)
        orderwindow.title("")
        orderwindow.geometry(self.popup_geometry(230, 270))
        orderwindow.resizable(False, False)
        orderwindow.bind('<Escape>', lambda event: orderwindow.destroy())

        try:
            orderwindow.iconbitmap('asset/icon.ico')
        except tk.TclError:
            pass

        bottomframe = tk.Frame(orderwindow)
        bottomframe.pack(side='bottom', padx=3, pady=3)

        labelframe = tk.Frame(orderwindow)
        labelframe.pack(side='bottom', padx=3)

        orderwindow.grab_set()
        orderwindow.focus()

        lbframe = tk.Frame(orderwindow)

        scrollbar = ttk.Scrollbar(lbframe)
        scrollbar.pack(side='right', fill='y')

        lb = DragDropListbox(lbframe, width=35, height=20,
                             highlightthickness=0,
                             yscrollcommand=scrollbar.set,
                             bd=1,
                             relief='solid')

        scrollbar["command"] = lb.yview

        def _on_mousewheel(event):
            '''Scroll window on mousewheel input'''
            lb.yview_scroll(int(-1*(event.delta/120)), "units")

        lb.bind("<MouseWheel>", _on_mousewheel)
        lb.pack(side='left')

        for i, v in enumerate(self.accounts.list):
            lb.insert(i, v)

        lb.select_set(0)
        lbframe.pack(side='top', padx=3, pady=(3, 5), expand=True)

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

            self.accounts.change_dict_order(order)
            self.refresh()

        def close():
            orderwindow.destroy()

        def ok():
            apply()
            close()

        button_ok = ttk.Button(bottomframe,
                               width=9, text=_('OK'), command=ok, style="Accent.TButton")
        button_cancel = ttk.Button(bottomframe,
                                   width=9, text=_('Cancel'), command=close)

        button_up = ttk.Button(bottomframe, width=3,
                               text='↑', command=up)

        button_down = ttk.Button(bottomframe, width=3,
                                 text='↓', command=down)

        button_ok.grid(row=0, column=0, padx=(3, 0), pady=3, sticky='nesw')
        button_cancel.grid(row=0, column=1, padx=3, pady=3, sticky='nesw')
        button_up.grid(row=0, column=2, padx=3, pady=3, sticky='nesw')
        button_down.grid(row=0, column=3, padx=(0, 3), pady=3, sticky='nesw')

        bottomframe.grid_columnconfigure(0, weight=1)
        bottomframe.grid_columnconfigure(1, weight=1)
        bottomframe.grid_columnconfigure(2, weight=1)
        bottomframe.grid_columnconfigure(3, weight=1)
        bottomframe.grid_rowconfigure(0, weight=1)

    def settingswindow(self):
        '''Open settings window'''
        global image1
        global image2
        global image3
        global image4

        config_dict = get_config('all')
        last_config = config_dict

        if LOCALE == 'fr_FR':
            width = 330
            ui_padx = 70
            theme_padx = 50
        else:
            width = 280
            ui_padx = 35
            theme_padx = 40

        settingswindow = tk.Toplevel(self)
        settingswindow.title(_("Settings"))
        settingswindow.geometry(self.popup_geometry(width, 520))  # 260 is original
        settingswindow.resizable(False, False)
        settingswindow.bind('<Escape>', lambda event: settingswindow.destroy())

        try:
            settingswindow.iconbitmap('asset/icon.ico')
        except tk.TclError:
            pass

        bottomframe_set = tk.Frame(settingswindow)
        bottomframe_set.pack(side='bottom')
        settingswindow.grab_set()
        settingswindow.focus()

        if LOCALE == 'fr_FR':
            padx_int = 45
        elif LOCALE == 'en_US':
            padx_int = 11
        else:
            padx_int = 24

        localeframe = tk.Frame(settingswindow)
        localeframe.pack(side='top', pady=(14, 7), fill='x')
        locale_label = tk.Label(localeframe, text=_('Language'))
        locale_label.pack(side='left', padx=(padx_int, 13))
        locale_cb = ttk.Combobox(localeframe,
                                 state="readonly",
                                 values=['English',  # 0
                                         '한국어 (Korean)',  # 1
                                         'Français (French)'])  # 2

        current_locale = config_dict['locale']

        if current_locale == 'en_US':
            locale_cb.current(0)
        elif current_locale == 'ko_KR':
            locale_cb.current(1)
        elif current_locale == 'fr_FR':
            locale_cb.current(2)

        locale_cb.pack(side='left')

        restart_frame = tk.Frame(settingswindow)
        restart_frame.pack(side='top')

        ui_frame = tk.Frame(settingswindow)
        ui_frame.pack(side='top', pady=(5, 5), fill='x')
        ui_radio_var = tk.IntVar()

        list_radio_frame = tk.Frame(ui_frame)
        list_radio_frame.pack(side='left', padx=(ui_padx, 0))

        if get_config('theme') == 'light':
            list_img = Image.open("asset/list.png").resize((30, 30))
            grid_img = Image.open("asset/grid.png").resize((30, 30))
        else:
            list_img = Image.open("asset/list_white.png").resize((30, 30))
            grid_img = Image.open("asset/grid_white.png").resize((30, 30))

        list_canvas = tk.Canvas(list_radio_frame, width=30, height=30, bd=0, highlightthickness=0)

        image1 = ImageTk.PhotoImage(list_img)
        list_canvas.create_image(15, 15, image=image1)
        list_canvas.pack(side='top', padx=0, pady=5)

        radio_list = ttk.Radiobutton(list_radio_frame,
                                     text=_('List Mode'),
                                     variable=ui_radio_var,
                                     value=0)
        radio_list.pack(side='top', pady=2)
        ToolTipWindow(radio_list, _('Display accounts in vertical list.'), center=True)

        grid_radio_frame = tk.Frame(ui_frame)
        grid_radio_frame.pack(side='right', padx=(0, ui_padx))

        grid_canvas = tk.Canvas(grid_radio_frame, width=30, height=30, bd=0, highlightthickness=0)

        image2 = ImageTk.PhotoImage(grid_img)
        grid_canvas.create_image(15, 15, image=image2)
        grid_canvas.pack(side='top', padx=0, pady=5)

        radio_grid = ttk.Radiobutton(grid_radio_frame,
                                     text=_('Grid Mode'),
                                     variable=ui_radio_var,
                                     value=1)
        radio_grid.pack(side='top', pady=2)
        ToolTipWindow(radio_grid, _('Display accounts in 3 x n grid.'), center=True)

        if get_config('ui_mode') == 'grid':
            ui_radio_var.set(1)

        avatar_frame = tk.Frame(settingswindow)
        avatar_frame.pack(fill='x', side='top', padx=12, pady=(2, 5))

        avatar_chkb = ttk.Checkbutton(avatar_frame, text=_('Show avatar images'))

        avatar_chkb.state(['!alternate'])

        if config_dict['show_avatar'] == 'true':
            avatar_chkb.state(['selected'])
        else:
            avatar_chkb.state(['!selected'])

        avatar_chkb.pack(side='top')

        def on_list_check():
            avatar_chkb.state(['!disabled'])

        def on_grid_check():
            avatar_chkb.state(['selected'])
            avatar_chkb.state(['disabled'])

        if ui_radio_var.get() == 1:
            on_grid_check()

        radio_list['command'] = on_list_check
        radio_grid['command'] = on_grid_check

        theme_frame = tk.Frame(settingswindow)
        theme_frame.pack(side='top', pady=(5, 5), fill='x')
        theme_radio_var = tk.IntVar()

        light_radio_frame = tk.Frame(theme_frame)
        light_radio_frame.pack(side='left', padx=(theme_padx, 0))

        light_canvas = tk.Canvas(light_radio_frame, width=40, height=64, bd=0, highlightthickness=0)
        light_img = Image.open("asset/light.png").resize((40, 64))

        image3 = ImageTk.PhotoImage(light_img)
        light_canvas.create_image(20, 32, image=image3)
        light_canvas.pack(side='top', padx=0, pady=5)

        radio_light = ttk.Radiobutton(light_radio_frame,
                                      text=_('Light Theme'),
                                      variable=theme_radio_var,
                                      value=0)
        radio_light.pack(side='top', pady=2)

        dark_radio_frame = tk.Frame(theme_frame)
        dark_radio_frame.pack(side='right', padx=(0, theme_padx))

        dark_canvas = tk.Canvas(dark_radio_frame, width=40, height=64, bd=0, highlightthickness=0)
        dark_img = Image.open("asset/dark.png").resize((40, 64))

        image4 = ImageTk.PhotoImage(dark_img)
        dark_canvas.create_image(20, 32, image=image4)
        dark_canvas.pack(side='top', padx=0, pady=5)

        radio_dark = ttk.Radiobutton(dark_radio_frame,
                                     text=_('Dark Theme'),
                                     variable=theme_radio_var,
                                     value=1,
                                     style='Settings.TRadiobutton')
        radio_dark.pack(side='top', pady=2)

        if get_config('theme') == 'dark':
            theme_radio_var.set(1)

        mode_radio_frame1 = tk.Frame(settingswindow)
        mode_radio_frame1.pack(side='top', padx=12, pady=(7, 2), fill='x')
        mode_radio_frame2 = tk.Frame(settingswindow)
        mode_radio_frame2.pack(side='top', padx=12, pady=(2, 7), fill='x')
        mode_radio_var = tk.IntVar()

        radio_normal = ttk.Radiobutton(mode_radio_frame1,
                                       text=_('Normal Mode (Manually restart Steam)'),
                                       variable=mode_radio_var,
                                       value=0,
                                       style='Settings.TRadiobutton')
        radio_normal.pack(side='left', pady=2)
        ToolTipWindow(radio_normal, _("Restart Steam by clicking on 'Restart Steam' button."))

        radio_express = ttk.Radiobutton(mode_radio_frame2,
                                        text=_('Express Mode (Auto-restart Steam)'),
                                        variable=mode_radio_var,
                                        value=1,
                                        style='Settings.TRadiobutton')
        radio_express.pack(side='left', pady=2)
        ToolTipWindow(radio_express, _("Automatically restart Steam when autologin account is changed."))
        if get_config('mode') == 'express':
            mode_radio_var.set(1)

        softshutdwn_frame = tk.Frame(settingswindow)
        softshutdwn_frame.pack(fill='x', side='top', padx=12, pady=(7, 5))

        soft_chkb = ttk.Checkbutton(softshutdwn_frame, style="Switch.TCheckbutton",
                                    text=_('Try to soft shutdown Steam client'))

        soft_chkb.state(['!alternate'])

        if config_dict['try_soft_shutdown'] == 'true':
            soft_chkb.state(['selected'])
        else:
            soft_chkb.state(['!selected'])

        soft_chkb.pack(side='left')

        autoexit_frame = tk.Frame(settingswindow)
        autoexit_frame.pack(fill='x', side='top', padx=12, pady=5)

        autoexit_chkb = ttk.Checkbutton(autoexit_frame, style="Switch.TCheckbutton",
                                        text=_('Exit app after Steam is restarted'))

        autoexit_chkb.state(['!alternate'])

        if config_dict['autoexit'] == 'true':
            autoexit_chkb.state(['selected'])
        else:
            autoexit_chkb.state(['!selected'])

        autoexit_chkb.pack(side='left')

        def open_manage_encryption_window():
            enc_window = ManageEncryptionWindow(self.popup_geometry(320, 300, multiplier=2), self.accounts)

            def event_function(event):
                if str(event.widget) == '.!manageencryptionwindow':
                    settingswindow.grab_set()

            enc_window.bind('<Destroy>', event_function)
            enc_window.grab_set()

        manage_encryption_button = ttk.Button(settingswindow,
                                              text=_('Manage Encryption Settings'),
                                              command=open_manage_encryption_window)
        manage_encryption_button.pack(side='bottom', fill='x', padx=3)

        def close():
            settingswindow.destroy()

        def apply():
            nonlocal config_dict
            nonlocal current_locale
            '''Write new config values to config.txt'''
            locale = ('en_US', 'ko_KR', 'fr_FR')

            if ui_radio_var.get() == 1:
                ui_mode = 'grid'
            else:
                ui_mode = 'list'

            if theme_radio_var.get() == 1:
                theme = 'dark'
                if sv_ttk.get_theme() != 'dark':
                    sv_ttk.use_dark_theme()
            else:
                theme = 'light'
                if sv_ttk.get_theme() != 'light':
                    sv_ttk.use_light_theme()

            if mode_radio_var.get() == 1:
                mode = 'express'
            else:
                mode = 'normal'

            if 'selected' in soft_chkb.state():
                soft_shutdown = 'true'
            else:
                soft_shutdown = 'false'

            if 'selected' in autoexit_chkb.state():
                autoexit = 'true'
            else:
                autoexit = 'false'

            if 'selected' in avatar_chkb.state():
                avatar = 'true'
            else:
                avatar = 'false'

            config_dict = {'locale': locale[locale_cb.current()],
                           'autoexit': autoexit,
                           'mode': mode,
                           'try_soft_shutdown': soft_shutdown,
                           'show_avatar': avatar,
                           'last_pos': get_config('last_pos'),
                           'steam_path': get_config('steam_path'),
                           'ui_mode': ui_mode,
                           'theme': theme,
                           'encryption': get_config('encryption')}

            config_write_dict(config_dict)

            if last_config['show_avatar'] == 'false' and 'selected' in avatar_chkb.state():
                if msgbox.askyesno('', _('Do you want to download avatar images now?')):
                    self.update_avatar(no_ui=True)

            if current_locale != locale[locale_cb.current()]:
                self.after(100, lambda: msgbox.showinfo(_('Language has been changed'),
                                                        _('Restart app to apply new language settings.')))
                current_locale = locale[locale_cb.current()]

            self.refresh()

        def ok():
            apply()
            close()

        settings_ok = ttk.Button(bottomframe_set,
                                 text=_('OK'),
                                 command=ok,
                                 width=10,
                                 style="Accent.TButton")

        settings_cancel = ttk.Button(bottomframe_set,
                                     text=_('Cancel'),
                                     command=close,
                                     width=10)

        settings_apply = ttk.Button(bottomframe_set,
                                    text=_('Apply'),
                                    command=apply,
                                    width=10)

        settings_ok.grid(row=0, column=0, padx=(3, 0), pady=3, sticky='nesw')
        settings_cancel.grid(row=0, column=1, padx=3, pady=3, sticky='nesw')
        settings_apply.grid(row=0, column=2, padx=(0, 3), pady=3, sticky='nesw')

        bottomframe_set.grid_columnconfigure(0, weight=1)
        bottomframe_set.grid_columnconfigure(1, weight=1)
        bottomframe_set.grid_columnconfigure(2, weight=1)
        bottomframe_set.grid_rowconfigure(0, weight=1)

    def exit_after_restart(self, refresh_override=False):
        '''Restart Steam client and exit application.
        If autoexit is disabled, app won't exit.'''
        if remember_password_disabled(self.user_var.get()):
            if msgbox.askyesno(_('Remember Password Disabled'),
                               _('Remember Password is disabled for this account.\n'
                                 'Do you want to enable it now?')):
                set_loginusers_value(self.user_var.get(), 'RememberPassword', '1')

        label_var = tk.StringVar()

        if get_config('steam_path') == 'reg':
            r_path = fetch_reg('SteamExe')
            r_path_items = r_path.split('/')
        else:
            r_path = get_config('steam_path') + '\\Steam.exe'
            r_path_items = r_path.split('\\')

        path_items = []
        for item in r_path_items:
            if ' ' in item:
                path_items.append(f'"{item}"')
            else:
                path_items.append(item)

        steam_exe = "\\".join(path_items)
        print('Steam.exe path:', steam_exe)

        def forcequit():
            print('Hard shutdown mode')
            subprocess.run("TASKKILL /F /IM Steam.exe",
                           creationflags=0x08000000, check=True)
            print('TASKKILL command sent.')

        self.no_user_frame.destroy()
        self.button_frame.destroy()
        hide_update()
        self.unbind('<MouseWheel>')
        self.bottomframe.pack_forget()
        button_frame = tk.Frame(self, bg=get_color('upperframe'))
        button_frame.pack(side='bottom', fill='x')
        cancel_button = SimpleButton(button_frame,
                                     text=_('Cancel'))
        force_button = SimpleButton(button_frame,
                                    text=_('Force quit Steam'),
                                    command=forcequit)
        cancel_button.disable(no_fade=True)
        force_button.disable(no_fade=True)

        def enable_button():
            cancel_button.enable()
            force_button.enable()

        cancel_button.pack(side='bottom', padx=3, pady=3, fill='x')
        force_button.pack(side='bottom', padx=3, pady=(3,0), fill='x')

        label_var = tk.StringVar()
        label_var.set(_('Initializing...'))
        label = tk.Label(self, textvariable=label_var, bg=self['bg'], fg=get_color('text'))
        label.pack(pady=(150, 0))

        def cleanup():
            label.destroy()
            button_frame.destroy()
            self.refresh(no_frame=True)
            self.bottomframe.pack(side='bottom', fill='x')
            show_update()

        self.update()
        queue = q.Queue()

        # This is absolute spaghetti... Really need to rewrite it someday.

        if steam_running():
            label_var.set(_('Waiting for Steam to exit...'))

            if get_config('try_soft_shutdown') == 'false':
                forcequit()
            elif get_config('try_soft_shutdown') == 'true':
                print('Soft shutdown mode')
                subprocess.run(f"start {steam_exe} -shutdown", shell=True,
                               creationflags=0x08000000, check=True)
                print('Shutdown command sent. Waiting for Steam...')

            checker_task = None

            def steam_checker():
                nonlocal queue
                nonlocal thread

                if thread.stopped():
                    return
                if steam_running():
                    self.after(1000, steam_checker)
                else:
                    queue.put(1)
                    return

            def cancel():
                thread.stop()
                cleanup()
                return

            thread = StoppableThread(target=steam_checker)
            thread.start()
            cancel_button.update_command(cancel)
        else:
            queue.put(1)

        counter = 0

        def launch_steam():
            nonlocal queue
            nonlocal counter
            nonlocal thread

            def after_steam_start():
                if get_config('autoexit') == 'true':
                    self.exit_app()
                elif not refresh_override:
                    cleanup()

            try:
                queue.get_nowait()
                queue = q.Queue()

                label_var.set(_('Launching Steam...'))
                self.update()

                print('Launching Steam...')

                username = fetch_reg('AutoLoginUser')
                password = self.accounts.get_password(username)

                if password:
                    def active_user_checker():
                        nonlocal queue

                        if not steam_running():
                            self.after(1000, active_user_checker)
                        elif not fetch_reg('ActiveUser'):
                            self.after(1000, active_user_checker)
                        else:
                            queue.put(1)
                            print('Steam log-in success')
                            return

                    def cancel():
                        nonlocal listener

                        self.after_cancel(active_user_checker_thread)
                        self.after_cancel(active_user_waiter)
                        listener.stop()
                        after_steam_start()

                    def for_canonical(f):
                        return lambda k: f(listener.canonical(k))

                    clipboard_eraser_task = None

                    def copy_pw():
                        nonlocal clipboard_eraser_task

                        win32clipboard.OpenClipboard()
                        win32clipboard.EmptyClipboard()
                        win32clipboard.SetClipboardText(self.accounts.get_password(self.user_var.get()))
                        win32clipboard.CloseClipboard()

                        if clipboard_eraser_task:
                            self.after_cancel(clipboard_eraser_task)
                        clipboard_eraser_task = self.after(1000, empty_clipboard)

                    def empty_clipboard():
                        win32clipboard.OpenClipboard()
                        win32clipboard.EmptyClipboard()
                        win32clipboard.CloseClipboard()

                    hotkey = keyboard.HotKey(
                        keyboard.HotKey.parse('<ctrl>+v'),
                        copy_pw)

                    listener = keyboard.Listener(
                        on_press=for_canonical(hotkey.press),
                        on_release=for_canonical(hotkey.release))
                    listener.start()

                    subprocess.run("start steam://open/main",
                                   shell=True, check=True)

                    active_user_checker_thread = self.after(3000, active_user_checker)

                    label_var.set(_('Waiting for log in...\n\nPress Ctrl+V to paste password.'))
                    print('Log in checker thread will start in 3 seconds.')

                    force_button.pack_forget()

                    cancel_button.update_command(cancel)
                    cancel_button.enable()

                    if get_config('autoexit') == 'true':
                        cancel_button.update_text(_('Exit'))

                    active_user_waiter = None

                    def waiter():
                        nonlocal active_user_waiter
                        nonlocal listener

                        try:
                            queue.get_nowait()
                            listener.stop()
                            after_steam_start()
                        except q.Empty:
                            active_user_waiter = self.after(1000, waiter)

                    active_user_waiter = self.after(1000, waiter)


                else:
                    subprocess.run("start steam://open/main",
                                   shell=True, check=True)
                    after_steam_start()

            except q.Empty:
                counter += 1
                if counter == 10:
                    enable_button()
                self.after(1000, launch_steam)

        self.after(2000, launch_steam)
