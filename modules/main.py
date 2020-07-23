import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox as msgbox
import gettext
import winreg
import subprocess
import os
import sys
import queue as q
from time import sleep
from ruamel.yaml import YAML
from modules.account import acc_getlist, acc_getdict, loginusers
from modules.reg import fetch_reg, setkey
from modules.config import get_config, config_write_dict
from modules.util import check_running, steam_running, StoppableThread, open_screenshot, raise_exception, test
from modules.update import start_checkupdate, hide_update, show_update
from modules.ui import DragDropListbox, AccountButton, WelcomeWindow, steamid_window, ask_steam_dir
from modules.avatar import download_avatar

yaml = YAML()

LOCALE = get_config('locale')

t = gettext.translation('steamswitcher',
                        localedir='locale',
                        languages=[LOCALE],
                        fallback=True)
_ = t.gettext


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
    def __init__(self, version, url, bundle, std_out, std_err):
        sys.stdout = std_out
        sys.stderr = std_err
        self.accounts = acc_getlist()
        self.acc_dict = acc_getdict()
        self.demo_mode = False
        tk.Tk.__init__(self)
        self['bg'] = 'white'
        self.title(_("Account Switcher"))

        self.geometry("300x472+600+250")
        self.resizable(False, False)

        try:
            self.iconbitmap('asset/icon.ico')
        except tk.TclError:
            pass

        if not test():
            ask_steam_dir()

        menubar = tk.Menu(self, bg='white')
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
        menu.add_command(label=_("About"),
                         command=lambda: self.about(version))

        menubar.add_cascade(label=_("Menu"), menu=menu)
        self.config(menu=menubar)

        if not bundle:
            debug_menu = tk.Menu(menubar, tearoff=0)
            debug_menu.add_command(label='Check for updates with debug mode',
                                   command=lambda: self.after(10, lambda: start_checkupdate(self, version, url, bundle, debug=True)))
            debug_menu.add_command(label='Check for updates without debug mode',
                                   command=lambda: self.after(10, lambda: start_checkupdate(self, version, url, True)))
            debug_menu.add_command(label='Check for updates (with exception)',
                                   command=lambda: self.after(10, lambda: start_checkupdate(self, version, url, True, exception=True)))
            debug_menu.add_command(label="Download avatar images",
                                   command=download_avatar)
            debug_menu.add_command(label="Open initial setup",
                                   command=self.welcomewindow)
            debug_menu.add_command(label="Toggle demo mode",
                                   command=self.toggle_demo)
            debug_menu.add_command(label="Raise exception",
                                   command=raise_exception)
            menubar.add_cascade(label=_("Debug"), menu=debug_menu)

        self.bottomframe = tk.Frame(self, bg='white')
        self.bottomframe.pack(side='bottom')

        def toggleAutologin():
            '''Toggle autologin registry value between 0 and 1'''
            if fetch_reg('RememberPassword') == 1:
                value = 0
            elif fetch_reg('RememberPassword') == 0:
                value = 1
            setkey('RememberPassword', value, winreg.REG_DWORD)

            if fetch_reg('RememberPassword') == 1:
                self.auto_var.set(_('Auto-login Enabled'))
                self.autolabel['fg'] = 'green'
            else:
                self.auto_var.set(_('Auto-login Disabled'))
                self.autolabel['fg'] = 'red'

        if LOCALE == 'fr_FR':
            toggle_width = 13
            quit_width = 7
        else:
            toggle_width = 15
            quit_width = 5

        button_toggle = ttk.Button(self.bottomframe,
                                   width=toggle_width,
                                   text=_('Toggle auto-login'),
                                   command=toggleAutologin)

        button_quit = ttk.Button(self.bottomframe,
                                 width=quit_width,
                                 text=_('Exit'),
                                 command=self.quit)

        self.restartbutton_text = tk.StringVar()

        if get_config('autoexit') == 'true':
            self.restartbutton_text.set(_('Restart Steam & Exit'))
        else:
            self.restartbutton_text.set(_('Restart Steam'))

        button_restart = ttk.Button(self.bottomframe,
                                    width=20,
                                    textvariable=self.restartbutton_text,
                                    command=self.exit_after_restart)

        button_toggle.pack(side='left', padx=3, pady=3)
        button_quit.pack(side='left', pady=3)
        button_restart.pack(side='right', padx=3, pady=3)

        self.button_dict = {}

        upper_frame = tk.Frame(self, bg='white')
        upper_frame.pack(side='top', fill='x')

        self.button_frame = tk.Frame(self, bg='white')
        self.button_frame.pack(side='top', fill='both', expand=True)

        userlabel_1 = tk.Label(upper_frame, text=_('Current Auto-login user:'), bg='white')
        userlabel_1.pack(side='top')

        self.user_var = tk.StringVar()
        self.user_var.set(fetch_reg('AutoLoginUser'))

        userlabel_2 = tk.Label(upper_frame, textvariable=self.user_var, bg='white')
        userlabel_2.pack(side='top', pady=2)

        self.auto_var = tk.StringVar()

        if fetch_reg('RememberPassword') == 1:
            self.auto_var.set(_('Auto-login Enabled'))
            auto_color = 'green'
        else:
            self.auto_var.set(_('Auto-login Disabled'))
            auto_color = 'red'

        self.autolabel = tk.Label(upper_frame, textvariable=self.auto_var, bg='white', fg=auto_color)
        self.autolabel.pack(side='top')
        ttk.Separator(upper_frame, orient='horizontal').pack(fill='x')

        self.draw_button()

    def toggle_demo(self):
        if self.demo_mode:
            self.demo_mode = False
        else:
            self.demo_mode = True

        self.refresh()

    def welcomewindow(self):
        window = WelcomeWindow(self)

        def event_function(event):
            if str(event.widget) == '.!welcomewindow':
                if self.accounts:
                    download_avatar()
                self.refresh()

        window.bind('<Destroy>', event_function)

    def configwindow(self, username, profilename):
        configwindow = tk.Toplevel(self, bg='white')
        configwindow.title('')
        configwindow.geometry("240x150+650+320")
        configwindow.resizable(False, False)

        i = self.accounts.index(username)
        try:
            custom_name = self.acc_dict[i]['customname']
        except KeyError:
            custom_name = ''

        button_frame = tk.Frame(configwindow, bg='white')
        button_frame.pack(side='bottom', pady=3)

        ok_button = ttk.Button(button_frame, text=_('OK'))
        ok_button.pack(side='right', padx=1.5)

        cancel_button = ttk.Button(button_frame,
                                   text=_('Cancel'),
                                   command=configwindow.destroy)
        cancel_button.pack(side='left', padx=1.5)

        top_label = tk.Label(configwindow, text=_('Select name settings for %s') % username, bg='white')
        top_label.pack(side='top', pady=(4, 3))

        radio_frame1 = tk.Frame(configwindow, bg='white')
        radio_frame1.pack(side='top', padx=20, pady=(4, 2), fill='x')
        radio_frame2 = tk.Frame(configwindow, bg='white')
        radio_frame2.pack(side='top', padx=20, pady=(0, 3), fill='x')
        radio_var = tk.IntVar()

        if custom_name.strip():
            radio_var.set(1)
        else:
            radio_var.set(0)

        s = ttk.Style()
        s.configure('config.TRadiobutton', background='white')

        radio_default = ttk.Radiobutton(radio_frame1,
                                        text=_('Use profile name if available'),
                                        variable=radio_var,
                                        value=0,
                                        style='config.TRadiobutton')
        radio_custom = ttk.Radiobutton(radio_frame2,
                                       text=_('Use custom name'),
                                       variable=radio_var,
                                       value=1,
                                       style='config.TRadiobutton')

        radio_default.pack(side='left', pady=2)
        radio_custom.pack(side='left', pady=2)

        entry_frame = tk.Frame(configwindow, bg='white')
        entry_frame.pack(side='bottom', pady=(1, 4))

        name_entry = tk.Entry(entry_frame, width=26, disabledbackground='#C6C6C6', relief='solid')
        name_entry.insert(0, custom_name)
        name_entry.pack()

        configwindow.grab_set()
        configwindow.focus()

        if radio_var.get() == 0:
            name_entry['state'] = 'disabled'
            name_entry.focus()

        def reset_entry():
            name_entry.delete(0, 'end')
            name_entry['state'] = 'disabled'

        def enable_entry():
            name_entry['state'] = 'normal'
            name_entry.focus()

        radio_default['command'] = reset_entry
        radio_custom['command'] = enable_entry

        def ok(username):
            if name_entry.get().strip() and radio_var.get() == 1:
                input_name = name_entry.get()
                self.acc_dict[i]['customname'] = input_name
                print(f"Using custom name '{input_name}' for '{username}'.")
            elif radio_var.get() == 1:
                msgbox.showwarning(_('Info'), _('Enter a custom name to use.'), parent=configwindow)
                return
            else:
                if self.acc_dict[i].pop('customname', None):
                    print(f"Custom name for '{username}' has been removed.")

            with open('accounts.yml', 'w', encoding='utf-8') as f:
                yaml.dump(self.acc_dict, f)
            self.refresh()
            configwindow.destroy()

        def enterkey(event):
            ok(username)

        configwindow.bind('<Return>', enterkey)
        ok_button['command'] = lambda username=username: ok(username)
        configwindow.wait_window()

    def button_func(self, username):
        current_user = fetch_reg('AutoLoginUser')

        try:
            self.button_dict[current_user].enable()
        except Exception:
            pass

        setkey('AutoLoginUser', username, winreg.REG_SZ)
        self.button_dict[username].disable()
        self.user_var.set(fetch_reg('AutoLoginUser'))
        self.focus()

        if get_config('mode') == 'express':
            self.exit_after_restart()

    def remove_user(self, target):
        '''Write accounts to accounts.yml except the
        one which user wants to delete'''
        if msgbox.askyesno(_('Confirm'), _('Are you sure want to remove account %s?') % target):
            acc_dict = acc_getdict()
            accounts = acc_getlist()
            dump_dict = {}

            print(f'Removing {target}...')
            for username in accounts:
                if username != target:
                    dump_dict[len(dump_dict)] = acc_dict[accounts.index(username)]

            with open('accounts.yml', 'w') as acc:
                yaml.dump(dump_dict, acc)
            self.refresh()

    def draw_button(self):
        menu_dict = {}
        self.no_user_frame = tk.Frame(self.button_frame, bg='white')

        def onFrameConfigure(canvas):
            canvas.configure(scrollregion=canvas.bbox("all"))

        if self.demo_mode:
            canvas = tk.Canvas(self.button_frame, borderwidth=0, highlightthickness=0)
            canvas.config(bg='white')
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
                ttk.Separator(buttonframe, orient='horizontal').pack(fill='x')

            scroll_bar.pack(side="right", fill="y")
            canvas.pack(side="left", fill='both', expand=True)
            h = 50 * 8
            canvas.create_window((0, 0), height=h, width=285, window=buttonframe, anchor="nw")
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
            canvas.config(bg='white')
            buttonframe = tk.Frame(canvas)
            scroll_bar = ttk.Scrollbar(self.button_frame,
                                       orient="vertical",
                                       command=canvas.yview)

            for username in self.accounts:
                steam64_list, account_name, persona_name = loginusers()

                if username in account_name:
                    i = account_name.index(username)
                else:
                    i = None

                try:
                    acc_index = self.accounts.index(username)
                    profilename = self.acc_dict[acc_index]['customname']

                except KeyError:  # No custom name set
                    if i is not None:  # i could be 0 so we can't use if i:
                        profilename = persona_name[i]
                    else:
                        profilename = _('Profile name not available')

                finally:
                    if i is not None:  # i could be 0 so we can't use if i:
                        steam64 = steam64_list[i]
                        image = steam64
                    else:
                        image = 'default'

                    profilename = profilename[:30]

                # We have to make a menu for every account! Sounds ridiculous? Me too.
                menu_dict[username] = tk.Menu(self, tearoff=0)
                menu_dict[username].add_command(label=_("Set as auto-login account"),
                                                command=lambda name=username: self.button_func(name))
                menu_dict[username].add_separator()

                if i is not None:  # i could be 0 so we can't use if i:
                    menu_dict[username].add_command(label=_('Open profile in browser'),
                                                    command=lambda steamid64=steam64: os.startfile(f'https://steamcommunity.com/profiles/{steamid64}'))
                    menu_dict[username].add_command(label=_('Open screenshots folder'),
                                                    command=lambda steamid64=steam64: open_screenshot(steamid64))
                    menu_dict[username].add_command(label=_('View SteamID'),
                                                    command=lambda username=username, steamid64=steam64: steamid_window(self, username, steamid64))
                    menu_dict[username].add_command(label=_('Update avatar'),
                                                    command=lambda steamid64=steam64: self.update_avatar(steamid_list=[steamid64]))
                    menu_dict[username].add_separator()

                menu_dict[username].add_command(label=_("Name settings"),
                                                command=lambda name=username, pname=profilename: self.configwindow(name, pname))
                menu_dict[username].add_command(label=_("Delete"),
                                                command=lambda name=username: self.remove_user(name))

                def popup(username, event):
                    menu_dict[username].tk_popup(event.x_root + 86, event.y_root + 13, 0)

                self.button_dict[username] = AccountButton(buttonframe,
                                                           username=username,
                                                           profilename=profilename,
                                                           command=lambda name=username: self.button_func(name),
                                                           rightcommand=lambda event, username=username: popup(username, event),
                                                           image=image)

                if username == fetch_reg('AutoLoginUser'):
                    self.button_dict[username].disable()

                self.button_dict[username].pack(fill='x')
                ttk.Separator(buttonframe, orient='horizontal').pack(fill='x')

            scroll_bar.pack(side="right", fill="y")
            canvas.pack(side="left", fill='both', expand=True)
            h = 50 * len(self.accounts)
            canvas.create_window((0, 0), height=h, width=285, window=buttonframe, anchor="nw")
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
            no_user = tk.Label(self.no_user_frame, text=_('No accounts added'), bg='white')
            self.unbind("<MouseWheel>")
            no_user.pack(pady=(150, 0))

    def refresh(self, no_frame=False):
        '''Refresh main window widgets'''
        self.accounts = acc_getlist()
        self.acc_dict = acc_getdict()

        if not no_frame:
            self.no_user_frame.destroy()
            self.button_frame.destroy()

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(side='top', fill='both', expand=True)

        if self.demo_mode:
            self.user_var.set('username1')
        else:
            self.user_var.set(fetch_reg('AutoLoginUser'))

        if self.demo_mode:
            self.auto_var.set(_('Auto-login Enabled'))
        elif fetch_reg('RememberPassword') == 1:
            self.auto_var.set(_('Auto-login Enabled'))
        else:
            self.auto_var.set(_('Auto-login Disabled'))

        self.draw_button()

        if get_config('autoexit') == 'true':
            self.restartbutton_text.set(_('Restart Steam & Exit'))
        else:
            self.restartbutton_text.set(_('Restart Steam'))

        print('Menu refreshed with %s account(s)' % len(self.accounts))

    def update_avatar(self, steamid_list=loginusers()[0]):
        self.no_user_frame.destroy()
        self.button_frame.destroy()
        hide_update()
        self.bottomframe.pack_forget()

        label = tk.Label(self, text=_('Please wait while downloading avatars...'), bg='white')
        label.pack(expand=True)
        self.update()
        download_avatar(steamid_list)

        label.destroy()
        self.refresh(no_frame=True)
        self.bottomframe.pack(side='bottom')
        show_update()

    def about(self, version):
        '''Open about window'''

        if LOCALE == 'fr_FR':
            width = '480'
        else:
            width = '360'

        aboutwindow = tk.Toplevel(self, bg='white')
        aboutwindow.title(_('About'))
        aboutwindow.geometry("%sx180+650+300" % width)
        aboutwindow.resizable(False, False)
        aboutwindow.focus()

        about_disclaimer = tk.Label(aboutwindow, bg='white',
                                    text=_('Warning: The developer of this application is not responsible for')
                                    + '\n' + _('data loss or any other damage from the use of this app.'))
        about_steam_trademark = tk.Label(aboutwindow, bg='white',
                                         text=_('STEAM is a registered trademark of Valve Corporation.'))
        copyright_label = tk.Label(aboutwindow, text='Copyright (c) sw2719 | All Rights Reserved\n' +
                                   'Licensed under the MIT License.', bg='white')
        ver = tk.Label(aboutwindow, bg='white',
                       text='Steam Account Switcher | Version ' + version)

        button_frame = tk.Frame(aboutwindow, bg='white')
        button_frame.pack(side='bottom', pady=5)

        button_exit = ttk.Button(button_frame,
                                 text=_('Close'),
                                 width=8,
                                 command=aboutwindow.destroy,)
        button_github = ttk.Button(button_frame,
                                   text=_('GitHub page'),
                                   command=lambda: os.startfile('https://github.com/sw2719/steam-account-switcher'))
        about_disclaimer.pack(pady=8)
        about_steam_trademark.pack()
        copyright_label.pack(pady=5)
        ver.pack()

        button_exit.pack(side='left', padx=2)
        button_github.pack(side='right', padx=2)

    def refreshwindow(self):
        '''Open remove accounts window'''
        accounts = acc_getlist()
        if not accounts:
            msgbox.showinfo(_('No Accounts'),
                            _("There's no account added."))
            return
        refreshwindow = tk.Toplevel(self, bg='white')
        refreshwindow.title(_("Refresh"))
        refreshwindow.geometry("230x320+650+300")
        refreshwindow.resizable(False, False)
        bottomframe_rm = tk.Frame(refreshwindow, bg='white')
        bottomframe_rm.pack(side='bottom')
        refreshwindow.grab_set()
        refreshwindow.focus()
        removelabel = tk.Label(refreshwindow, text=_('Select accounts to refresh.'), bg='white')
        removelabel.pack(side='top', padx=5, pady=5)

        def close():
            refreshwindow.destroy()

        def onFrameConfigure(canvas):
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas = tk.Canvas(refreshwindow, borderwidth=0, highlightthickness=0, bg='white')
        check_frame = tk.Frame(canvas, bg='white')
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

        s = ttk.Style()
        s.configure('check.TCheckbutton', background='white')

        for v in accounts:
            tk_var = tk.IntVar()
            checkbutton = ttk.Checkbutton(check_frame,
                                          text=v,
                                          variable=tk_var,
                                          style='check.TCheckbutton')
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

            popup = tk.Toplevel(self, bg='white')
            popup.title('')
            popup.geometry("180x100+650+300")
            popup.resizable(False, False)

            popup_var = tk.StringVar()
            popup_var.set(_('Initializing...'))

            popup_uservar = tk.StringVar()
            popup_uservar.set('---------')

            popup_label = tk.Label(popup, textvariable=popup_var, bg='white')
            popup_user = tk.Label(popup, textvariable=popup_uservar, bg='white')

            popup_label.pack(pady=17)
            popup_user.pack()

            self.update()

            if steam_running() and not check_running('steam.exe'):
                setkey('pid', 0, winreg.REG_DWORD, path=r"Software\Valve\Steam\ActiveProcess")

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
                                width=9)

        refresh_cancel.pack(side='left', padx=5, pady=3)
        refresh_ok.pack(side='left', padx=5, pady=3)

    def addwindow(self):
        '''Open add accounts window'''
        accounts = acc_getlist()
        acc_dict = acc_getdict()
        steamid_list, account_name, persona_name = loginusers()

        addwindow = tk.Toplevel(self, bg='white')
        addwindow.title(_("Add"))
        addwindow.geometry("300x150+650+300")
        addwindow.resizable(False, False)

        topframe_add = tk.Frame(addwindow, bg='white')
        topframe_add.pack(side='top', anchor='center')

        bottomframe_add = tk.Frame(addwindow, bg='white')
        bottomframe_add.pack(side='bottom', anchor='e')

        addlabel_row1 = tk.Label(topframe_add, bg='white',
                                 text=_('Enter account(s) to add.'))
        addlabel_row2 = tk.Label(topframe_add, bg='white',
                                 text=_("In case of adding multiple accounts,") + '\n' +
                                 _("seperate each account with '/' (slash)."))

        account_entry = ttk.Entry(bottomframe_add, width=29)

        addwindow.grab_set()
        addwindow.focus()
        account_entry.focus()

        def disable_close():
            pass

        def adduser(userinput):
            '''Write accounts from user's input to accounts.yml
            :param userinput: Account names to add
            '''
            nonlocal acc_dict
            dl_list = []

            if userinput.strip():
                name_buffer = userinput.split("/")
                accounts_to_add = [name.strip() for name in name_buffer if name.strip()]

                for name_to_write in accounts_to_add:
                    if name_to_write not in accounts:
                        acc_dict[len(acc_dict)] = {'accountname': name_to_write}

                        if name_to_write in account_name:
                            dl_list.append(steamid_list[account_name.index(name_to_write)])

                    else:
                        print(f'Account {name_to_write} already exists!')
                        msgbox.showinfo(_('Duplicate Alert'),
                                        _('Account %s already exists.')
                                        % name_to_write)
                with open('accounts.yml', 'w') as acc:
                    yaml = YAML()
                    yaml.dump(acc_dict, acc)

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
        button_add = ttk.Button(bottomframe_add, width=9, text=_('Add'),
                                command=lambda: adduser(account_entry.get()))
        button_addcancel = ttk.Button(addwindow, width=9,
                                      text=_('Cancel'), command=close)
        addlabel_row1.pack(pady=10)
        addlabel_row2.pack()

        account_entry.pack(side='left', padx=3, pady=3)
        button_add.pack(side='left', anchor='e', padx=3, pady=3)
        button_addcancel.pack(side='bottom', anchor='e', padx=3)

    def importwindow(self):
        '''Open import accounts window'''
        accounts = acc_getlist()
        acc_dict = acc_getdict()
        steamid_list, account_name, persona_name = loginusers()

        if set(account_name).issubset(set(acc_getlist())):
            msgbox.showinfo(_('Info'), _("There's no account left to add."))
            return

        s = ttk.Style()
        s.configure('Import.TCheckbutton', background='white')

        importwindow = tk.Toplevel(self, bg='white')
        importwindow.title(_("Import"))
        importwindow.geometry("280x300+650+300")
        importwindow.resizable(False, False)
        importwindow.grab_set()
        importwindow.focus()

        bottomframe_imp = tk.Frame(importwindow, bg='white')
        bottomframe_imp.pack(side='bottom')

        import_label = tk.Label(importwindow, text=_('Select accounts to import.') + '\n' +
                                _("Added accounts don't show up."),
                                bg='white')
        import_label.pack(side='top', padx=5, pady=5)

        def close():
            importwindow.destroy()

        def disable_close():
            pass

        def onFrameConfigure(canvas):
            '''Reset the scroll region to encompass the inner frame'''
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas = tk.Canvas(importwindow, borderwidth=0, highlightthickness=0, background='white')
        check_frame = tk.Frame(canvas, bg='white')
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
            if username not in accounts:
                int_var = tk.IntVar()
                checkbutton = ttk.Checkbutton(check_frame,
                                              text=username + f' ({persona_name[index]})',
                                              variable=int_var,
                                              style='Import.TCheckbutton')
                checkbutton.bind("<MouseWheel>", _on_mousewheel)
                checkbutton.pack(side='top', padx=2, anchor='w')
                checkbox_dict[username] = int_var

        def import_user():
            nonlocal acc_dict
            dl_list = []

            for key, value in checkbox_dict.items():
                if value.get() == 1:
                    acc_dict[len(acc_dict)] = {'accountname': key}
                    dl_list.append(steamid_list[account_name.index(key)])

            with open('accounts.yml', 'w') as acc:
                yaml = YAML()
                yaml.dump(acc_dict, acc)

            if get_config('show_avatar') == 'true':
                canvas.destroy()
                import_label.destroy()
                scroll_bar.destroy()
                import_cancel['state'] = 'disabled'
                import_ok['state'] = 'disabled'
                importwindow.protocol("WM_DELETE_WINDOW", disable_close)
                importwindow.focus()

                tk.Label(importwindow, text=_('Please wait while downloading avatars...'), bg='white').pack(fill='both', expand=True)
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
                               width=9)

        import_cancel.pack(side='left', padx=5, pady=3)
        import_ok.pack(side='left', padx=5, pady=3)

    def orderwindow(self):
        '''Open order change window'''
        accounts = acc_getlist()

        if not accounts:
            msgbox.showinfo(_('No Accounts'),
                            _("There's no account added."))
            return

        orderwindow = tk.Toplevel(self, bg='white')
        orderwindow.title("")
        orderwindow.geometry("210x270+650+300")
        orderwindow.resizable(False, False)

        bottomframe_windowctrl = tk.Frame(orderwindow, bg='white')
        bottomframe_windowctrl.pack(side='bottom', padx=3, pady=3)

        bottomframe_orderctrl = tk.Frame(orderwindow, bg='white')
        bottomframe_orderctrl.pack(side='bottom', padx=3, pady=3)

        labelframe = tk.Frame(orderwindow, bg='white')
        labelframe.pack(side='bottom', padx=3)

        orderwindow.grab_set()
        orderwindow.focus()

        lbframe = tk.Frame(orderwindow, bg='white')

        scrollbar = ttk.Scrollbar(lbframe)
        scrollbar.pack(side='right', fill='y')

        lb = DragDropListbox(lbframe, height=12, width=26,
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

        for i, v in enumerate(accounts):
            lb.insert(i, v)

        lb.select_set(0)
        lbframe.pack(side='top', pady=5)

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
            acc_dict = acc_getdict()
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
            self.refresh()

        def close():
            orderwindow.destroy()

        def ok():
            apply()
            close()

        button_up = ttk.Button(bottomframe_orderctrl,
                               text='↑', command=up)
        button_up.pack(side='left', padx=2)

        button_down = ttk.Button(bottomframe_orderctrl,
                                 text='↓', command=down)
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

    def settingswindow(self):
        '''Open settings window'''
        config_dict = get_config('all')
        last_config = config_dict

        if LOCALE == 'fr_FR':
            width = '330'
        else:
            width = '260'

        settingswindow = tk.Toplevel(self, bg='white')
        settingswindow.title(_("Settings"))
        settingswindow.geometry("%sx300+650+300" % width)  # 260 is original
        settingswindow.resizable(False, False)
        bottomframe_set = tk.Frame(settingswindow, bg='white')
        bottomframe_set.pack(side='bottom')
        settingswindow.grab_set()
        settingswindow.focus()

        if LOCALE == 'fr_FR':
            padx_int = 45
        elif LOCALE == 'en_US':
            padx_int = 11
        else:
            padx_int = 24

        localeframe = tk.Frame(settingswindow, bg='white')
        localeframe.pack(side='top', pady=14, fill='x')
        locale_label = tk.Label(localeframe, text=_('Language'), bg='white')
        locale_label.pack(side='left', padx=(padx_int, 13))
        locale_cb = ttk.Combobox(localeframe,
                                 state="readonly",
                                 values=['English',  # 0
                                         '한국어 (Korean)',  # 1
                                         'Français (French)'])  # 2
        if config_dict['locale'] == 'en_US':
            locale_cb.current(0)
        elif config_dict['locale'] == 'ko_KR':
            locale_cb.current(1)
        elif config_dict['locale'] == 'fr_FR':
            locale_cb.current(2)

        locale_cb.pack(side='left')

        restart_frame = tk.Frame(settingswindow, bg='white')
        restart_frame.pack(side='top')

        restart_label = tk.Label(restart_frame, bg='white',
                                 text=_('Restart app to apply language settings.'))
        restart_label.pack(pady=(1, 0))

        radio_frame1 = tk.Frame(settingswindow, bg='white')
        radio_frame1.pack(side='top', padx=12, pady=(13, 3), fill='x')
        radio_frame2 = tk.Frame(settingswindow, bg='white')
        radio_frame2.pack(side='top', padx=12, pady=(3, 12), fill='x')
        radio_var = tk.IntVar()

        if get_config('mode') == 'express':
            radio_var.set(1)

        s = ttk.Style()
        s.configure('Settings.TRadiobutton', background='white')
        s.configure('Settings.TCheckbutton', background='white')

        radio_normal = ttk.Radiobutton(radio_frame1,
                                       text=_('Normal Mode (Manually restart Steam)'),
                                       variable=radio_var,
                                       value=0,
                                       style='Settings.TRadiobutton')
        radio_normal.pack(side='left', pady=2)

        radio_express = ttk.Radiobutton(radio_frame2,
                                        text=_('Express Mode (Auto-restart Steam)'),
                                        variable=radio_var,
                                        value=1,
                                        style='Settings.TRadiobutton')
        radio_express.pack(side='left', pady=2)

        softshutdwn_frame = tk.Frame(settingswindow, bg='white')
        softshutdwn_frame.pack(fill='x', side='top', padx=12, pady=(1, 0))

        soft_chkb = ttk.Checkbutton(softshutdwn_frame, style='Settings.TCheckbutton',
                                    text=_('Try to soft shutdown Steam client'))

        soft_chkb.state(['!alternate'])

        if config_dict['try_soft_shutdown'] == 'true':
            soft_chkb.state(['selected'])
        else:
            soft_chkb.state(['!selected'])

        soft_chkb.pack(side='left')

        autoexit_frame = tk.Frame(settingswindow, bg='white')
        autoexit_frame.pack(fill='x', side='top', padx=12, pady=17)

        autoexit_chkb = ttk.Checkbutton(autoexit_frame, style='Settings.TCheckbutton',
                                        text=_('Exit app after Steam is restarted'))

        autoexit_chkb.state(['!alternate'])
        if config_dict['autoexit'] == 'true':
            autoexit_chkb.state(['selected'])
        else:
            autoexit_chkb.state(['!selected'])

        autoexit_chkb.pack(side='left')

        avatar_frame = tk.Frame(settingswindow, bg='white')
        avatar_frame.pack(fill='x', side='top', padx=12)

        avatar_chkb = ttk.Checkbutton(avatar_frame, style='Settings.TCheckbutton',
                                      text=_('Show avatar images'))

        avatar_chkb.state(['!alternate'])

        if config_dict['show_avatar'] == 'true':
            avatar_chkb.state(['selected'])
        else:
            avatar_chkb.state(['!selected'])

        avatar_chkb.pack(side='left')

        def close():
            settingswindow.destroy()

        def apply():
            nonlocal config_dict
            '''Write new config values to config.txt'''
            locale = ('en_US', 'ko_KR', 'fr_FR')

            if radio_var.get() == 1:
                mode = 'express'
            elif radio_var.get() == 0:
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
                           'try_soft_shutdown': soft_shutdown,
                           'autoexit': autoexit,
                           'mode': mode,
                           'show_avatar': avatar,
                           'steam_path': get_config('steam_path')}

            config_write_dict(config_dict)

            if last_config['show_avatar'] == 'false' and 'selected' in avatar_chkb.state():
                if msgbox.askyesno('', _('Do you want to download avatar images now?'), parent=settingswindow):
                    download_avatar(loginusers()[0])

            self.refresh()
            if last_config['locale'] != locale[locale_cb.current()]:
                self.after(100, lambda: msgbox.showinfo(_('Locale has been changed'),
                                                        _('Restart app to apply new locale settings.')))

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

    def exit_after_restart(self, refresh_override=False, silent=True):
        '''Restart Steam client and exit application.
        If autoexit is disabled, app won't exit.'''
        label_var = tk.StringVar()

        def forcequit():
            print('Hard shutdown mode')
            subprocess.run("TASKKILL /F /IM Steam.exe",
                           creationflags=0x08000000, check=True)
            print('TASKKILL command sent.')

        if not refresh_override:
            self.no_user_frame.destroy()
            self.button_frame.destroy()
            hide_update()
            self.bottomframe.pack_forget()
            button_frame = tk.Frame(self, bg='white')
            button_frame.pack(side='bottom', fill='x')
            cancel_button = ttk.Button(button_frame,
                                       text=_('Cancel'))
            cancel_button['state'] = 'disabled'
            force_button = ttk.Button(button_frame,
                                      text=_('Force quit Steam'),
                                      command=forcequit)
            force_button['state'] = 'disabled'

            def enable_button():
                cancel_button['state'] = 'normal'
                force_button['state'] = 'normal'

            cancel_button.pack(side='bottom', padx=3, pady=3, fill='x')
            force_button.pack(side='bottom', padx=3, fill='x')

            label_var = tk.StringVar()
            label_var.set(_('Waiting for Steam to exit...'))
            label = tk.Label(self, textvariable=label_var, bg='white')
            label.pack(pady=(150, 0))

            def cleanup():
                label.destroy()
                button_frame.destroy()
                self.refresh(no_frame=True)
                self.bottomframe.pack(side='bottom')
                show_update()
            self.update()

        queue = q.Queue()

        if check_running('Steam.exe'):
            if get_config('try_soft_shutdown') == 'false':
                forcequit()
            elif get_config('try_soft_shutdown') == 'true':
                print('Soft shutdown mode')
                r_path = fetch_reg('SteamExe')
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

            def steam_checker():
                nonlocal queue
                sleep(1)
                while True:
                    if t.stopped():
                        break
                    if check_running('steam.exe'):
                        sleep(1)
                        continue
                    else:
                        queue.put(1)
                        break

            def cancel():
                t.stop()
                cleanup()
                return

            t = StoppableThread(target=steam_checker)
            t.start()
            if not refresh_override:
                cancel_button['command'] = cancel
        else:
            queue.put(1)

        counter = 0

        def launch_steam():
            nonlocal queue
            nonlocal counter

            try:
                queue.get_nowait()
                label_var.set(_('Launching Steam...'))
                self.update()

                if refresh_override and silent:
                    print('Launching Steam silently...')
                    subprocess.run("start steam://open",
                                   shell=True, check=True)
                else:
                    print('Launching Steam...')
                    subprocess.run("start steam://open/main",
                                   shell=True, check=True)

                if get_config('autoexit') == 'true' and not refresh_override:
                    sys.exit(0)
                elif not refresh_override:
                    cleanup()
            except q.Empty:
                counter += 1
                if counter == 5 and not refresh_override:
                    enable_button()
                self.after(1000, launch_steam)

        self.after(1000, launch_steam)
