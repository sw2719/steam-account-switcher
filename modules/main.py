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
from time import sleep
from ruamel.yaml import YAML
from PIL import Image, ImageTk
from modules.account import acc_getlist, acc_getdict, loginusers
from modules.reg import fetch_reg, setkey
from modules.config import get_config, config_write_dict, config_write_value, SYS_LOCALE
from modules.util import steam_running, StoppableThread, open_screenshot, raise_exception, test, get_center_pos, launch_updater, create_shortcut
from modules.update import start_checkupdate, hide_update, show_update, update_frame_color
from modules.ui import DragDropListbox, AccountButton, AccountButtonGrid, SimpleButton, WelcomeWindow, steamid_window, ToolTipWindow, ask_steam_dir, get_color
from modules.avatar import download_avatar

yaml = YAML()

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
    def __init__(self, version, url, bundle, std_out, std_err, after_update):
        sys.stdout = std_out
        sys.stderr = std_err

        self.accounts = acc_getlist()
        self.acc_dict = acc_getdict()
        self.demo_mode = False
        self.BUNDLE = bundle
        self.after_update = after_update

        tk.Tk.__init__(self)
        self['bg'] = get_color('window_background')
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

        if not test():
            ask_steam_dir()

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
                         command=lambda: self.about(version))

        menubar.add_cascade(label=_("Menu"), menu=menu)
        self.config(menu=menubar)

        if not self.BUNDLE:
            debug_menu = tk.Menu(menubar, tearoff=0)
            debug_menu.add_command(label='Check for updates with debug mode',
                                   command=lambda: self.after(10, lambda: start_checkupdate(self, version, url, self.BUNDLE, debug=True)))
            debug_menu.add_command(label='Check for updates without debug mode',
                                   command=lambda: self.after(10, lambda: start_checkupdate(self, version, url, True)))
            debug_menu.add_command(label='Check for updates (Force update available)',
                                   command=lambda: self.after(10, lambda: start_checkupdate(self, '1.0', url, True)))
            debug_menu.add_command(label='Check for updates (Raise error)',
                                   command=lambda: self.after(10, lambda: start_checkupdate(self, version, url, True, exception=True)))
            debug_menu.add_command(label="Download avatar images",
                                   command=download_avatar)
            debug_menu.add_command(label="Open initial setup",
                                   command=lambda: self.welcomewindow(debug=True))
            debug_menu.add_command(label="Open initial setup with after_update True",
                                   command=lambda: self.welcomewindow(debug=True, update_override=True))
            debug_menu.add_command(label="Toggle demo mode",
                                   command=self.toggle_demo)
            debug_menu.add_command(label="Raise exception",
                                   command=raise_exception)
            debug_menu.add_command(label="Open about window with copyright notice",
                                   command=lambda: self.about(version, force_copyright=True))
            debug_menu.add_command(label="Launch updater (update.zip required)",
                                   command=launch_updater)
            debug_menu.add_command(label="Create shortcut",
                                   command=create_shortcut)
            debug_menu.add_command(label="Exit app with sys.exit",
                                   command=sys.exit)
            menubar.add_cascade(label=_("Debug"), menu=debug_menu)

        self.bottomframe = tk.Frame(self, bg=get_color('bottomframe'))
        self.bottomframe.pack(side='bottom', fill='x')

        def toggleAutologin():
            '''Toggle autologin registry value between 0 and 1'''
            if fetch_reg('RememberPassword') == 1:
                setkey('RememberPassword', 0, winreg.REG_DWORD)
            elif fetch_reg('RememberPassword') == 0:
                setkey('RememberPassword', 1, winreg.REG_DWORD)

            if fetch_reg('RememberPassword') == 1:
                self.auto_var.set(_('Auto-login Enabled'))
                self.autolabel['fg'] = get_color('autologin_text_on')
            else:
                self.auto_var.set(_('Auto-login Disabled'))
                self.autolabel['fg'] = get_color('autologin_text_off')

        self.restartbutton_text = tk.StringVar()

        if get_config('autoexit') == 'true':
            self.restartbutton_text.set(_('Restart Steam & Exit'))
        else:
            self.restartbutton_text.set(_('Restart Steam'))

        self.button_toggle = SimpleButton(self.bottomframe,
                                          widget='bottom_button',
                                          text=_('Toggle auto-login'),
                                          command=toggleAutologin,
                                          bd=2)
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

        self.button_toggle.grid(row=0, column=0, padx=3, pady=3, sticky='nesw')
        self.button_exit.grid(row=0, column=1, pady=3, sticky='nesw')
        self.button_restart.grid(row=0, column=2, padx=3, pady=3, sticky='nesw')

        self.bottomframe.grid_columnconfigure(0, weight=1)
        self.bottomframe.grid_columnconfigure(1, weight=1)
        self.bottomframe.grid_columnconfigure(2, weight=1)
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

        if fetch_reg('RememberPassword') == 1:
            self.auto_var.set(_('Auto-login Enabled'))
            auto_color = get_color('autologin_text_on')
        else:
            self.auto_var.set(_('Auto-login Disabled'))
            auto_color = get_color('autologin_text_off')

        self.autolabel = tk.Label(self.upper_frame, textvariable=self.auto_var, bg=self.upper_frame['bg'], fg=auto_color)
        self.autolabel.pack(side='top')
        tk.Frame(self.upper_frame, bg='grey').pack(fill='x')

        self.draw_button()

    def report_callback_exception(self, exc, val, tb):
        msgbox.showerror(_('Unhandled Exception'),
                         message=traceback.format_exc() + '\n' + _('Please contact the developer if the issue persists.'))

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

    def welcomewindow(self, debug=False, update_override=False):
        if update_override:
            window = WelcomeWindow(self, self.popup_geometry(320, 270, multiplier=2), True, debug)
        else:
            window = WelcomeWindow(self, self.popup_geometry(320, 270, multiplier=2), self.after_update, debug)

        def event_function(event):
            if str(event.widget) == '.!welcomewindow':
                if self.accounts:
                    self.update_avatar()

                self.refresh()

        window.bind('<Destroy>', event_function)

    def configwindow(self, username):
        configwindow = tk.Toplevel(self, bg='white')
        configwindow.title('')

        x, y = self.get_window_pos()
        configwindow.geometry(self.popup_geometry(250, 165))
        configwindow.resizable(False, False)
        configwindow.bind('<Escape>', lambda event: configwindow.destroy())

        try:
            configwindow.iconbitmap('asset/icon.ico')
        except tk.TclError:
            pass

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

        top_label = tk.Label(configwindow, text=_('Select name settings\nfor %s') % username, bg='white')
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

        name_entry = tk.Entry(entry_frame, width=27, disabledbackground='#C6C6C6', relief='solid')
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

            buttonframe.grid_propagate(0)
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

            for index, username in enumerate(self.accounts):
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
                        profilename = _('N/A')

                finally:
                    if i is not None:  # i could be 0 so we can't use if i:
                        steam64 = steam64_list[i]
                        image = steam64
                    else:
                        steam64 = None
                        image = 'default'

                    profilename = profilename[:30]

                # We have to make a menu for every account! Sounds ridiculous? Me too.
                if SYS_LOCALE == 'ko_KR':
                    menu_font = tkfont.Font(self, size=9, family='맑은 고딕')
                    menu_dict[username] = tk.Menu(self, tearoff=0, font=menu_font)
                else:
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
                                                    command=lambda username=username, steamid64=steam64: steamid_window(self, username, steamid64, self.popup_geometry(270, 180)))
                    menu_dict[username].add_command(label=_('Update avatar'),
                                                    command=lambda steamid64=steam64: self.update_avatar(steamid_list=[steamid64]))
                    menu_dict[username].add_separator()

                menu_dict[username].add_command(label=_("Name settings"),
                                                command=lambda name=username, pname=profilename: self.configwindow(name))
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

            buttonframe.grid_propagate(0)
            scroll_bar.pack(side="right", fill="y")
            canvas.pack(side="left", fill='both', expand=True)

            if len(self.accounts) % 3 == 0:
                h = 109 * (len(self.accounts) // 3)
            else:
                h = 109 * (len(self.accounts) // 3 + 1)

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
                        steam64 = None
                        image = 'default'

                    profilename = profilename[:30]

                # We have to make a menu for every account! Sounds ridiculous? Me too.
                if SYS_LOCALE == 'ko_KR':
                    menu_font = tkfont.Font(self, size=9, family='맑은 고딕')
                    menu_dict[username] = tk.Menu(self, tearoff=0, font=menu_font)
                else:
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
                                                    command=lambda username=username, steamid64=steam64: steamid_window(self, username, steamid64, self.popup_geometry(270, 180)))
                    menu_dict[username].add_command(label=_('Update avatar'),
                                                    command=lambda steamid64=steam64: self.update_avatar(steamid_list=[steamid64]))
                    menu_dict[username].add_separator()

                menu_dict[username].add_command(label=_("Name settings"),
                                                command=lambda name=username, pname=profilename: self.configwindow(name))
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
                    self.button_dict[username].disable(no_fade=True)

                self.button_dict[username].pack(fill='x')
                tk.Frame(buttonframe, bg=get_color('seperator')).pack(fill='x')

            scroll_bar.pack(side="right", fill="y")
            canvas.pack(side="left", fill='both', expand=True)
            h = 49 * len(self.accounts)
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
        self.accounts = acc_getlist()
        self.acc_dict = acc_getdict()

        if not no_frame:
            self.no_user_frame.destroy()
            self.button_frame.destroy()

        self.button_frame = tk.Frame(self, bg=get_color('bottomframe'))
        self.button_frame.pack(side='top', fill='both', expand=True)
        self['bg'] = get_color('window_background')

        self.bottomframe.configure(bg=get_color('bottomframe'))
        self.button_toggle.update_color()
        self.button_exit.update_color()
        self.button_restart.update_color()
        self.upper_frame.configure(bg=get_color('upperframe'))
        self.userlabel_1.configure(bg=self.upper_frame['bg'], fg=get_color('text'))
        self.userlabel_2.configure(bg=self.upper_frame['bg'], fg=get_color('text'))

        update_frame_color()

        if fetch_reg('RememberPassword') == 1:
            self.auto_var.set(_('Auto-login Enabled'))
            auto_color = get_color('autologin_text_on')
        else:
            self.auto_var.set(_('Auto-login Disabled'))
            auto_color = get_color('autologin_text_off')

        self.autolabel.configure(bg=self.upper_frame['bg'], fg=auto_color)

        if self.demo_mode:
            self.user_var.set('username0')
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
            steamid_list, accountname, __ = loginusers()

            for index, steamid in enumerate(steamid_list):
                if accountname[index] in self.accounts:
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
            height = 200
        else:
            height = 180

        aboutwindow = tk.Toplevel(self, bg='white')
        aboutwindow.title(_('About'))
        aboutwindow.geometry(self.popup_geometry(360, height))
        aboutwindow.resizable(False, False)
        aboutwindow.focus()
        aboutwindow.bind('<Escape>', lambda event: aboutwindow.destroy())

        try:
            aboutwindow.iconbitmap('asset/icon.ico')
        except tk.TclError:
            pass

        about_disclaimer = tk.Label(aboutwindow, bg='white', fg='black',
                                    text=_('Warning: The developer of this application is not responsible for\n' +
                                           'data loss or any other damage from the use of this app.'))
        about_steam_trademark = tk.Label(aboutwindow, bg='white', fg='black',
                                         text=_('STEAM is a registered trademark of Valve Corporation.'))
        if self.BUNDLE or force_copyright:
            copyright_label = tk.Label(aboutwindow, bg='white', fg='black',
                                       text='Copyright (c) 2020 sw2719 | All Rights Reserved\n' +
                                       'View copyright notice for details')
        else:
            copyright_label = tk.Label(aboutwindow, bg='white', fg='black',
                                       text='Copyright (c) 2020 sw2719 | All Rights Reserved\n' +
                                       'View LICENSE file for details')
        ver = tk.Label(aboutwindow, bg='white', fg='black',
                       text='Steam Account Switcher | Version ' + version)

        def copyright_notice():
            cprightwindow = tk.Toplevel(aboutwindow, bg='white')
            cprightwindow.title(_('Copyright notice'))
            cprightwindow.geometry(self.popup_geometry(630, 350, multiplier=2))
            cprightwindow.resizable(False, False)
            cprightwindow.focus()
            cprightwindow.bind('<Escape>', lambda event: cprightwindow.destroy())

            ttk.Button(cprightwindow, text=_('Close'), command=cprightwindow.destroy).pack(side='bottom', pady=3)
            ttk.Separator(cprightwindow, orient=tk.HORIZONTAL).pack(side='bottom', fill='x')

            cpright_text = ScrolledText(cprightwindow, bd=1, relief='flat')

            with open('asset/COPYRIGHT_NOTICE', encoding='utf-8') as txt:
                cpright_text.insert(tk.CURRENT, txt.read())

            cpright_text.configure(state=tk.DISABLED)
            cpright_text.pack(side='top', expand=True, fill='both')

        button_frame = tk.Frame(aboutwindow, bg='white')
        button_frame.pack(side='bottom', pady=5)

        button_close = ttk.Button(button_frame,
                                  text=_('Close'),
                                  command=aboutwindow.destroy)
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
        accounts = acc_getlist()
        if not accounts:
            msgbox.showinfo(_('No Accounts'),
                            _("There's no account added."))
            return
        refreshwindow = tk.Toplevel(self, bg='white')
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

        bottomframe_rm = tk.Frame(refreshwindow, bg='white')
        bottomframe_rm.pack(side='bottom')

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
            popup.geometry(self.popup_geometry(180, 100))
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
        x, y = self.get_window_pos()

        addwindow = tk.Toplevel(self, bg='white')
        addwindow.title(_("Add"))
        addwindow.geometry(self.popup_geometry(300, 150))
        addwindow.resizable(False, False)
        addwindow.bind('<Escape>', lambda event: addwindow.destroy())

        try:
            addwindow.iconbitmap('asset/icon.ico')
        except tk.TclError:
            pass

        topframe_add = tk.Frame(addwindow, bg='white')
        topframe_add.pack(side='top', anchor='center')

        bottomframe_add = tk.Frame(addwindow, bg='white')
        bottomframe_add.pack(side='bottom', anchor='e', fill='x')

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
        button_add = ttk.Button(bottomframe_add, width=10, text=_('Add'),
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
        accounts = acc_getlist()
        acc_dict = acc_getdict()
        steamid_list, account_name, persona_name = loginusers()

        if set(account_name).issubset(set(acc_getlist())):
            msgbox.showinfo(_('Info'), _("There's no account left to import."))
            return

        s = ttk.Style()
        s.configure('Import.TCheckbutton', background='white')

        x, y = self.get_window_pos()

        importwindow = tk.Toplevel(self, bg='white')
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

        x, y = self.get_window_pos()

        orderwindow = tk.Toplevel(self, bg='white')
        orderwindow.title("")
        orderwindow.geometry(self.popup_geometry(224, 270))
        orderwindow.resizable(False, False)
        orderwindow.bind('<Escape>', lambda event: orderwindow.destroy())

        try:
            orderwindow.iconbitmap('asset/icon.ico')
        except tk.TclError:
            pass

        bottomframe = tk.Frame(orderwindow, bg='white')
        bottomframe.pack(side='bottom', padx=3, pady=3)

        labelframe = tk.Frame(orderwindow, bg='white')
        labelframe.pack(side='bottom', padx=3)

        orderwindow.grab_set()
        orderwindow.focus()

        lbframe = tk.Frame(orderwindow, bg='white')

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

        for i, v in enumerate(accounts):
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

        button_ok = ttk.Button(bottomframe,
                               width=9, text=_('OK'), command=ok)
        button_ok.pack(side='left', padx=(0, 1))
        button_cancel = ttk.Button(bottomframe,
                                   width=9, text=_('Cancel'), command=close)
        button_cancel.pack(side='left', padx=(1, 1.5))

        button_up = ttk.Button(bottomframe, width=3,
                               text='↑', command=up)
        button_up.pack(side='right', padx=(1.5, 1))

        button_down = ttk.Button(bottomframe, width=3,
                                 text='↓', command=down)
        button_down.pack(side='right', padx=(1, 0))

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
            width = 260
            ui_padx = 35
            theme_padx = 40

        settingswindow = tk.Toplevel(self, bg='white')
        settingswindow.title(_("Settings"))
        settingswindow.geometry(self.popup_geometry(width, 430))  # 260 is original
        settingswindow.resizable(False, False)
        settingswindow.bind('<Escape>', lambda event: settingswindow.destroy())

        try:
            settingswindow.iconbitmap('asset/icon.ico')
        except tk.TclError:
            pass

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
        localeframe.pack(side='top', pady=(14, 7), fill='x')
        locale_label = tk.Label(localeframe, text=_('Language'), bg='white')
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

        restart_frame = tk.Frame(settingswindow, bg='white')
        restart_frame.pack(side='top')

        s = ttk.Style()
        s.configure('Settings.TRadiobutton', background='white')
        s.configure('Settings.TCheckbutton', background='white')

        ui_frame = tk.Frame(settingswindow, bg='white')
        ui_frame.pack(side='top', pady=(5, 5), fill='x')
        ui_radio_var = tk.IntVar()

        list_radio_frame = tk.Frame(ui_frame, bg='white')
        list_radio_frame.pack(side='left', padx=(ui_padx, 0))

        list_canvas = tk.Canvas(list_radio_frame, width=30, height=30, bg='white', bd=0, highlightthickness=0)
        list_img = Image.open("asset/list.png").resize((30, 30))

        image1 = ImageTk.PhotoImage(list_img)
        list_canvas.create_image(15, 15, image=image1)
        list_canvas.pack(side='top', padx=0, pady=5)

        radio_list = ttk.Radiobutton(list_radio_frame,
                                     text=_('List Mode'),
                                     variable=ui_radio_var,
                                     value=0,
                                     style='Settings.TRadiobutton')
        radio_list.pack(side='top', pady=2)
        ToolTipWindow(radio_list, _('Display accounts in vertical list.'), center=True)

        grid_radio_frame = tk.Frame(ui_frame, bg='white')
        grid_radio_frame.pack(side='right', padx=(0, ui_padx))

        grid_canvas = tk.Canvas(grid_radio_frame, width=30, height=30, bg='white', bd=0, highlightthickness=0)
        grid_img = Image.open("asset/grid.png").resize((30, 30))

        image2 = ImageTk.PhotoImage(grid_img)
        grid_canvas.create_image(15, 15, image=image2)
        grid_canvas.pack(side='top', padx=0, pady=5)

        radio_grid = ttk.Radiobutton(grid_radio_frame,
                                     text=_('Grid Mode'),
                                     variable=ui_radio_var,
                                     value=1,
                                     style='Settings.TRadiobutton')
        radio_grid.pack(side='top', pady=2)
        ToolTipWindow(radio_grid, _('Display accounts in 3 x n grid.'), center=True)

        if get_config('ui_mode') == 'grid':
            ui_radio_var.set(1)

        avatar_frame = tk.Frame(settingswindow, bg='white')
        avatar_frame.pack(fill='x', side='top', padx=12, pady=(2, 5))

        avatar_chkb = ttk.Checkbutton(avatar_frame, style='Settings.TCheckbutton',
                                      text=_('Show avatar images'))

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

        theme_frame = tk.Frame(settingswindow, bg='white')
        theme_frame.pack(side='top', pady=(5, 5), fill='x')
        theme_radio_var = tk.IntVar()

        light_radio_frame = tk.Frame(theme_frame, bg='white')
        light_radio_frame.pack(side='left', padx=(theme_padx, 0))

        light_canvas = tk.Canvas(light_radio_frame, width=40, height=64, bg='white', bd=0, highlightthickness=0)
        light_img = Image.open("asset/light.png").resize((40, 64))

        image3 = ImageTk.PhotoImage(light_img)
        light_canvas.create_image(20, 32, image=image3)
        light_canvas.pack(side='top', padx=0, pady=5)

        radio_light = ttk.Radiobutton(light_radio_frame,
                                      text=_('Light Theme'),
                                      variable=theme_radio_var,
                                      value=0,
                                      style='Settings.TRadiobutton')
        radio_light.pack(side='top', pady=2)

        dark_radio_frame = tk.Frame(theme_frame, bg='white')
        dark_radio_frame.pack(side='right', padx=(0, theme_padx))

        dark_canvas = tk.Canvas(dark_radio_frame, width=40, height=64, bg='white', bd=0, highlightthickness=0)
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

        ToolTipWindow(radio_dark, _('Dark theme is applied only to main window.'), center=True)
        if get_config('theme') == 'dark':
            theme_radio_var.set(1)

        mode_radio_frame1 = tk.Frame(settingswindow, bg='white')
        mode_radio_frame1.pack(side='top', padx=12, pady=(7, 2), fill='x')
        mode_radio_frame2 = tk.Frame(settingswindow, bg='white')
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

        softshutdwn_frame = tk.Frame(settingswindow, bg='white')
        softshutdwn_frame.pack(fill='x', side='top', padx=12, pady=(7, 5))

        soft_chkb = ttk.Checkbutton(softshutdwn_frame, style='Settings.TCheckbutton',
                                    text=_('Try to soft shutdown Steam client'))

        soft_chkb.state(['!alternate'])

        if config_dict['try_soft_shutdown'] == 'true':
            soft_chkb.state(['selected'])
        else:
            soft_chkb.state(['!selected'])

        soft_chkb.pack(side='left')

        autoexit_frame = tk.Frame(settingswindow, bg='white')
        autoexit_frame.pack(fill='x', side='top', padx=12, pady=(5, 0))

        autoexit_chkb = ttk.Checkbutton(autoexit_frame, style='Settings.TCheckbutton',
                                        text=_('Exit app after Steam is restarted'))

        autoexit_chkb.state(['!alternate'])

        if config_dict['autoexit'] == 'true':
            autoexit_chkb.state(['selected'])
        else:
            autoexit_chkb.state(['!selected'])

        autoexit_chkb.pack(side='left')

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
            else:
                theme = 'light'

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
                           'theme': theme}

            config_write_dict(config_dict)

            if last_config['show_avatar'] == 'false' and 'selected' in avatar_chkb.state():
                if msgbox.askyesno('', _('Do you want to download avatar images now?')):
                    self.update_avatar(no_ui=True)

            if current_locale != locale[locale_cb.current()]:
                self.after(100, lambda: msgbox.showinfo(_('Locale has been changed'),
                                                        _('Restart app to apply new locale settings.')))
                current_locale = locale[locale_cb.current()]

            self.refresh()

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

        self.no_user_frame.destroy()
        self.button_frame.destroy()
        hide_update()
        self.bottomframe.pack_forget()
        button_frame = tk.Frame(self, bg=self['bg'])
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
        force_button.pack(side='bottom', padx=3, fill='x')

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

        if steam_running():
            label_var.set(_('Waiting for Steam to exit...'))

            if get_config('try_soft_shutdown') == 'false':
                forcequit()
            elif get_config('try_soft_shutdown') == 'true':
                print('Soft shutdown mode')

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
                subprocess.run(f"start {steam_exe} -shutdown", shell=True,
                               creationflags=0x08000000, check=True)
                print('Shutdown command sent. Waiting for Steam...')

            def steam_checker():
                nonlocal queue
                sleep(1)
                while True:
                    if t.stopped():
                        break
                    if steam_running():
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
            cancel_button.update_command(cancel)
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

                print('Launching Steam...')
                subprocess.run("start steam://open/main",
                               shell=True, check=True)

                if get_config('autoexit') == 'true':
                    self.exit_app()
                elif not refresh_override:
                    cleanup()
            except q.Empty:
                counter += 1
                if counter == 10:
                    enable_button()
                self.after(1000, launch_steam)

        self.after(2000, launch_steam)
