import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox as msgbox
from tkinter import filedialog
import gettext
import winreg
import psutil
import subprocess
from time import sleep
from ruamel.yaml import YAML
from modules.account import acc_getlist, acc_getdict
from modules.loginusers import loginusers
from modules.reg import fetch_reg, setkey
from modules.config import get_config
from modules.misc import error_msg

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


def about(master, version):
    '''Open about window'''
    aboutwindow = tk.Toplevel(master)
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
    ver = tk.Label(aboutwindow,
                   text='Steam Account Switcher | Version ' + version)

    button_exit = ttk.Button(aboutwindow,
                             text=_('Close'),
                             width=8,
                             command=aboutwindow.destroy)
    about_row.pack(pady=8)
    about_steam.pack()
    about_email.pack()
    about_disclaimer.pack(pady=5)
    about_steam_trademark.pack()
    copyright_label.pack(pady=5)
    ver.pack()
    button_exit.pack(side='bottom', pady=5)


class addwindow(tk.Toplevel):
    '''Open add accounts window'''
    def adduser(self, userinput):
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
        self.destroy()

    def enterkey(self, event):
        self.adduser(self.account_entry.get())

    def __init__(self, master):
        tk.Toplevel.__init__(self, master)
        self.title(_("Add"))
        self.geometry("300x150+650+300")
        self.resizable(False, False)

        topframe_add = tk.Frame(self)
        topframe_add.pack(side='top', anchor='center')

        bottomframe_add = tk.Frame(self)
        bottomframe_add.pack(side='bottom', anchor='e')

        addlabel_row1 = tk.Label(topframe_add,
                                 text=_('Enter accounts(s) to add.'))
        addlabel_row2 = tk.Label(topframe_add,
                                 text=_("In case of adding multiple accounts,") + '\n' +
                                 _("seperate each account with '/' (slash)."))

        self.account_entry = ttk.Entry(bottomframe_add, width=29)

        self.grab_set()
        self.focus()
        self.account_entry.focus()

        self.bind('<Return>', self.enterkey)
        button_add = ttk.Button(bottomframe_add, width=9, text=_('Add'),
                                command=lambda: self.adduser(self.account_entry.get()))
        button_addcancel = ttk.Button(self, width=9,
                                      text=_('Cancel'), command=self.destroy)
        addlabel_row1.pack(pady=10)
        addlabel_row2.pack()

        self.account_entry.pack(side='left', padx=3, pady=3)
        button_add.pack(side='left', anchor='e', padx=3, pady=3)
        button_addcancel.pack(side='bottom', anchor='e', padx=3)


class importwindow(tk.Toplevel):
    '''Open import accounts window'''

    def import_user(self):
        for key, value in self.check_dict.items():
            if value.get() == 1:
                self.acc_dict[len(self.acc_dict)] = {'accountname': key}
        with open('accounts.yml', 'w') as acc:
            yaml = YAML()
            yaml.dump(self.acc_dict, acc)
        main.refresh()
        self.destroy()

    def __init__(self, master):
        self.accounts = acc_getlist()
        self.acc_dict = acc_getdict()

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

        tk.Toplevel.__init__(self, master)
        self.title(_("Import"))
        self.geometry("280x300+650+300")
        self.resizable(False, False)

        self.grab_set()
        self.focus()

        bottomframe_imp = tk.Frame(self)
        bottomframe_imp.pack(side='bottom')

        importlabel = tk.Label(self, text=_('Select accounts to import.') + '\n' +
                               _("Added accounts don't show up."))
        importlabel.pack(side='top',
                         padx=5,
                         pady=5)
        print('Opened import window.')

        def close():
            self.destroy()

        def onFrameConfigure(canvas):
            '''Reset the scroll region to encompass the inner frame'''
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        check_frame = tk.Frame(canvas)
        scroll_bar = ttk.Scrollbar(self,
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

        self.check_dict = {}

        for i, v in enumerate(AccountName):
            if v not in self.accounts:
                tk_var = tk.IntVar()
                checkbutton = ttk.Checkbutton(check_frame,
                                              text=v + f' ({PersonaName[i]})',
                                              variable=tk_var)
                checkbutton.bind("<MouseWheel>", _on_mousewheel)
                checkbutton.pack(side='top', padx=2, anchor='w')
                self.check_dict[v] = tk_var

        import_cancel = ttk.Button(bottomframe_imp,
                                   text=_('Cancel'),
                                   command=self.destroy,
                                   width=9)
        import_ok = ttk.Button(bottomframe_imp,
                               text=_('Import'),
                               command=self.import_user,
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


class orderwindow(tk.Toplevel):
    '''Open order change window'''
    def down(self):
        i = self.lb.curselection()[0]
        if i == self.lb.size() - 1:
            return
        x = self.lb.get(i)
        self.lb.delete(i)
        self.lb.insert(i+1, x)
        self.lb.select_set(i+1)

    def up(self):
        i = self.lb.curselection()[0]
        if i == 0:
            return
        x = self.lb.get(i)
        self.lb.delete(i)
        self.lb.insert(i-1, x)
        self.lb.select_set(i-1)

    def apply(self):
        order = self.lb.get(0, tk.END)
        print('New order is', order)

        buffer_dict = {}

        for item in self.acc_dict.items():
            i = order.index(item[1]['accountname'])
            buffer_dict[i] = item[1]

        dump_dict = {}

        for x in range(len(buffer_dict)):
            dump_dict[x] = buffer_dict[x]

        with open('accounts.yml', 'w') as acc:
            yaml = YAML()
            yaml.dump(dump_dict, acc)
        main.refresh()

    def close(self):
        self.destroy()

    def ok(self):
        self.apply()
        self.destroy()

    def __init__(self, master):
        self.accounts = acc_getlist()
        self.acc_dict = acc_getdict()

        tk.Toplevel.__init__(self, master)
        self.title("")
        self.geometry("210x300+650+300")
        self.resizable(False, False)

        bottomframe_windowctrl = tk.Frame(self)
        bottomframe_windowctrl.pack(side='bottom', padx=3, pady=3)

        bottomframe_orderctrl = tk.Frame(self)
        bottomframe_orderctrl.pack(side='bottom', padx=3, pady=3)

        labelframe = tk.Frame(self)
        labelframe.pack(side='bottom', padx=3)

        self.grab_set()
        self.focus()

        lbframe = tk.Frame(self)

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

        self.lb = DragDropListbox(lbframe, height=12, width=26,
                                  highlightthickness=0,
                                  yscrollcommand=scrollbar.set)

        scrollbar["command"] = self.lb.yview

        def _on_mousewheel(event):
            '''Scroll window on mousewheel input'''
            self.lb.yview_scroll(int(-1*(event.delta/120)), "units")

        self.lb.bind("<MouseWheel>", _on_mousewheel)
        self.lb.pack(side='left')

        for i, v in enumerate(self.accounts):
            self.lb.insert(i, v)

        self.lb.select_set(0)
        lbframe.pack(side='top', pady=5)

        lb_label1 = tk.Label(labelframe, text=_('Drag or use buttons below'))
        lb_label2 = tk.Label(labelframe, text=_('to change order.'))

        lb_label1.pack()
        lb_label2.pack()

        button_up = ttk.Button(bottomframe_orderctrl,
                               text=_('Up'),
                               command=self.up)
        button_up.pack(side='left', padx=2)

        button_down = ttk.Button(bottomframe_orderctrl,
                                 text=_('Down'),
                                 command=self.down)
        button_down.pack(side='right', padx=2)

        button_ok = ttk.Button(bottomframe_windowctrl,
                               width=8,
                               text=_('OK'),
                               command=self.ok)
        button_ok.pack(side='left')
        button_cancel = ttk.Button(bottomframe_windowctrl,
                                   width=8,
                                   text=_('Cancel'),
                                   command=self.destroy)
        button_cancel.pack(side='left', padx=3)

        button_apply = ttk.Button(bottomframe_windowctrl,
                                  width=8,
                                  text=_('Apply'),
                                  command=self.apply)
        button_apply.pack(side='left')


class settingswindow(tk.Toplevel):
    '''Open settings window'''
    def apply(self):
        '''Write new config values to config.txt'''
        with open('config.yml', 'w') as cfg:
            locale = ('en_US', 'ko_KR')
            show_pname = ('bar', 'bracket', 'false')

            if 'selected' in self.soft_chkb.state():
                soft_shutdown = 'true'
            else:
                soft_shutdown = 'false'

            if 'selected' in self.autoexit_chkb.state():
                autoexit = 'true'
            else:
                autoexit = 'false'

            config_dict = {'locale': locale[self.locale_cb.current()],
                           'try_soft_shutdown': soft_shutdown,
                           'show_profilename': show_pname[self.showpnames_cb.current()],  # NOQA
                           'autoexit': autoexit}

            yaml = YAML()
            yaml.dump(config_dict, cfg)

        main.refresh()

    def ok(self):
        self.apply()
        self.destroy()

    def __init__(self, master):
        self.config_dict = get_config('all')
        tk.Toplevel.__init__(self, master)
        self.title(_("Settings"))
        self.geometry("260x240+650+300")
        self.resizable(False, False)
        self.bottomframe_set = tk.Frame(self)
        self.bottomframe_set.pack(side='bottom')
        self.grab_set()
        self.focus()

        localeframe = tk.Frame(self)
        localeframe.pack(side='top', padx=10, pady=14)
        locale_label = tk.Label(localeframe, text=_('Language'))
        locale_label.pack(side='left', padx=3)
        self.locale_cb = ttk.Combobox(localeframe,
                                      state="readonly",
                                      values=['English',  # 0
                                              '한국어 (Korean)'])  # 1
        if get_config('locale') == 'en_US':
            self.locale_cb.current(0)
        elif get_config('locale') == 'ko_KR':
            self.locale_cb.current(1)

        self.locale_cb.pack(side='left', padx=3)

        restart_frame = tk.Frame(self)
        restart_frame.pack(side='top')

        restart_label = tk.Label(restart_frame,
                                 text=_('Restart app to apply language settings.'))
        restart_label.pack()

        showpnames_frame = tk.Frame(self)
        showpnames_frame.pack(fill='x', side='top', padx=10, pady=19)

        showpnames_label = tk.Label(showpnames_frame, text=_('Show profile names'))
        showpnames_label.pack(side='left', padx=3)
        self.showpnames_cb = ttk.Combobox(showpnames_frame,
                                          state="readonly",
                                          values=[_('Use bar - |'),  # 0
                                                  _('Use brackets - ( )'),  # 1
                                                  _('Off')])  # 1
        if self.config_dict['show_profilename'] == 'bar':
            self.showpnames_cb.current(0)
        elif self.config_dict['show_profilename'] == 'bracket':
            self.showpnames_cb.current(1)
        elif self.config_dict['show_profilename'] == 'false':
            self.showpnames_cb.current(2)

        self.showpnames_cb.pack(side='left', padx=3)

        softshutdwn_frame = tk.Frame(self)
        softshutdwn_frame.pack(fill='x', side='top', padx=12, pady=1)

        self.soft_chkb = ttk.Checkbutton(softshutdwn_frame,
                                         text=_('Try to soft shutdown Steam client'))

        self.soft_chkb.state(['!alternate'])

        if self.config_dict['try_soft_shutdown'] == 'true':
            self.soft_chkb.state(['selected'])
        else:
            self.soft_chkb.state(['!selected'])

        self.soft_chkb.pack(side='left')

        autoexit_frame = tk.Frame(self)
        autoexit_frame.pack(fill='x', side='top', padx=12, pady=18)

        self.autoexit_chkb = ttk.Checkbutton(autoexit_frame,
                                             text=_('Exit app upon Steam restart'))

        self.autoexit_chkb.state(['!alternate'])
        if self.config_dict['autoexit'] == 'true':
            self.autoexit_chkb.state(['selected'])
        else:
            self.autoexit_chkb.state(['!selected'])

        self.autoexit_chkb.pack(side='left')
        settings_ok = ttk.Button(self.bottomframe_set,
                                 text=_('OK'),
                                 command=self.ok,
                                 width=10)

        settings_cancel = ttk.Button(self.bottomframe_set,
                                     text=_('Cancel'),
                                     command=self.destroy,
                                     width=10)

        settings_apply = ttk.Button(self.bottomframe_set,
                                    text=_('Apply'),
                                    command=self.apply,
                                    width=10)

        settings_ok.pack(side='left', padx=3, pady=3)
        settings_cancel.pack(side='left', padx=3, pady=3)
        settings_apply.pack(side='left', padx=3, pady=3)


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
                         command=lambda: importwindow(self))
        menu.add_command(label=_("Add accounts"),
                         command=lambda: addwindow(self))
        menu.add_command(label=_("Remove accounts"),
                         command=lambda: removewindow(self))
        menu.add_command(label=_("Change account order"),
                         command=lambda: orderwindow(self))
        menu.add_separator()
        menu.add_command(label=_("Settings"),
                         command=lambda: settingswindow(self))
        menu.add_command(label=_("About"),
                         command=lambda: about(self, version))

        menubar.add_cascade(label=_("Menu"), menu=menu)
        self.config(menu=menubar)

        if not bundle:
            debug_menu = tk.Menu(menubar, tearoff=0)
            debug_menu.add_command(label='Update Debug',
                                command=lambda: self.after(
                                    10, lambda: start_checkupdate(self, version, url, bundle, debug=True)))  # NOQA
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
