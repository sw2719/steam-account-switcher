import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox as msgbox
from tkinter import filedialog
import gettext
import winreg
import psutil
import subprocess
import os
from time import sleep
from ruamel.yaml import YAML
from modules.account import acc_getlist, acc_getdict
from modules.loginusers import loginusers
from modules.reg import fetch_reg, setkey
from modules.config import get_config
from modules.misc import error_msg
from modules.update import start_checkupdate

yaml = YAML()

LOCALE = get_config('locale')

t = gettext.translation('steamswitcher',
                        localedir='locale',
                        languages=[LOCALE],
                        fallback=True)
_ = t.gettext


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


class MainApp(tk.Tk):
    '''Draw main window.'''
    def about(self, version):
        '''Open about window'''
        aboutwindow = tk.Toplevel(self)
        aboutwindow.title(_('About'))
        aboutwindow.geometry("360x180+650+300")
        aboutwindow.resizable(False, False)
        about_disclaimer = tk.Label(aboutwindow,
                                    text=_('Warning: The developer of this application is not responsible for')
                                    + '\n' + _('data loss or any other damage from the use of this app.'))
        about_steam_trademark = tk.Label(aboutwindow, text=_('STEAM is a registered trademark of Valve Corporation.'))
        copyright_label = tk.Label(aboutwindow, text='Copyright (c) sw2719 | All Rights Reserved\n' +
                                   'Licensed under the MIT License.')
        ver = tk.Label(aboutwindow,
                       text='Steam Account Switcher | Version ' + version)

        button_frame = tk.Frame(aboutwindow)
        button_frame.pack(side='bottom', pady=5)

        button_exit = ttk.Button(button_frame,
                                 text=_('Close'),
                                 width=8,
                                 command=aboutwindow.destroy)
        button_github = ttk.Button(button_frame,
                                   text=_('GitHub page'),
                                   command=lambda: os.startfile('https://github.com/sw2719/steam-account-switcher'))
        about_disclaimer.pack(pady=8)
        about_steam_trademark.pack()
        copyright_label.pack(pady=5)
        ver.pack()

        button_exit.pack(side='left', padx=2)
        button_github.pack(side='right', padx=2)

    def addwindow(self):
        '''Open add accounts window'''
        accounts = acc_getlist()
        acc_dict = acc_getdict()

        addwindow = tk.Toplevel(self)
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

        account_entry = ttk.Entry(bottomframe_add, width=29)

        addwindow.grab_set()
        addwindow.focus()
        account_entry.focus()

        print('Opened add window.')

        def adduser(userinput):
            nonlocal acc_dict
            '''Write accounts from user's input to accounts.yml
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
        if loginusers():
            AccountName, PersonaName = loginusers()
        else:
            try_manually = msgbox.askyesno(_('Alert'), _('Could not load loginusers.vdf.') + '\n' +
                                           _('This may be because Steam directory defined') + '\n' +
                                           _('in registry is invalid.') + '\n\n' +
                                           _('Do you want to select Steam directory manually?'))
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
                                                    _('Steam directory is invalid.') + '\n' +
                                                    _('Try again?'))
                        if try_again:
                            continue
                        else:
                            return
            else:
                return

        importwindow = tk.Toplevel(self)
        importwindow.title(_("Import"))
        importwindow.geometry("280x300+650+300")
        importwindow.resizable(False, False)

        importwindow.grab_set()
        importwindow.focus()

        bottomframe_imp = tk.Frame(importwindow)
        bottomframe_imp.pack(side='bottom')

        importlabel = tk.Label(importwindow, text=_('Select accounts to import.') + '\n' +
                               _("Added accounts don't show up."))
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
            nonlocal acc_dict
            for key, value in check_dict.items():
                if value.get() == 1:
                    acc_dict[len(acc_dict)] = {'accountname': key}
            with open('accounts.yml', 'w') as acc:
                yaml = YAML()
                yaml.dump(acc_dict, acc)
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

        orderwindow = tk.Toplevel(self)
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

    def settingswindow(self):
        '''Open settings window'''
        config_dict = get_config('all')

        settingswindow = tk.Toplevel(self)
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
            nonlocal config_dict
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
                               'show_profilename': show_pname[showpnames_cb.current()],
                               'autoexit': autoexit}

                yaml = YAML()
                yaml.dump(config_dict, cfg)

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

    def __init__(self, version, url, bundle):
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
                         command=self.importwindow)
        menu.add_command(label=_("Add accounts"),
                         command=self.addwindow)
        menu.add_command(label=_("Change account order"),
                         command=self.orderwindow)
        menu.add_separator()
        menu.add_command(label=_("Settings"),
                         command=self.settingswindow)
        menu.add_command(label=_("About"),
                         command=lambda: self.about(version))

        menubar.add_cascade(label=_("Menu"), menu=menu)
        self.config(menu=menubar)

        if not bundle:
            debug_menu = tk.Menu(menubar, tearoff=0)
            debug_menu.add_command(label='Update Debug',
                                   command=lambda: self.after(10, lambda: start_checkupdate(self, version, url, bundle, debug=True)))
            menubar.add_cascade(label=_("Debug"), menu=debug_menu)

        bottomframe = tk.Frame(self)
        bottomframe.pack(side='bottom')

        def toggleAutologin():
            '''Toggle autologin registry value between 0 and 1'''
            if fetch_reg('autologin') == 1:
                value = 0
            elif fetch_reg('autologin') == 0:
                value = 1
            setkey('RememberPassword', value, winreg.REG_DWORD)
            self.refresh()

        button_toggle = ttk.Button(bottomframe,
                                   width=15,
                                   text=_('Toggle auto-login'),
                                   command=toggleAutologin)

        button_quit = ttk.Button(bottomframe,
                                 width=5,
                                 text=_('Exit'),
                                 command=self.quit)

        self.restartbutton_text = tk.StringVar()

        if get_config('autoexit') == 'true':
            self.restartbutton_text.set(_('Restart Steam & Exit'))
        else:
            self.restartbutton_text.set(_('Restart Steam'))

        def exit_after_restart():
            '''Restart Steam client and exit application.
            If autoexit is disabled, app won't exit.'''
            try:
                if get_config('try_soft_shutdown') == 'false':
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
                            print('Steam is still running after %s seconds' % str(2+x*2))
                            if x < 8:
                                sleep(1.5)
                                continue
                            else:
                                msg = msgbox.askyesno(_('Alert'),
                                                      _('After soft shutdown attempt,') + '\n' +
                                                      _('Steam appears to be still running.') + '\n\n' +
                                                      _('Do you want to force shutdown Steam?'))
                                if msg:
                                    raise FileNotFoundError
                                else:
                                    error_msg(_('Error'),
                                              _('Could not soft shutdown Steam.') + '\n' +
                                              _('App will now exit.'))
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
                                 _('Could not start Steam automatically') + '\n' +
                                 _('for unknown reason.'))
            if get_config('autoexit') == 'true':
                self.quit()

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

        if fetch_reg('autologin') == 1:
            self.auto_var.set(_('Auto-login Enabled'))
        else:
            self.auto_var.set(_('Auto-login Disabled'))

        autolabel = tk.Label(upper_frame, textvariable=self.auto_var)
        autolabel.pack(side='top')

    def configwindow(self, username, profilename):
        configwindow = tk.Toplevel(self)
        configwindow.title('')
        configwindow.geometry("240x150+650+320")
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

        top_label = tk.Label(configwindow, text=_('Select name settings for %s.') % username)
        top_label.pack(side='top', pady=(4, 3))

        radio_frame1 = tk.Frame(configwindow)
        radio_frame1.pack(side='top', padx=20, pady=(4, 2), fill='x')
        radio_frame2 = tk.Frame(configwindow)
        radio_frame2.pack(side='top', padx=20, pady=(0, 3), fill='x')
        radio_var = tk.IntVar()

        if custom_name.strip():
            radio_var.set(1)
        else:
            radio_var.set(0)

        radio_default = ttk.Radiobutton(radio_frame1,
                                        text=_('Use profile name if available'),
                                        variable=radio_var,
                                        value=0)
        radio_custom = ttk.Radiobutton(radio_frame2,
                                       text=_('Use custom name'),
                                       variable=radio_var,
                                       value=1)

        radio_default.pack(side='left', pady=2)
        radio_custom.pack(side='left', pady=2)

        entry_frame = tk.Frame(configwindow)
        entry_frame.pack(side='bottom', pady=(1, 4))

        name_entry = ttk.Entry(entry_frame, width=26)
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
        configwindow.wait_window()

    def button_func(self, username):
        current_user = fetch_reg('username')
        try:
            self.button_dict[current_user].config(style='TButton', state='normal')  # NOQA
        except Exception:
            pass
        setkey('AutoLoginUser', username, winreg.REG_SZ)
        self.button_dict[username].config(style='sel.TButton', state='disabled')  # NOQA
        self.user_var.set(fetch_reg('username'))

    def remove_user(self, target):
        '''Write accounts to accounts.txt except the
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

        if self.accounts:
            for username in self.accounts:
                if get_config('show_profilename') != 'false':
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
                        if get_config('show_profilename') == 'bar':
                            if profilename == profilename[:n]:
                                profilename = ' | ' + profilename[:n] + ''
                            else:
                                profilename = ' | ' + profilename[:n] + '..'
                        elif get_config('show_profilename') == 'bracket':
                            if profilename == profilename[:n]:
                                profilename = ' (' + profilename[:n] + ')'
                            else:
                                profilename = ' (' + profilename[:n] + '..)'
                else:
                    profilename = ''

                self.frame_dict[username] = tk.Frame(self.button_frame)
                self.frame_dict[username].pack(fill='x', padx=5, pady=3)

                menu_dict[username] = tk.Menu(self, tearoff=0)
                menu_dict[username].add_command(label=_("Set as auto-login account"),
                                                command=lambda name=username: self.button_func(name))
                menu_dict[username].add_separator()
                menu_dict[username].add_command(label=_("Name settings"),
                                                command=lambda name=username, pname=profilename: self.configwindow(name, pname))
                menu_dict[username].add_command(label=_("Delete"),
                                                command=lambda name=username: self.remove_user(name))

                def popup(username, event):
                    menu_dict[username].tk_popup(event.x_root + 55, event.y_root + 17, 0)

                if username == fetch_reg('username'):
                    self.button_dict[username] = ttk.Button(self.frame_dict[username],
                                                            style='sel.TButton',
                                                            text=username + profilename,
                                                            state='disabled',
                                                            command=lambda name=username: self.button_func(name))
                else:
                    self.button_dict[username] = ttk.Button(self.frame_dict[username],
                                                            style='TButton',
                                                            text=username + profilename,
                                                            state='normal',
                                                            command=lambda name=username: self.button_func(name))
                self.button_dict[username].bind("<Button-3>", lambda event, username=username: popup(username, event))
                self.button_dict[username].pack(fill='x', padx=(0, 1))

    def refresh(self):
        '''Refresh main window widgets'''
        self.accounts = acc_getlist()
        self.acc_dict = acc_getdict()
        self.geometry("300x%s" %
                      window_height())
        self.button_frame.destroy()
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(side='top', fill='x')

        self.user_var.set(fetch_reg('username'))

        if fetch_reg('autologin') == 1:
            self.auto_var.set(_('Auto-login Enabled'))
        else:
            self.auto_var.set(_('Auto-login Disabled'))

        self.draw_button()

        if get_config('autoexit') == 'true':
            self.restartbutton_text.set(_('Restart Steam & Exit'))
        else:
            self.restartbutton_text.set(_('Restart Steam'))

        print('Menu refreshed with %s account(s)' % len(self.accounts))
