import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkfont
from tkinter import messagebox as msgbox
from tkinter import filedialog
import os
import sys
import gettext
from PIL import Image, ImageTk
from modules.config import get_config, config_write_value
from ruamel.yaml import YAML
from modules.util import steam64_to_3, steam64_to_32, steam64_to_2, check_steam_dir

COLOR_DISABLED = '#cfcfcf'
COLOR_CLICKED = '#363636'
COLOR_HOVER = '#f2f2f2'
yaml = YAML()

t = gettext.translation('steamswitcher',
                        localedir='locale',
                        languages=[get_config('locale')],
                        fallback=True)
_ = t.gettext


class DragDropListbox(tk.Listbox):
    '''Listbox with drag reordering of entries'''
    def __init__(self, master, **kw):
        kw['selectmode'] = tk.SINGLE
        tk.Listbox.__init__(self, master, kw)
        self.bind('<Button-1>', self.click)
        self.bind('<B1-Motion>', self.drag)
        self.cur_index = None

    def click(self, event):
        self.cur_index = self.nearest(event.y)

    def drag(self, event):
        i = self.nearest(event.y)
        if i < self.cur_index:
            x = self.get(i)
            self.delete(i)
            self.insert(i+1, x)
            self.cur_index = i
        elif i > self.cur_index:
            x = self.get(i)
            self.delete(i)
            self.insert(i-1, x)
            self.cur_index = i


class AccountButton:
    def __init__(self, master, username, profilename, command=None, rightcommand=None, image='default'):
        self.master = master
        self.frame = tk.Frame(master, borderwidth=3)
        self.command = command
        self.frame.config(background='white')

        self.frame.bind('<Button-1>', lambda event: self.__click())
        self.frame.bind('<ButtonRelease-1>', lambda event: self.__release())
        self.frame.bind('<Button-3>', rightcommand)
        self.frame.bind('<Enter>', lambda event: self.__enter())
        self.frame.bind('<Leave>', lambda event: self.__leave())

        self.onbutton = False
        self.clicked = False
        self.onpress = False
        self.enabled = True
        self.avatar = None

        username_font = tkfont.Font(weight=tkfont.BOLD, size=12, family='Arial')

        if get_config('show_avatar') == 'true':
            self.avatar = tk.Canvas(self.frame, width=40, height=40, bd=0, highlightthickness=0)

            try:
                if image != 'default':
                    img = Image.open(f"avatar/{image}.jpg").resize((40, 40))
                else:
                    raise FileNotFoundError

            except FileNotFoundError:
                img = Image.open(f"asset/default.jpg").resize((40, 40))

            self.imgtk = ImageTk.PhotoImage(img)
            self.avatar.create_image(20, 20, image=self.imgtk)
            self.avatar.pack(side='left', padx=(2, 3), pady=0)

            self.avatar.bind('<Button-1>', lambda event: self.__click())
            self.avatar.bind('<ButtonRelease-1>', lambda event: self.__release())
            self.avatar.bind('<Button-3>', rightcommand)

        self.acc_label = ttk.Label(self.frame, text=username, font=username_font)
        self.acc_label.config(background='white')
        self.acc_label.pack(anchor='w', padx=(3, 0))
        self.acc_label.bind('<Button-1>', lambda event: self.__click())
        self.acc_label.bind('<ButtonRelease-1>', lambda event: self.__release())
        self.acc_label.bind('<Button-3>', rightcommand)

        self.profile_label = ttk.Label(self.frame, text=profilename)
        self.profile_label.config(background='white')
        self.profile_label.pack(anchor='w', padx=(3, 0))
        self.profile_label.bind('<Button-1>', lambda event: self.__click())
        self.profile_label.bind('<ButtonRelease-1>', lambda event: self.__release())
        self.profile_label.bind('<Button-3>', rightcommand)

    def check_cursor(self, event):
        widget = event.widget.winfo_containing(event.x_root, event.y_root)

        if widget in (self.frame, self.acc_label, self.profile_label, self.avatar):
            self.__enter()
        else:
            self.__leave()

    def color_clicked(self):
        self.frame.config(background=COLOR_CLICKED)

        self.acc_label.config(background=COLOR_CLICKED, foreground='white')
        self.profile_label.config(background=COLOR_CLICKED, foreground='white')

    def color_hover(self):
        self.frame.config(background=COLOR_HOVER)

        self.acc_label.config(background=COLOR_HOVER)
        self.profile_label.config(background=COLOR_HOVER)

    def color_normal(self):
        self.frame.config(background='white')

        self.acc_label.config(background='white', foreground='black')
        self.profile_label.config(background='white', foreground='black')

    def __click(self):
        self.clicked = True
        self.color_clicked()
        self.frame.bind('<B1-Motion>', self.check_cursor)
        self.acc_label.bind('<B1-Motion>', self.check_cursor)
        self.profile_label.bind('<B1-Motion>', self.check_cursor)
        if self.avatar:
            self.avatar.bind('<B1-Motion>', self.check_cursor)

    def __release(self):
        self.clicked = False
        self.color_normal()
        self.frame.unbind('<B1-Motion>')
        self.acc_label.unbind('<B1-Motion>')
        self.profile_label.unbind('<B1-Motion>')
        if self.avatar:
            self.avatar.unbind('<B1-Motion>')

        if self.command and self.onbutton:
            self.command()

    def __enter(self):
        self.onbutton = True

        if self.clicked:
            self.color_clicked()
        elif self.enabled:
            self.color_hover()

    def __leave(self):
        self.onbutton = False

        if self.clicked or self.enabled:
            self.color_normal()

    def enable(self):
        self.enabled = True
        self.frame.bind('<Button-1>', lambda event: self.__click())
        self.frame.bind('<ButtonRelease-1>', lambda event: self.__release())
        self.frame.config(background='white')

        self.acc_label.bind('<Button-1>', lambda event: self.__click())
        self.acc_label.bind('<ButtonRelease-1>', lambda event: self.__release())
        self.acc_label.config(background='white')

        self.profile_label.bind('<Button-1>', lambda event: self.__click())
        self.profile_label.bind('<ButtonRelease-1>', lambda event: self.__release())
        self.profile_label.config(background='white')

    def disable(self):
        self.enabled = False
        self.frame.unbind('<Button-1>')
        self.frame.unbind('<ButtonRelease-1>')
        self.frame.config(background=COLOR_DISABLED)

        self.acc_label.unbind('<Button-1>')
        self.acc_label.unbind('<ButtonRelease-1>')
        self.acc_label.config(background=COLOR_DISABLED)

        self.profile_label.unbind('<Button-1>')
        self.profile_label.unbind('<ButtonRelease-1>')
        self.profile_label.config(background=COLOR_DISABLED)

    def pack(self, **kw):
        self.frame.pack(**kw)


class ReadonlyEntryWithLabel:
    def __init__(self, master, label, text):
        self.frame = tk.Frame(master)
        label = tk.Label(self.frame, text=label)
        entry = ttk.Entry(self.frame, width=21)
        entry.insert(0, text)
        entry['state'] = 'readonly'

        self.frame.pack(pady=(6, 0), fill='x')
        label.pack(side='left', padx=(6, 0))
        entry.pack(side='right', padx=(0, 6))

    def pack(self, **kw):
        self.frame.pack(**kw)


class WelcomeWindow(tk.Toplevel):
    def __init__(self, master):
        self.master = master
        tk.Toplevel.__init__(self, self.master)
        self.title(_('Welcome'))
        self.geometry("300x230+650+320")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_window_close)
        self.focus()

        self.radio_var = tk.IntVar()
        self.active_page = 0

        self.upper_frame = tk.Frame(self)
        self.upper_frame.pack(side='top')

        self.ok_button = ttk.Button(self, text=_('OK'), command=self.ok)
        self.ok_button.pack(side='bottom', padx=3, pady=3, fill='x')

        self.welcome_label = tk.Label(self, text=_('Thank you for downloading this app.\nClick OK to continue.'))
        self.welcome_label.pack(expand=True, fill='both')

        self.grab_set()

    def on_window_close(self):
        os.remove('config.yml')
        sys.exit(0)

    def ok(self):
        if self.active_page == 0:
            self.welcome_label.destroy()
            self.top_label = tk.Label(self.upper_frame, text=_('Customize your settings.'))
            self.top_label.pack(pady=(4, 3))
            self.page_1()

        elif self.active_page == 1:
            if self.radio_var.get() == 0:
                self.mode = 'normal'
            elif self.radio_var.get() == 1:
                self.mode = 'express'

            self.radio_frame1.destroy()
            self.radio_frame2.destroy()
            self.page_2()

        elif self.active_page == 2:
            if 'selected' in self.soft_chkb.state():
                self.soft_shutdown = 'true'
            else:
                self.soft_shutdown = 'false'

            if 'selected' in self.autoexit_chkb.state():
                self.autoexit = 'true'
            else:
                self.autoexit = 'false'

            if 'selected' in self.avatar_chkb.state():
                self.avatar = 'true'
            else:
                self.avatar = 'false'

            self.softshutdown_frame.destroy()
            self.autoexit_frame.destroy()
            self.avatar_frame.destroy()

            self.save()
            self.page_3()
        elif self.active_page == 3:
            self.ok_button['text'] = _('Please wait...')
            self.ok_button['state'] = 'disabled'
            self.focus()
            self.master.update()
            self.destroy()

    def page_1(self):
        self.active_page = 1

        self.radio_frame1 = tk.Frame(self)
        self.radio_frame1.pack(side='top', padx=20, pady=(4, 10), fill='x')

        radio_normal = ttk.Radiobutton(self.radio_frame1,
                                       text=_('Normal Mode'),
                                       variable=self.radio_var,
                                       value=0)
        radio_normal.pack(side='top', anchor='w', pady=2)

        tk.Label(self.radio_frame1, justify='left',
                 text=_("In normal mode, you restart Steam\nby clicking 'Restart Steam' button.")).pack(side='left', pady=5)

        self.radio_frame2 = tk.Frame(self)
        self.radio_frame2.pack(side='top', padx=20, pady=(0, 3), fill='x')

        radio_express = ttk.Radiobutton(self.radio_frame2,
                                        text=_('Express Mode'),
                                        variable=self.radio_var,
                                        value=1)
        radio_express.pack(side='top', anchor='w', pady=2)

        tk.Label(self.radio_frame2, justify='left',
                 text=_('In express mode, Steam will be automatically\nrestarted when you change account.')).pack(side='left', pady=5)

    def page_2(self):
        self.active_page = 2

        self.softshutdown_frame = tk.Frame(self)
        self.softshutdown_frame.pack(fill='x', side='top', padx=(14, 0), pady=(4, 0))

        self.soft_chkb = ttk.Checkbutton(self.softshutdown_frame,
                                         text=_('Try to soft shutdown Steam client'))

        self.soft_chkb.state(['!alternate'])
        self.soft_chkb.state(['selected'])

        self.soft_chkb.pack(side='top', anchor='w')
        tk.Label(self.softshutdown_frame, text=_('Shutdown Steam instead of killing Steam process')).pack(side='top', anchor='w')

        self.autoexit_frame = tk.Frame(self)
        self.autoexit_frame.pack(fill='x', side='top', padx=(14, 0), pady=15)

        self.autoexit_chkb = ttk.Checkbutton(self.autoexit_frame,
                                             text=_('Exit app after Steam is restarted'))

        self.autoexit_chkb.state(['!alternate'])
        self.autoexit_chkb.state(['selected'])

        self.autoexit_chkb.pack(side='top', anchor='w')
        tk.Label(self.autoexit_frame, text=_('Exit app automatically after restarting Steam')).pack(side='top', anchor='w')

        self.avatar_frame = tk.Frame(self)
        self.avatar_frame.pack(fill='x', side='top', padx=(14, 0))

        self.avatar_chkb = ttk.Checkbutton(self.avatar_frame,
                                           text=_('Show avatar images'))

        self.avatar_chkb.state(['!alternate'])
        self.avatar_chkb.state(['selected'])

        self.avatar_chkb.pack(side='top', anchor='w')
        tk.Label(self.avatar_frame, text=_('Show avatars in account list')).pack(side='top', anchor='w')

    def page_3(self):
        self.active_page = 3
        self.top_label['text'] = _('Good to go!')

        # tkinter doesn't like three quotes string, so... yeah.
        self.finish_label = tk.Label(self, text=_("Add or import accounts via Menu.\nRight click on accounts to see more options.\n\nYou can change settings in Menu > Settings\nif you don't like the settings you just set.\n\nPlease read GitHub README's How to use-4\nif you are using this app for first time.\n\nYou can open GitHub repo via Menu > About."))
        self.finish_label.pack(expand=True, fill='both')

    def save(self):
        dump_dict = {'locale': get_config('locale'),
                     'try_soft_shutdown': self.soft_shutdown,
                     'autoexit': self.autoexit,
                     'mode': self.mode,
                     'show_avatar': self.avatar}

        with open('config.yml', 'w') as cfg:
            yaml.dump(dump_dict, cfg)


def ask_steam_dir():
    if not check_steam_dir():
        msgbox.showwarning(_('Steam directory invalid'), _('Could not locate Steam directory.') + '\n' +
                           _('Please select Steam directory manually.'))

        while True:
            input_dir = filedialog.askdirectory()

            if os.path.isfile(input_dir + '\\Steam.exe') and os.path.isfile(input_dir + '\\config\\loginusers.vdf'):
                config_write_value('steam_path', input_dir)
                break
            else:
                msgbox.showwarning(_('Warning'),
                                   _('Steam directory is invalid.') + '\n' +
                                   _('Try again.'))
                continue


def steamid_window(master, username, steamid64):
    steamid_window = tk.Toplevel(master)
    steamid_window.geometry()
    steamid_window.title('SteamID')
    steamid_window.geometry("240x180+650+320")
    steamid_window.resizable(False, False)
    steamid_window.focus()

    close_button = ttk.Button(steamid_window, text=_('Close'), command=steamid_window.destroy)
    close_button.pack(side='bottom', pady=(0, 3))

    ReadonlyEntryWithLabel(steamid_window, _('Username'), username).pack(pady=(6, 0), fill='x')
    ReadonlyEntryWithLabel(steamid_window, _('Friend code'), steam64_to_32(steamid64)).pack(pady=(6, 0), fill='x')
    ReadonlyEntryWithLabel(steamid_window, 'SteamID64', steamid64).pack(pady=(6, 0), fill='x')
    ReadonlyEntryWithLabel(steamid_window, 'SteamID2', steam64_to_2(steamid64)).pack(pady=(6, 0), fill='x')
    ReadonlyEntryWithLabel(steamid_window, 'SteamID3', steam64_to_3(steamid64)).pack(pady=(6, 0), fill='x')
