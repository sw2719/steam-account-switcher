import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkfont
from tkinter import messagebox as msgbox
from tkinter import filedialog
import os
import sys
import gettext
import colour
import json
import sv_ttk
import re
from PIL import Image, ImageTk
from modules.config import get_config, config_write_value, config_write_dict, missing_values
from ruamel.yaml import YAML
from modules.util import check_steam_dir, create_shortcut
from modules.steamid import steam64_to_3, steam64_to_32, steam64_to_2
from modules.account import AccountManager


yaml = YAML()

t = gettext.translation('steamswitcher',
                        localedir='locale',
                        languages=[get_config('locale')],
                        fallback=True)
_ = t.gettext


def get_color(key):
    try:
        if sv_ttk.get_theme() == 'light':
            return COLOR_LIGHT[key]
        else:
            return COLOR_DARK[key]

    except KeyError:
        print('WARNING: get_color was called with wrong color key', key)
        return 'black'


def color_fade(widget, **kw):
    if not getattr(widget, '_after_ids', None):
        widget._after_ids = {}

    widget.after_cancel(widget._after_ids.get(list(kw)[0], ' '))

    color_a = tuple(c / 65535 for c in widget.winfo_rgb(widget[list(kw)[0]]))
    color_b = tuple(c / 65535 for c in widget.winfo_rgb(list(kw.values())[0]))

    colors = tuple(colour.rgb2hex(color, force_long=True) for color in colour.color_scale(color_a, color_b, 70))

    def update_widget_after(count=0):
        if len(colors) - 1 <= count:
            return

        else:
            widget.config({list(kw)[0]: colors[count]})
            widget._after_ids.update({list(kw)[0]: widget.after(1, update_widget_after, count+1)})

    update_widget_after()


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
        self.update_color(init=True)

        self.master = master
        self.frame = tk.Frame(master, borderwidth=3)
        self.command = command
        self.frame.config(background=self.normal, cursor='hand2')

        self.frame.bind('<Button-1>', lambda event: self.__click())
        self.frame.bind('<ButtonRelease-1>', lambda event: self.__release(event))
        self.frame.bind('<Button-3>', rightcommand)
        self.frame.bind('<Enter>', lambda event: self.__enter())
        self.frame.bind('<Leave>', lambda event: self.__leave())

        self.is_clicked = False
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
                img = Image.open("asset/default.jpg").resize((40, 40))

            self.imgtk = ImageTk.PhotoImage(img)
            self.avatar.create_image(20, 20, image=self.imgtk)
            self.avatar.pack(side='left', padx=(1, 3), pady=0)

            self.avatar.bind('<Button-1>', lambda event: self.__click())
            self.avatar.bind('<ButtonRelease-1>', lambda event: self.__release(event))
            self.avatar.bind('<Button-3>', rightcommand)

        self.acc_label = ttk.Label(self.frame, text=username, font=username_font)
        self.acc_label.config(background=self.normal, foreground=self.text)
        self.acc_label.pack(anchor='w', padx=(3, 0), pady=(1, 0))
        self.acc_label.bind('<Button-1>', lambda event: self.__click())
        self.acc_label.bind('<ButtonRelease-1>', lambda event: self.__release(event))
        self.acc_label.bind('<Button-3>', rightcommand)

        self.profile_label = ttk.Label(self.frame, text=profilename)
        self.profile_label.config(background=self.normal, foreground=self.text)
        self.profile_label.pack(anchor='w', padx=(3, 0), pady=(2, 0))
        self.profile_label.bind('<Button-1>', lambda event: self.__click())
        self.profile_label.bind('<ButtonRelease-1>', lambda event: self.__release(event))
        self.profile_label.bind('<Button-3>', rightcommand)

    def update_color(self, init=False):
        self.normal = get_color('account_button')
        self.disabled = get_color('account_button_disabled')
        self.clicked = get_color('account_button_clicked')
        self.hover = get_color('account_button_hover')
        self.text = get_color('account_button_text')
        self.text_disabled = get_color('account_button_text_disabled')
        self.text_clicked = get_color('account_button_text_clicked')

        if not init:
            if self.enabled:
                self.frame.configure(background=self.normal)
                self.acc_label.configure(background=self.normal, foreground=self.text)
                self.profile_label.configure(background=self.normal, foreground=self.text)
            else:
                self.frame.config(background=self.disabled)
                self.acc_label.config(background=self.disabled, foreground=self.text_disabled)
                self.profile_label.config(background=self.disabled, foreground=self.text_disabled)

    def color_clicked(self):
        color_fade(self.frame, background=self.clicked)
        color_fade(self.acc_label, background=self.clicked)
        color_fade(self.acc_label, foreground=self.text_clicked)
        color_fade(self.profile_label, background=self.clicked)
        color_fade(self.profile_label, foreground=self.text_clicked)

    def color_hover(self):
        color_fade(self.frame, background=self.hover)
        color_fade(self.acc_label, background=self.hover)
        color_fade(self.profile_label, background=self.hover)

    def color_normal(self):
        color_fade(self.frame, background=self.normal)
        color_fade(self.acc_label, background=self.normal)
        color_fade(self.acc_label, foreground=self.text)
        color_fade(self.profile_label, background=self.normal)
        color_fade(self.profile_label, foreground=self.text)

    def __click(self):
        self.is_clicked = True
        self.color_clicked()

    def __release(self, event):
        self.is_clicked = False
        self.color_normal()

        widget = event.widget.winfo_containing(event.x_root, event.y_root)

        if self.command and widget in (self.frame, self.acc_label, self.profile_label, self.avatar):
            self.command()

    def __enter(self):
        if self.is_clicked:
            self.color_clicked()
        elif self.enabled:
            self.color_hover()

    def __leave(self):
        if self.enabled and not self.is_clicked:
            self.color_normal()

    def enable(self):
        self.enabled = True
        self.frame.bind('<Button-1>', lambda event: self.__click())
        self.frame.bind('<ButtonRelease-1>', lambda event: self.__release(event))
        self.frame.config(background=self.normal, cursor='hand2')

        self.acc_label.bind('<Button-1>', lambda event: self.__click())
        self.acc_label.bind('<ButtonRelease-1>', lambda event: self.__release(event))
        self.acc_label.config(background=self.normal, foreground=self.text)

        self.profile_label.bind('<Button-1>', lambda event: self.__click())
        self.profile_label.bind('<ButtonRelease-1>', lambda event: self.__release(event))
        self.profile_label.config(background=self.normal, foreground=self.text)

        if self.avatar:
            self.avatar.bind('<Button-1>', lambda event: self.__click())
            self.avatar.bind('<ButtonRelease-1>', lambda event: self.__release(event))

    def disable(self, no_fade=False):
        self.enabled = False
        self.frame.unbind('<Button-1>')
        self.frame.unbind('<ButtonRelease-1>')
        self.frame.config(cursor='arrow')

        self.acc_label.unbind('<Button-1>')
        self.acc_label.unbind('<ButtonRelease-1>')
        self.profile_label.unbind('<Button-1>')
        self.profile_label.unbind('<ButtonRelease-1>')

        if self.avatar:
            self.avatar.unbind('<Button-1>')
            self.avatar.unbind('<ButtonRelease-1>')

        if no_fade:
            self.frame.config(background=self.disabled)
            self.acc_label.config(background=self.disabled, foreground=self.text_disabled)
            self.profile_label.config(background=self.disabled, foreground=self.text_disabled)
        else:
            color_fade(self.frame, background=self.disabled)
            color_fade(self.acc_label, background=self.disabled)
            color_fade(self.acc_label, foreground=self.text_disabled)
            color_fade(self.profile_label, background=self.disabled)
            color_fade(self.profile_label, foreground=self.text_disabled)

    def pack(self, **kw):
        self.frame.pack(**kw)


class AccountButtonGrid:
    def __init__(self, master, username, profilename, command=None, rightcommand=None, image='default'):
        self.update_color(init=True)

        self.master = master
        self.frame = tk.Frame(master, borderwidth=3, width=84, height=100)
        self.command = command
        self.frame.config(background=self.normal, cursor='hand2')
        self.frame.pack_propagate(0)

        self.frame.bind('<Button-1>', lambda event: self.__click())
        self.frame.bind('<ButtonRelease-1>', lambda event: self.__release(event))
        self.frame.bind('<Button-3>', rightcommand)
        self.frame.bind('<Enter>', lambda event: self.__enter())
        self.frame.bind('<Leave>', lambda event: self.__leave())

        self.onbutton = False
        self.is_clicked = False
        self.enabled = True
        self.avatar = None
        size = 48

        if get_config('show_avatar') == 'true':
            self.avatar = tk.Canvas(self.frame, width=size, height=size, bd=0, highlightthickness=0)

            try:
                if image != 'default':
                    img = Image.open(f"avatar/{image}.jpg").resize((size, size))
                else:
                    raise FileNotFoundError

            except FileNotFoundError:
                img = Image.open("asset/default.jpg").resize((size, size))

            self.imgtk = ImageTk.PhotoImage(img)
            self.avatar.create_image(size // 2, size // 2, image=self.imgtk)
            self.avatar.pack(side='top', pady=(2, 0))

            self.avatar.bind('<Button-1>', lambda event: self.__click())
            self.avatar.bind('<ButtonRelease-1>', lambda event: self.__release(event))
            self.avatar.bind('<Button-3>', rightcommand)

        self.acc_label = ttk.Label(self.frame)
        self.acc_label.config(background=self.normal, foreground=self.text)
        self.acc_label.pack(side='top', pady=(2, 0))
        self.acc_label.bind('<Button-1>', lambda event: self.__click())
        self.acc_label.bind('<ButtonRelease-1>', lambda event: self.__release(event))
        self.acc_label.bind('<Button-3>', rightcommand)

        if tkfont.Font(font=self.acc_label['font']).measure(username) > 90:
            while tkfont.Font(font=self.acc_label['font']).measure(username) > 90:
                username = username[:-1]
            else:
                username = f'{username}..'

        self.acc_label.configure(text=username)

        self.profile_label = ttk.Label(self.frame)
        self.profile_label.config(background=self.normal, foreground=self.text)
        self.profile_label.pack(side='top')
        self.profile_label.bind('<Button-1>', lambda event: self.__click())
        self.profile_label.bind('<ButtonRelease-1>', lambda event: self.__release(event))
        self.profile_label.bind('<Button-3>', rightcommand)

        if tkfont.Font(font=self.profile_label['font']).measure(profilename) > 90:
            while tkfont.Font(font=self.profile_label['font']).measure(profilename) > 90:
                profilename = profilename[:-1]
            else:
                profilename = f'{profilename}..'

        self.profile_label.configure(text=profilename)

    def update_color(self, init=False):
        self.normal = get_color('account_button')
        self.disabled = get_color('account_button_disabled')
        self.clicked = get_color('account_button_clicked')
        self.hover = get_color('account_button_hover')
        self.text = get_color('account_button_text')
        self.text_disabled = get_color('account_button_text_disabled')
        self.text_clicked = get_color('account_button_text_clicked')

        if not init:
            if self.enabled:
                self.frame.configure(background=self.normal)
                self.acc_label.configure(background=self.normal, foreground=self.text)
                self.profile_label.configure(background=self.normal, foreground=self.text)
            else:
                self.frame.config(background=self.disabled)
                self.acc_label.config(background=self.disabled, foreground=self.text_disabled)
                self.profile_label.config(background=self.disabled, foreground=self.text_disabled)

    def check_cursor(self, event):
        widget = event.widget.winfo_containing(event.x_root, event.y_root)

        if widget in (self.frame, self.acc_label, self.profile_label, self.avatar):
            self.__enter()
        else:
            self.__leave()

    def color_clicked(self):
        color_fade(self.frame, background=self.clicked)
        color_fade(self.acc_label, background=self.clicked)
        color_fade(self.acc_label, foreground=self.text_clicked)
        color_fade(self.profile_label, background=self.clicked)
        color_fade(self.profile_label, foreground=self.text_clicked)

    def color_hover(self):
        color_fade(self.frame, background=self.hover)
        color_fade(self.acc_label, background=self.hover)
        color_fade(self.profile_label, background=self.hover)

    def color_normal(self):
        color_fade(self.frame, background=self.normal)
        color_fade(self.acc_label, background=self.normal)
        color_fade(self.acc_label, foreground=self.text)
        color_fade(self.profile_label, background=self.normal)
        color_fade(self.profile_label, foreground=self.text)

    def __click(self):
        self.is_clicked = True
        self.color_clicked()

    def __release(self, event):
        self.is_clicked = False
        self.color_normal()

        widget = event.widget.winfo_containing(event.x_root, event.y_root)

        if self.command and widget in (self.frame, self.acc_label, self.profile_label, self.avatar):
            self.command()

    def __enter(self):
        if self.is_clicked:
            self.color_clicked()
        elif self.enabled:
            self.color_hover()

    def __leave(self):
        if self.enabled and not self.is_clicked:
            self.color_normal()

    def enable(self):
        self.enabled = True
        self.frame.bind('<Button-1>', lambda event: self.__click())
        self.frame.bind('<ButtonRelease-1>', lambda event: self.__release(event))
        self.frame.config(background=self.normal, cursor='hand2')

        self.avatar.bind('<Button-1>', lambda event: self.__click())
        self.avatar.bind('<ButtonRelease-1>', lambda event: self.__release(event))

        self.acc_label.bind('<Button-1>', lambda event: self.__click())
        self.acc_label.bind('<ButtonRelease-1>', lambda event: self.__release(event))
        self.acc_label.config(background=self.normal, foreground=self.text)

        self.profile_label.bind('<Button-1>', lambda event: self.__click())
        self.profile_label.bind('<ButtonRelease-1>', lambda event: self.__release(event))
        self.profile_label.config(background=self.normal, foreground=self.text)

    def disable(self, no_fade=False):
        self.enabled = False
        self.frame.unbind('<Button-1>')
        self.frame.unbind('<ButtonRelease-1>')
        self.frame.config(cursor='arrow')

        self.avatar.unbind('<Button-1>')
        self.avatar.unbind('<ButtonRelease-1>')
        self.acc_label.unbind('<Button-1>')
        self.acc_label.unbind('<ButtonRelease-1>')
        self.profile_label.unbind('<Button-1>')
        self.profile_label.unbind('<ButtonRelease-1>')

        if no_fade:
            self.frame.config(background=self.disabled)
            self.acc_label.config(background=self.disabled, foreground=self.text_disabled)
            self.profile_label.config(background=self.disabled, foreground=self.text_disabled)
        else:
            color_fade(self.frame, background=self.disabled)
            color_fade(self.acc_label, background=self.disabled)
            color_fade(self.acc_label, foreground=self.text_disabled)
            color_fade(self.profile_label, background=self.disabled)
            color_fade(self.profile_label, foreground=self.text_disabled)

    def grid(self, **kw):
        self.frame.grid(**kw)


class SimpleButton:
    def __init__(self, master, text='', widget='button', textvariable=None, command=None, bd=2):
        self.widget = widget
        self.update_color(init=True)

        self.frame = tk.Frame(master, bg=self.normal, bd=bd)
        self.command = command
        self.button_text = tk.Label(self.frame, bg=self.normal, fg=self.text)

        if textvariable:
            self.button_text['textvariable'] = textvariable
        else:
            self.button_text['text'] = text

        self.button_text.pack(padx=2, pady=1)
        self.enabled = True
        self.is_clicked = False

        self.frame.bind('<Button-1>', lambda event: self.__click())
        self.frame.bind('<ButtonRelease-1>', lambda event: self.__release(event))
        self.frame.bind('<Enter>', lambda event: self.__enter())
        self.frame.bind('<Leave>', lambda event: self.__leave())

        self.button_text.bind('<Button-1>', lambda event: self.__click())
        self.button_text.bind('<ButtonRelease-1>', lambda event: self.__release(event))

    def update_color(self, init=False):
        self.normal = get_color(self.widget)
        self.clicked = get_color(f'{self.widget}_clicked')
        self.hover = get_color(f'{self.widget}_hover')
        self.disabled = get_color('button_disabled')
        self.text = get_color('text')
        self.text_clicked = get_color('text_clicked')
        self.text_disabled = get_color('button_text_disabled')

        if not init:
            if self.enabled:
                self.frame.configure(background=self.normal)
                self.button_text.configure(background=self.normal, foreground=self.text)
            else:
                self.frame.configure(background=self.disabled)
                self.button_text.configure(background=self.disabled, foreground=self.text_disabled)

    def color_clicked(self):
        color_fade(self.frame, background=self.clicked)
        color_fade(self.button_text, background=self.clicked)
        color_fade(self.button_text, foreground=self.text_clicked)

    def color_hover(self):
        color_fade(self.frame, background=self.hover)
        color_fade(self.button_text, background=self.hover)

    def color_normal(self):
        color_fade(self.frame, background=self.normal)
        color_fade(self.button_text, background=self.normal)
        color_fade(self.button_text, foreground=self.text)

    def __click(self):
        self.is_clicked = True
        self.color_clicked()

    def __release(self, event):
        self.is_clicked = False
        widget = event.widget.winfo_containing(event.x_root, event.y_root)

        self.color_normal()

        if self.command and widget in (self.frame, self.button_text):
            self.command()

    def __enter(self):
        if self.enabled:
            self.color_hover()

    def __leave(self):
        if self.enabled and not self.is_clicked:
            self.color_normal()

    def enable(self):
        self.enabled = True
        self.frame.bind('<Button-1>', lambda event: self.__click())
        self.frame.bind('<ButtonRelease-1>', lambda event: self.__release(event))
        self.frame.config(background=self.normal)

        self.button_text.bind('<Button-1>', lambda event: self.__click())
        self.button_text.bind('<ButtonRelease-1>', lambda event: self.__release(event))
        self.button_text.config(background=self.normal, foreground=self.text)

    def disable(self, no_fade=False):
        self.enabled = False
        self.frame.unbind('<Button-1>')
        self.frame.unbind('<ButtonRelease-1>')

        self.button_text.unbind('<Button-1>')
        self.button_text.unbind('<ButtonRelease-1>')

        if no_fade:
            self.frame.config(background=self.disabled)
            self.button_text.config(background=self.disabled, foreground=self.text_disabled)
        else:
            color_fade(self.frame, background=self.disabled)
            color_fade(self.button_text, background=self.disabled)
            color_fade(self.button_text, foreground=self.text_disabled)

    def update_command(self, command):
        self.command = command

    def update_text(self, text):
        self.button_text.config(text=text)

    def pack(self, **kw):
        self.frame.pack(**kw)

    def grid(self, **kw):
        self.frame.grid(**kw)

    def pack_forget(self):
        self.frame.pack_forget()

    def grid_forget(self):
        self.frame.grid_forget()


class ReadonlyEntryWithLabel:
    def __init__(self, master, label, text):
        self.frame = tk.Frame(master)
        label = ttk.Label(self.frame, text=label)
        entry = ttk.Entry(self.frame, width=21,)
        entry.insert(0, text)
        entry['state'] = 'readonly'

        self.frame.pack(pady=(6, 0), fill='x')
        label.pack(side='left', padx=(6, 0))
        entry.pack(side='right', padx=(0, 6))

    def pack(self, **kw):
        self.frame.pack(**kw)


class WelcomeWindow(tk.Toplevel):
    def __init__(self, master, geometry, after_update, debug):
        self.master = master
        tk.Toplevel.__init__(self, self.master)
        self.title(_('Initial Setup'))

        self.geometry(geometry)
        self.resizable(False, False)

        self.after_update = after_update

        if not debug:
            self.protocol("WM_DELETE_WINDOW", self.on_window_close)

        try:
            self.iconbitmap('asset/icon.ico')
        except tk.TclError:
            pass

        self.theme_radio_var = tk.IntVar()
        self.ui_radio_var = tk.IntVar()
        self.mode_radio_var = tk.IntVar()
        self.active_page = 0

        self.upper_frame = tk.Frame(self)
        self.upper_frame.pack(side='top', fill='x')

        self.top_font = tkfont.Font(weight=tkfont.BOLD, size=17, family='Arial')
        self.title_font = tkfont.Font(weight=tkfont.BOLD, size=23, family='Arial')

        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(side='bottom', fill='x', padx=3, pady=3)

        self.button_frame.rowconfigure(0, weight=1)
        self.button_frame.columnconfigure(0, weight=1)
        self.button_frame.columnconfigure(1, weight=1)
        self.button_frame.columnconfigure(2, weight=1)

        self.back_button = ttk.Button(self.button_frame, text=_('Exit'), command=self.back, width=10)
        self.back_button.grid(row=0, column=0, sticky='w')

        self.page_label = ttk.Label(self.button_frame, text='0/6')
        self.page_label.grid(row=0, column=1, sticky='s', padx=3, pady=(0, 10))

        if self.after_update:
            self.page_label['text'] = '0/5'

        self.ok_button = ttk.Button(self.button_frame, text=_('Next'), command=self.ok, width=10)
        self.ok_button.grid(row=0, column=2, sticky='e')

        self.encryption = False
        self.pw = None

        self.encryption_already_enabled = get_config('encryption')

        self.focus_force()
        self.grab_set()

        self.required_pages = []

        # TODO: Actually use this and show user only required pages
        if self.after_update and missing_values:
            if 'theme' in missing_values:
                self.required_pages.append(1)
            if 'ui_mode' in missing_values:
                self.required_pages.append(2)
            if 'mode' in missing_values:
                self.required_pages.append(3)
            if 'password' in missing_values or 'encryption' in missing_values:
                self.required_pages.append(4)
            if 'try_soft_shutdown' in missing_values or 'autoexit' in missing_values or 'show_avatar' in missing_values:
                self.required_pages.append(5)

        self.page_0()

    def on_window_close(self):
        os.remove('config.json')
        sys.exit(0)

    def back(self):
        if self.active_page == 0:
            self.on_window_close()

        elif self.active_page == 1:
            self.top_label.destroy()
            self.radio_frame1.destroy()
            self.radio_frame2.destroy()
            self.page_0()
            self.focus()

        elif self.active_page == 2:
            self.radio_frame1.destroy()
            self.radio_frame2.destroy()
            self.page_1()
            self.focus()

        elif self.active_page == 3:
            self.radio_frame1.destroy()
            self.radio_frame2.destroy()
            self.page_2()
            self.focus()

        elif self.active_page == 4:
            self.innerframe.destroy()
            self.page_3()
            self.focus()

        elif self.active_page == 'pw1':
            self.innerframe.destroy()
            self.page_4()
            self.ok_button['state'] = 'normal'
            self.ok_button['text'] = _('Next')
            self.focus()

        elif self.active_page == 'pw2':
            self.innerframe.destroy()
            self.password_page()
            self.ok_button['text'] = _('Next (Enter)')
            self.focus()

        elif self.active_page == 5:
            self.softshutdown_frame.destroy()
            self.autoexit_frame.destroy()
            self.avatar_frame.destroy()

            if self.encryption == 'true':
                self.password_page()
            else:
                self.page_4()
                self.ok_button['text'] = _('Next')
            self.focus()

        elif self.active_page == 6:
            self.innerframe.destroy()
            self.ok_button['text'] = _('Next')
            self.page_5()

        if type(self.active_page) == int:
            if self.after_update:
                self.page_label['text'] = str(self.active_page) + '/5'
            else:
                self.page_label['text'] = str(self.active_page) + '/6'

    def ok(self):
        if self.active_page == 0:
            self.title_label.destroy()
            self.welcome_label.destroy()
            self.top_label = tk.Label(self.upper_frame, font=self.top_font)
            self.top_label.pack(side='left', padx=(10, 0), pady=10)
            self.back_button['text'] = _('Back')
            self.page_1()
            self.focus()

        elif self.active_page == 1:
            if sv_ttk.get_theme() == 'light':
                self.theme = 'light'
            else:
                self.theme = 'dark'

            self.radio_frame1.destroy()
            self.radio_frame2.destroy()
            self.bottomframe.destroy()
            self.page_2()
            self.focus()

        elif self.active_page == 2:
            if self.ui_radio_var.get() == 0:
                self.ui_mode = 'list'
            elif self.ui_radio_var.get() == 1:
                self.ui_mode = 'grid'

            self.radio_frame1.destroy()
            self.radio_frame2.destroy()
            self.page_3()
            self.focus()

        elif self.active_page == 3:
            if self.mode_radio_var.get() == 0:
                self.mode = 'normal'
            elif self.mode_radio_var.get() == 1:
                self.mode = 'express'

            self.radio_frame1.destroy()
            self.radio_frame2.destroy()
            self.page_4()
            self.focus()

        elif self.active_page == 4:
            if 'selected' in self.encryption_chkb.state():
                self.encryption = 'true'
            else:
                self.encryption = 'false'

            self.innerframe.destroy()

            if self.encryption == 'true':
                self.ok_button['text'] = _('Next (Enter)')
                self.password_page()
            else:
                self.page_5()

                if self.after_update:
                    self.ok_button['text'] = _('Finish')
                else:
                    self.ok_button['text'] = _('Next')

                self.focus()

        elif self.active_page == 'pw1':
            self.innerframe.destroy()
            self.password_confirm_page()
            self.ok_button['text'] = _('Confirm (Enter)')

        elif self.active_page == 'pw2':
            self.pw = self.pw_var.get()
            del self.pw_var
            self.innerframe.destroy()
            self.page_5()

            if self.after_update:
                self.ok_button['text'] = _('Finish')
            else:
                self.ok_button['text'] = _('Next')
            self.focus()

        elif self.active_page == 5:
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

            if self.after_update:
                self.save()
                self.destroy()
                return
            else:
                self.ok_button['text'] = _('Finish')
                self.page_6()
                self.focus()

        elif self.active_page == 6:
            if 'selected' in self.shortcut_chkb.state():
                create_shortcut()

            self.ok_button['text'] = _('Please wait...')
            self.ok_button['state'] = 'disabled'
            self.focus()
            self.save()
            self.destroy()
            return

        if type(self.active_page) == int:
            if self.after_update:
                self.page_label['text'] = str(self.active_page) + '/5'
            else:
                self.page_label['text'] = str(self.active_page) + '/6'

    def page_0(self):
        self.active_page = 0
        self.title_label = tk.Label(self, text=_('Welcome'), font=self.title_font)

        if self.after_update:
            self.title_label['text'] = _('Update complete')

        self.welcome_label = tk.Label(self, text=_("Click 'Next' to continue."))
        self.back_button['text'] = _('Exit')
        self.title_label.pack(expand=True, pady=1)
        self.welcome_label.pack(expand=True, pady=1)

    def page_1(self):
        self.active_page = 1
        self.top_label['text'] = _('UI Appearance')
        self.bottomframe = tk.Frame(self)
        self.bottomframe.pack(side='bottom', fill='x')

        icon_w = 60
        icon_h = 96

        self.radio_frame1 = tk.Frame(self)
        self.radio_frame1.pack(side='left', padx=(50, 0), pady=5)

        self.light_canvas = tk.Canvas(self.radio_frame1, width=icon_w, height=icon_h, bd=0, highlightthickness=0)
        img = Image.open("asset/light.png").resize((icon_w, icon_h))

        self.light_imgtk = ImageTk.PhotoImage(img)
        self.light_canvas.create_image(icon_w / 2, icon_h / 2, image=self.light_imgtk)
        self.light_canvas.pack(side='top', padx=0, pady=5)

        radio_light = ttk.Radiobutton(self.radio_frame1,
                                      text=_('Light Theme'),
                                      variable=self.theme_radio_var,
                                      value=0,
                                      command=sv_ttk.use_light_theme)
        radio_light.pack(side='top', pady=2)

        self.radio_frame2 = tk.Frame(self)
        self.radio_frame2.pack(side='right', padx=(0, 50), pady=5)

        self.dark_canvas = tk.Canvas(self.radio_frame2, width=icon_w, height=icon_h, bd=0, highlightthickness=0)
        img = Image.open("asset/dark.png").resize((icon_w, icon_h))
        self.dark_imgtk = ImageTk.PhotoImage(img)
        self.dark_canvas.create_image(icon_w / 2, icon_h / 2, image=self.dark_imgtk)
        self.dark_canvas.pack(side='top', padx=0, pady=5)

        radio_dark = ttk.Radiobutton(self.radio_frame2,
                                     text=_('Dark Theme'),
                                     variable=self.theme_radio_var,
                                     value=1,
                                     command=sv_ttk.use_dark_theme)
        radio_dark.pack(side='top', pady=2)

        if sv_ttk.get_theme() == 'dark':
            self.theme_radio_var.set(1)

    def page_2(self):
        self.active_page = 2
        self.top_label['text'] = _('UI Appearance')
        self.radio_frame1 = tk.Frame(self)
        self.radio_frame1.pack(side='left', padx=(30, 0), pady=5)
        self.list_canvas = tk.Canvas(self.radio_frame1, width=50, height=50, bd=0, highlightthickness=0)

        if not self.theme_radio_var.get():
            img_list = Image.open("asset/list.png").resize((50, 50))
            img_grid = Image.open("asset/grid.png").resize((50, 50))
        else:
            img_list = Image.open("asset/list_white.png").resize((50, 50))
            img_grid = Image.open("asset/grid_white.png").resize((50, 50))

        self.list_imgtk = ImageTk.PhotoImage(img_list)
        self.list_canvas.create_image(25, 25, image=self.list_imgtk)
        self.list_canvas.pack(side='top', padx=0, pady=5)

        radio_list = ttk.Radiobutton(self.radio_frame1,
                                     text=_('List Mode'),
                                     variable=self.ui_radio_var,
                                     value=0,
                                     style='welcome.TRadiobutton')
        radio_list.pack(side='top', pady=2)

        tk.Label(self.radio_frame1, justify='left',
                 text=_("Display accounts\nin vertical list")).pack(side='bottom', pady=5)

        self.radio_frame2 = tk.Frame(self)
        self.radio_frame2.pack(side='right', padx=(0, 30), pady=5)

        self.grid_canvas = tk.Canvas(self.radio_frame2, width=50, height=50, bd=0, highlightthickness=0)

        self.grid_imgtk = ImageTk.PhotoImage(img_grid)
        self.grid_canvas.create_image(25, 25, image=self.grid_imgtk)
        self.grid_canvas.pack(side='top', padx=0, pady=5)

        radio_grid = ttk.Radiobutton(self.radio_frame2,
                                     text=_('Grid Mode'),
                                     variable=self.ui_radio_var,
                                     value=1,
                                     style='welcome.TRadiobutton')
        radio_grid.pack(side='top', pady=2)

        tk.Label(self.radio_frame2, justify='left',
                 text=_('Display accounts\nin 3 x n grid')).pack(side='bottom', pady=5)

        if get_config('ui_mode') == 'grid':
            self.ui_radio_var.set(1)

    def page_3(self):
        self.active_page = 3
        self.top_label['text'] = _('Steam restart mode')

        if get_config('mode') == 'express':
            self.mode_radio_var.set(1)

        self.radio_frame1 = tk.Frame(self)
        self.radio_frame1.pack(side='top', padx=20, pady=(4, 10), fill='x')

        radio_normal = ttk.Radiobutton(self.radio_frame1,
                                       text=_('Normal Mode'),
                                       variable=self.mode_radio_var,
                                       value=0,
                                       style='welcome.TRadiobutton')
        radio_normal.pack(side='top', anchor='w', pady=2)

        tk.Label(self.radio_frame1, justify='left',
                 text=_("In normal mode, you restart Steam\nby clicking 'Restart Steam' button.")).pack(side='left', pady=5)

        self.radio_frame2 = tk.Frame(self)
        self.radio_frame2.pack(side='top', padx=20, pady=(0, 3), fill='x')

        radio_express = ttk.Radiobutton(self.radio_frame2,
                                        text=_('Express Mode'),
                                        variable=self.mode_radio_var,
                                        value=1,
                                        style='welcome.TRadiobutton')
        radio_express.pack(side='top', anchor='w', pady=2)

        tk.Label(self.radio_frame2, justify='left',
                 text=_('In express mode, Steam will be automatically\nrestarted when you change account.')).pack(side='left', pady=5)

    def page_4(self):
        self.active_page = 4
        self.top_label['text'] = _('Encryption Settings')

        self.innerframe = ttk.Frame(self)
        self.innerframe.pack(side='top', padx=0, pady=(0, 8), fill='both', expand=True)

        encryption_frame = ttk.Frame(self.innerframe)
        encryption_frame.pack(side='top', fill='y', expand=True, pady=5)

        self.encryption_chkb = ttk.Checkbutton(encryption_frame, text=_('Encrypt accounts data'), style='Switch.TCheckbutton')
        self.encryption_chkb.pack(pady=(8, 0))

        encryption_info = ttk.Label(encryption_frame,
                                    text=_('Enable to encrypt accounts data with a password.') + '\n' +
                                         _('STRONGLY recommended when using Password Saving.') + '\n' +
                                         _('Uses AES-128-CBC-HMAC-SHA256.'),
                                    justify=tk.CENTER)
        encryption_info.pack(expand=True, fill='both')

        if self.encryption == 'true':
            self.encryption_chkb.state(['selected'])

        if self.encryption_already_enabled == 'true':
            encryption_info['text'] = _("Encryption is already enabled.\nClick 'Next' to continue.")
            self.encryption_chkb.state(['disabled'])

    def password_page(self):
        self.active_page = 'pw1'
        self.top_label['text'] = _('Set Password')
        self.pw_var = tk.StringVar()
        self.ok_button['state'] = 'disabled'

        self.innerframe = ttk.Frame(self)
        self.innerframe.pack(side='top', fill='both', expand=True)

        def check_pw(sv):
            nonlocal prompt

            pw = sv.get()

            try:
                last_ch = pw[-1]
                if last_ch == ' ':
                    sv.set(pw[:-1])
                    return
            except IndexError:
                pass

            conditions = re.search('[a-zA-Z]', pw) and re.search('[0-9]', pw) and len(pw) >= 8 and pw.strip() == pw

            if conditions:
                prompt['foreground'] = get_color('autologin_text_avail')
                self.ok_button['state'] = 'normal'
            else:
                prompt['foreground'] = ''
                self.ok_button['state'] = 'disabled'

        ttk.Label(self.innerframe,
                  text=_('Enter a password to use for encryption.') + '\n' +
                       _('You will have to enter it every time you open the app.') + '\n' +
                       _('The more complex it is, the better.'),
                  justify=tk.CENTER).pack(pady=(2, 0))

        ttk.Label(self.innerframe,
                  text=_('Keep in mind that if you forget it,') + '\n' +
                       _('you will have to reset the accounts data!'),
                  justify=tk.CENTER, foreground='red').pack(pady=(6, 0))

        entry_frame = ttk.Frame(self.innerframe)
        entry_frame.pack(side=tk.BOTTOM, fill=tk.X)

        pw_entry = ttk.Entry(entry_frame, show="⬤", justify=tk.CENTER, textvariable=self.pw_var)
        pw_entry.pack(side=tk.LEFT, padx=(3, 0), fill=tk.X, expand=True)

        pw_entry.bind('<Control-x>', lambda e: 'break')
        pw_entry.bind('<Control-c>', lambda e: 'break')
        pw_entry.bind('<Control-v>', lambda e: 'break')
        pw_entry.bind('<Button-3>', lambda e: 'break')

        pw_entry.focus()

        self.pw_var.trace("w", lambda name, index, mode, sv=self.pw_var: check_pw(sv))

        check_var = tk.IntVar()

        checkbutton = ttk.Checkbutton(entry_frame,
                                      text=_('Show'),
                                      variable=check_var,
                                      style='Toggle.TButton')
        checkbutton.pack(side=tk.RIGHT, padx=3)

        def on_show_checkbutton():
            if check_var.get():
                pw_entry['show'] = ''
                checkbutton['text'] = _('Hide')
            else:
                pw_entry['show'] = '⬤'
                checkbutton['text'] = _('Show')

        checkbutton['command'] = on_show_checkbutton

        prompt = ttk.Label(self.innerframe, text=_('At least 8 characters\nMust contain at least one alphabet and a number'),
                           justify=tk.CENTER)
        prompt.pack(side=tk.BOTTOM, padx=3, pady=3)

        def on_return(e):
            if 'disabled' not in self.ok_button.state():
                self.ok()

        pw_entry.bind('<Return>',  on_return)

    def password_confirm_page(self):
        self.active_page = 'pw2'
        self.top_label['text'] = _('Confirm Password')
        pw_var = tk.StringVar()
        self.ok_button['state'] = 'disabled'
        self.ok_button['text'] = _('Confirm (Enter)')

        self.innerframe = ttk.Frame(self)
        self.innerframe.pack(side='top', padx=0, pady=(0, 0), fill='both', expand=True)

        def check_pw(sv):
            nonlocal prompt

            pw = sv.get()

            try:
                last_ch = pw[-1]
                if last_ch == ' ':
                    sv.set(pw[:-1])
                    return
            except IndexError:
                pass

            if pw == self.pw_var.get():
                prompt['foreground'] = get_color('autologin_text_avail')
                prompt['text'] = _('Passwords match!')
                self.ok_button['state'] = 'normal'
            else:
                prompt['foreground'] = ''
                prompt['text'] = _('Passwords do not match')
                self.ok_button['state'] = 'disabled'

        ttk.Label(self.innerframe,
                  text=_('Enter the same password once again to confirm.'),
                  justify=tk.CENTER).pack(pady=(5, 0))

        entry_frame = ttk.Frame(self.innerframe)
        entry_frame.pack(side=tk.BOTTOM, fill=tk.X)

        pw_entry = ttk.Entry(entry_frame, show="⬤", justify=tk.CENTER, textvariable=pw_var)
        pw_entry.pack(side=tk.LEFT, padx=(3, 0), fill=tk.X, expand=True)

        pw_entry.bind('<Control-x>', lambda e: 'break')
        pw_entry.bind('<Control-c>', lambda e: 'break')
        pw_entry.bind('<Control-v>', lambda e: 'break')
        pw_entry.bind('<Button-3>', lambda e: 'break')

        pw_entry.focus()

        pw_var.trace("w", lambda name, index, mode, sv=pw_var: check_pw(sv))

        check_var = tk.IntVar()

        checkbutton = ttk.Checkbutton(entry_frame,
                                      text=_('Show'),
                                      variable=check_var,
                                      style='Toggle.TButton')
        checkbutton.pack(side=tk.RIGHT, padx=3)

        def on_show_checkbutton():
            if check_var.get():
                pw_entry['show'] = ''
                checkbutton['text'] = _('Hide')
            else:
                pw_entry['show'] = '⬤'
                checkbutton['text'] = _('Show')

        checkbutton['command'] = on_show_checkbutton

        prompt = ttk.Label(self.innerframe, text=_('Passwords do not match'),
                           justify=tk.CENTER)
        prompt.pack(side=tk.BOTTOM, padx=3, pady=3)

        def on_return(e):
            if 'disabled' not in self.ok_button.state():
                self.ok()

        pw_entry.bind('<Return>', on_return)

    def page_5(self):
        self.active_page = 5
        self.top_label['text'] = _('Other settings')

        self.softshutdown_frame = tk.Frame(self)
        self.softshutdown_frame.pack(fill='x', side='top', padx=(14, 0), pady=(4, 0))

        self.soft_chkb = ttk.Checkbutton(self.softshutdown_frame,
                                         text=_('Try to soft shutdown Steam client'),
                                         style='welcome.TCheckbutton')

        self.soft_chkb.state(['!alternate'])
        self.soft_chkb.state(['selected'])

        self.soft_chkb.pack(side='top', anchor='w')
        ttk.Label(self.softshutdown_frame, text=_('Shutdown Steam instead of killing Steam process')).pack(side='top', anchor='w')

        self.autoexit_frame = tk.Frame(self)
        self.autoexit_frame.pack(fill='x', side='top', padx=(14, 0), pady=15)

        self.autoexit_chkb = ttk.Checkbutton(self.autoexit_frame,
                                             text=_('Exit app after Steam is restarted'),
                                             style='welcome.TCheckbutton')

        self.autoexit_chkb.state(['!alternate'])
        self.autoexit_chkb.state(['selected'])

        self.autoexit_chkb.pack(side='top', anchor='w')
        ttk.Label(self.autoexit_frame, text=_('Exit app automatically after restarting Steam')).pack(side='top', anchor='w')

        self.avatar_frame = tk.Frame(self)
        self.avatar_frame.pack(fill='x', side='top', padx=(14, 0))

        self.avatar_chkb = ttk.Checkbutton(self.avatar_frame,
                                           text=_('Show avatar images'),
                                           style='welcome.TCheckbutton')

        self.avatar_chkb.state(['!alternate'])
        self.avatar_chkb.state(['selected'])

        if self.ui_mode == 'grid':
            self.avatar_chkb.state(['disabled'])

        self.avatar_chkb.pack(side='top', anchor='w')
        ttk.Label(self.avatar_frame, text=_('Show avatars in account list')).pack(side='top', anchor='w')

    def page_6(self):
        self.active_page = 6
        self.top_label['text'] = _('Good to go!')

        self.innerframe = ttk.Frame(self)
        self.innerframe.pack(fill='both', expand=True)

        self.shortcut_chkb = ttk.Checkbutton(self.innerframe,
                                             text=_('Create a desktop shortcut'),
                                             style='welcome.TCheckbutton')
        self.shortcut_chkb.state(['!alternate'])
        self.shortcut_chkb.state(['!selected'])

        self.shortcut_chkb.pack(side='bottom', pady=(3, 0))

        # tkinter doesn't like three quotes string, so... yeah.
        self.finish_label = tk.Label(self.innerframe,
                                     text=_("Add or import accounts via Menu.\nRight click on accounts to see more options.\n\nYou can change settings in Menu > Settings\nif you don't like the settings you just set.\n\nPlease read GitHub README's How to use-4\nif you are using this app for first time.\n\nYou can open GitHub repo via Menu > About."))
        self.finish_label.pack(expand=True, fill='both')

    def save(self):
        dump_dict = {'locale': get_config('locale'),
                     'try_soft_shutdown': self.soft_shutdown,
                     'autoexit': self.autoexit,
                     'mode': self.mode,
                     'show_avatar': self.avatar,
                     'last_pos': get_config('last_pos'),
                     'steam_path': get_config('steam_path'),
                     'ui_mode': self.ui_mode,
                     'theme': self.theme,
                     'encryption': self.encryption}

        config_write_dict(dump_dict)

        if self.encryption == 'true' and not self.encryption_already_enabled == 'true':
            AccountManager.create_encrypted_json_file(self.pw)


class ToolTipWindow(object):
    '''
    create a tooltip for a given widget
    '''
    def __init__(self, widget, text='widget info', center=False):
        self.widget = widget
        self.text = text
        self.center = center
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.close)

    def enter(self, event=None):
        x = y = 0
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx()
        y += self.widget.winfo_rooty() + 30

        self.win = tk.Toplevel(self.widget)
        self.win.wm_overrideredirect(True)

        label = tk.Label(self.win, text=self.text, justify='left',
                         relief='solid', borderwidth=1)
        label.pack(ipadx=1)

        if self.center:
            d = self.win.winfo_width() - self.widget.winfo_width()
            x += d // 2

        self.win.wm_geometry("+%d+%d" % (x, y))

    def close(self, event=None):
        if self.win:
            self.win.destroy()


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


def steamid_window(master, username, steamid64, geometry):
    steamid_window = tk.Toplevel(master)
    steamid_window.geometry(geometry)
    steamid_window.title('SteamID')
    steamid_window.bind('<Escape>', lambda event: steamid_window.destroy())
    steamid_window.resizable(False, False)
    steamid_window.focus()

    try:
        steamid_window.iconbitmap('asset/icon.ico')
    except tk.TclError:
        pass

    close_button = ttk.Button(steamid_window, text=_('Close'), command=steamid_window.destroy)
    close_button.pack(side='bottom', pady=(0, 3))

    ReadonlyEntryWithLabel(steamid_window, _('Username'), username).pack(pady=(6, 0), fill='x')
    ReadonlyEntryWithLabel(steamid_window, _('Friend code'), steam64_to_32(steamid64)).pack(pady=(6, 0), fill='x')
    ReadonlyEntryWithLabel(steamid_window, 'SteamID64', steamid64).pack(pady=(6, 0), fill='x')
    ReadonlyEntryWithLabel(steamid_window, 'SteamID2', steam64_to_2(steamid64)).pack(pady=(6, 0), fill='x')
    ReadonlyEntryWithLabel(steamid_window, 'SteamID3', steam64_to_3(steamid64)).pack(pady=(6, 0), fill='x')


class ManageEncryptionWindow(tk.Toplevel):
    def __init__(self, geometry, acm):
        super().__init__()
        self.geometry(geometry)
        self.title(_('Encryption Settings'))
        self.resizable(False, False)
        self.active_page = None
        self.upper_frame = tk.Frame(self)
        self.upper_frame.pack(side='top', fill='x')
        self.top_font = tkfont.Font(weight=tkfont.BOLD, size=17)
        self.value_font = tkfont.Font(weight=tkfont.BOLD, size=13)
        self.top_label = ttk.Label(self.upper_frame, font=self.top_font)
        self.top_label.pack(side='left', padx=(10, 0), pady=10)
        self.acm = acm

        self.focus()
        self.grab_set()

        self.main_window()

    def main_window(self):
        self.active_page = 'main'
        self.top_label['text'] = _('Encryption Settings')
        self.bottomframe = ttk.Frame(self)
        self.bottomframe.pack(side='bottom')

        self.bottomframe.rowconfigure(0, weight=1)
        self.bottomframe.columnconfigure(0, weight=1)
        self.bottomframe.columnconfigure(1, weight=1)

        self.close_button = ttk.Button(self.bottomframe, text=_('Close'), command=self.destroy, style='Accent.TButton')
        self.close_button.grid(row=0, column=0, pady=3, padx=3)

        self.innerframe = ttk.Frame(self)
        self.innerframe.pack(side='top', padx=0, pady=(0, 8), fill='both', expand=True)

        encryption_frame = ttk.Frame(self.innerframe)
        encryption_frame.pack(side='top', fill='x', pady=5)

        self.encryption_status = ttk.Label(encryption_frame, font=self.value_font)
        self.encryption_status.pack(pady=(8, 0))

        self.encryption_button = ttk.Button(self.bottomframe)
        self.encryption_button.grid(row=0, column=1, padx=(0, 3))

        self.change_password_button = ttk.Button(self.bottomframe, text=_('Change Password'))

        if get_config('encryption') == 'true':
            self.encryption_status.config(text=_('Encryption is enabled'), foreground=get_color('autologin_text_avail'))
            self.encryption_button.config(text=_('Disable Encryption'), command=self.disable_encryption)
            self.change_password_button.grid(row=0, column=2, padx=(0, 3))
            self.change_password_button['command'] = self.ok
            self.bottomframe.columnconfigure(2, weight=1)

            ttk.Label(self.innerframe,
                      text=_('Your accounts data is encrypted.'),
                      justify=tk.CENTER).pack(expand=True)


        else:
            self.encryption_status.config(text=_('Encryption is disabled'), foreground=get_color('autologin_text_unavail'))
            self.encryption_button.config(text=_('Enable Encryption'), command=self.ok)

            ttk.Label(self.innerframe,
                      text=_('Enable to encrypt accounts data with a password.') + '\n' +
                           _('STRONGLY recommended when using Password saving.') + '\n' +
                           _('Uses AES-128-CBC-HMAC-SHA256.'), justify=tk.CENTER).pack(expand=True)

    def back(self):
        if self.active_page == 'pw1':
            self.innerframe.destroy()
            del self.pw_var
            self.main_window()
        elif self.active_page == 'pw2':
            self.innerframe.destroy()
            self.password_page()

    def disable_encryption(self):
        if msgbox.askyesno(_('Disable Encryption'), _('Are you sure you want to disable encryption?'), parent=self):
            config_write_value('encryption', 'false')
            self.acm.disable_encryption()
            self.bottomframe.destroy()
            self.innerframe.destroy()
            self.main_window()

    def ok(self):
        if self.active_page == 'main':
            self.bottomframe.destroy()
            self.innerframe.destroy()
            self.password_page()
        elif self.active_page == 'pw1':
            self.innerframe.destroy()
            self.active_page = 'pw2'
            self.password_confirm_page()
        elif self.active_page == 'pw2':
            pw = self.pw_var.get()
            self.acm.set_master_password(pw)
            config_write_value('encryption', 'true')
            self.innerframe.destroy()
            self.main_window()
            del self.pw_var

    def password_page(self):
        self.active_page = 'pw1'
        self.top_label['text'] = _('Set Password')
        self.pw_var = tk.StringVar()

        self.innerframe = ttk.Frame(self)
        self.innerframe.pack(side='top', padx=0, pady=0, fill='both', expand=True)

        password_button_frame = ttk.Frame(self.innerframe)
        password_button_frame.pack(side='bottom')
        ok_button = ttk.Button(password_button_frame, text=_('OK (Enter)'), command=self.ok, style='Accent.TButton', state='disabled')
        cancel_button = ttk.Button(password_button_frame, text=_('Cancel'), command=self.back)

        cancel_button.grid(row=0, column=0, padx=3, pady=3)
        ok_button.grid(row=0, column=1, padx=(0, 3), pady=3)

        def check_pw(sv):
            nonlocal prompt

            pw = sv.get()

            try:
                last_ch = pw[-1]
                if last_ch == ' ':
                    sv.set(pw[:-1])
                    return
            except IndexError:
                pass

            conditions = re.search('[a-zA-Z]', pw) and re.search('[0-9]', pw) and len(pw) >= 8 and pw.strip() == pw

            if conditions:
                prompt['foreground'] = get_color('autologin_text_avail')
                ok_button['state'] = 'normal'
            else:
                prompt['foreground'] = ''
                ok_button['state'] = 'disabled'

        ttk.Label(self.innerframe,
                  text=_('Enter a password to use for encryption.') + '\n' +
                       _('You will have to enter it every time you open the app.') + '\n' +
                       _('The more complex it is, the better.'),
                  justify=tk.CENTER).pack(pady=(2, 0))

        ttk.Label(self.innerframe,
                  text=_('Keep in mind that if you forget it,') + '\n' +
                       _('you will have to reset the accounts data!'),
                  justify=tk.CENTER, foreground='red').pack(pady=(6, 0))

        entry_frame = ttk.Frame(self.innerframe)
        entry_frame.pack(side=tk.BOTTOM, fill=tk.X)

        pw_entry = ttk.Entry(entry_frame, show="⬤", justify=tk.CENTER, textvariable=self.pw_var)
        pw_entry.bind('<Control-x>', lambda e: 'break')
        pw_entry.bind('<Control-c>', lambda e: 'break')
        pw_entry.bind('<Control-v>', lambda e: 'break')
        pw_entry.bind('<Button-3>', lambda e: 'break')
        pw_entry.pack(side=tk.LEFT, padx=(3, 0), fill=tk.X, expand=True)
        pw_entry.focus()

        self.pw_var.trace("w", lambda name, index, mode, sv=self.pw_var: check_pw(sv))

        check_var = tk.IntVar()

        checkbutton = ttk.Checkbutton(entry_frame,
                                      text=_('Show'),
                                      variable=check_var,
                                      style='Toggle.TButton')
        checkbutton.pack(side=tk.RIGHT, padx=3)

        def on_show_checkbutton():
            if check_var.get():
                pw_entry['show'] = ''
                checkbutton['text'] = _('Hide')
            else:
                pw_entry['show'] = '⬤'
                checkbutton['text'] = _('Show')

        checkbutton['command'] = on_show_checkbutton

        prompt = ttk.Label(self.innerframe, text=_('At least 8 characters\nMust contain at least one alphabet and a number'),
                           justify=tk.CENTER)
        prompt.pack(side=tk.BOTTOM, padx=3, pady=3)

        def on_return(e):
            if 'disabled' not in ok_button.state():
                self.ok()

        pw_entry.bind('<Return>', on_return)

    def password_confirm_page(self):
        self.active_page = 'pw2'
        self.top_label['text'] = _('Confirm Password')
        pw_var = tk.StringVar()

        self.innerframe = ttk.Frame(self)
        self.innerframe.pack(side='top', padx=0, pady=0, fill='both', expand=True)

        password_button_frame = ttk.Frame(self.innerframe)
        password_button_frame.pack(side='bottom')
        confirm_button = ttk.Button(password_button_frame, text=_('Confirm (Enter)'), style='Accent.TButton',
                                    state='disabled', command=self.ok)
        cancel_button = ttk.Button(password_button_frame, text=_('Back'), command=self.back)

        cancel_button.grid(row=0, column=0, padx=3, pady=3)
        confirm_button.grid(row=0, column=1, padx=(0, 3), pady=3)

        def check_pw(sv):
            nonlocal prompt

            pw = sv.get()

            try:
                last_ch = pw[-1]
                if last_ch == ' ':
                    sv.set(pw[:-1])
                    return
            except IndexError:
                pass

            if pw == self.pw_var.get():
                prompt['foreground'] = get_color('autologin_text_avail')
                prompt['text'] = _('Passwords match!')
                confirm_button['state'] = 'normal'
            else:
                prompt['foreground'] = ''
                prompt['text'] = _('Passwords do not match')
                confirm_button['state'] = 'disabled'

        ttk.Label(self.innerframe,
                  text=_('Enter the same password once again to confirm.'),
                  justify=tk.CENTER).pack(pady=(5, 0))

        entry_frame = ttk.Frame(self.innerframe)
        entry_frame.pack(side=tk.BOTTOM, fill=tk.X)

        pw_entry = ttk.Entry(entry_frame, show="⬤", justify=tk.CENTER, textvariable=pw_var)
        pw_entry.pack(side=tk.LEFT, padx=(3, 0), fill=tk.X, expand=True)
        pw_entry.bind('<Control-x>', lambda e: 'break')
        pw_entry.bind('<Control-c>', lambda e: 'break')
        pw_entry.bind('<Control-v>', lambda e: 'break')
        pw_entry.bind('<Button-3>', lambda e: 'break')
        pw_entry.focus()

        pw_var.trace("w", lambda name, index, mode, sv=pw_var: check_pw(sv))

        check_var = tk.IntVar()

        checkbutton = ttk.Checkbutton(entry_frame,
                                      text=_('Show'),
                                      variable=check_var,
                                      style='Toggle.TButton')
        checkbutton.pack(side=tk.RIGHT, padx=3)

        def on_show_checkbutton():
            if check_var.get():
                pw_entry['show'] = ''
                checkbutton['text'] = _('Hide')
            else:
                pw_entry['show'] = '⬤'
                checkbutton['text'] = _('Show')

        checkbutton['command'] = on_show_checkbutton

        prompt = ttk.Label(self.innerframe, text=_('Passwords do not match'),
                           justify=tk.CENTER)
        prompt.pack(side=tk.BOTTOM, padx=3, pady=3)

        def on_return(e):
            if 'disabled' not in confirm_button.state():
                self.ok()

        pw_entry.bind('<Return>', on_return)

if __name__ == '__main__':
    with open('../theme.json') as theme_json:
        theme_dict = json.loads(theme_json.read())
        COLOR_LIGHT = theme_dict['light']
        COLOR_DARK = theme_dict['dark']

    def open_window():
        window = ManageEncryptionWindow('320x300+600+300')

    root = tk.Tk()
    root.title('Test UI')
    root.geometry('300x300')
    root.resizable(False, False)
    sv_ttk.use_light_theme()
    root.after(1000, open_window)
    root.mainloop()
else:
    with open('theme.json') as theme_json:
        theme_dict = json.loads(theme_json.read())
        COLOR_LIGHT = theme_dict['light']
        COLOR_DARK = theme_dict['dark']