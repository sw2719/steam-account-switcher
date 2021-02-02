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
from PIL import Image, ImageTk
from modules.config import get_config, config_write_value, config_write_dict
from ruamel.yaml import YAML
from modules.util import check_steam_dir, create_shortcut
from modules.steamid import steam64_to_3, steam64_to_32, steam64_to_2


yaml = YAML()

t = gettext.translation('steamswitcher',
                        localedir='locale',
                        languages=[get_config('locale')],
                        fallback=True)
_ = t.gettext

with open('theme.json') as theme_json:
    theme_dict = json.loads(theme_json.read())
    COLOR_LIGHT = theme_dict['light']
    COLOR_DARK = theme_dict['dark']


def get_color(key):
    theme = get_config('theme')
    if theme == 'light':
        return COLOR_LIGHT[key]
    elif theme == 'dark':
        return COLOR_DARK[key]


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


class MenuBar(tk.Frame):
    def __init__(self, master, bg, fg, selected_bg):
        tk.Frame.__init__(self, master, bd=1, relief='raised')
        self.master = master
        self.configure(background=bg)

        menu_button = tk.Menubutton(self, text='File',
                                    background=bg,
                                    foreground=fg,
                                    activeforeground=bg,
                                    activebackground='white')

        file_menu = tk.Menu(menu_button, tearoff=0)
        file_menu.add_command(label='Example',
                              background=bg,
                              foreground=bg,
                              activeforeground=bg,
                              activebackground='white'
                              )

        menu_button.config(menu=file_menu)
        menu_button.pack(side='left')

        close = SimpleButton(self, text=' X ',
                             command=master.quit,
                             bg=bg,
                             fg=fg)
        close.pack(side='right')

        self.bind("<Button-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.moving)

    def start_move(self, event):
        self.master.x = event.x
        self.master.y = event.y

    def stop_move(self, event):
        self.master.x = None
        self.master.y = None

    def moving(self, event):
        x = (event.x_root - self.master.x)
        y = (event.y_root - self.master.y)
        self.master.geometry("+%s+%s" % (x, y))


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
        self.acc_label.pack(anchor='w', padx=(3, 0))
        self.acc_label.bind('<Button-1>', lambda event: self.__click())
        self.acc_label.bind('<ButtonRelease-1>', lambda event: self.__release(event))
        self.acc_label.bind('<Button-3>', rightcommand)

        self.profile_label = ttk.Label(self.frame, text=profilename)
        self.profile_label.config(background=self.normal, foreground=self.text)
        self.profile_label.pack(anchor='w', padx=(3, 0))
        self.profile_label.bind('<Button-1>', lambda event: self.__click())
        self.profile_label.bind('<ButtonRelease-1>', lambda event: self.__release(event))
        self.profile_label.bind('<Button-3>', rightcommand)

    def update_color(self, init=False):
        self.normal = get_color('account_button')
        self.disabled = get_color('account_button_disabled')
        self.clicked = get_color('account_button_clicked')
        self.hover = get_color('account_button_hover')
        self.onexit = get_color('account_button_cursor_exit')
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

    def color_on_cursor_exit(self):
        color_fade(self.frame, background=self.onexit)
        color_fade(self.acc_label, background=self.onexit)
        color_fade(self.acc_label, foreground=self.text)
        color_fade(self.profile_label, background=self.onexit)
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
        self.frame.bind('<ButtonRelease-1>', lambda event: self.__release())
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
            self.avatar.bind('<ButtonRelease-1>', lambda event: self.__release())
            self.avatar.bind('<Button-3>', rightcommand)

        self.acc_label = ttk.Label(self.frame)
        self.acc_label.config(background=self.normal, foreground=self.text)
        self.acc_label.pack(side='top', pady=(2, 0))
        self.acc_label.bind('<Button-1>', lambda event: self.__click())
        self.acc_label.bind('<ButtonRelease-1>', lambda event: self.__release())
        self.acc_label.bind('<Button-3>', rightcommand)

        if tkfont.Font(font=self.acc_label['font']).measure(username) > 86:
            while tkfont.Font(font=self.acc_label['font']).measure(username) > 86:
                username = username[:-1]
            else:
                username = f'{username}..'

        self.acc_label.configure(text=username)

        self.profile_label = ttk.Label(self.frame)
        self.profile_label.config(background=self.normal, foreground=self.text)
        self.profile_label.pack(side='top')
        self.profile_label.bind('<Button-1>', lambda event: self.__click())
        self.profile_label.bind('<ButtonRelease-1>', lambda event: self.__release())
        self.profile_label.bind('<Button-3>', rightcommand)

        if tkfont.Font(font=self.profile_label['font']).measure(profilename) > 86:
            while tkfont.Font(font=self.profile_label['font']).measure(profilename) > 86:
                profilename = profilename[:-1]
            else:
                profilename = f'{profilename}..'

        self.profile_label.configure(text=profilename)

    def update_color(self, init=False):
        self.normal = get_color('account_button')
        self.disabled = get_color('account_button_disabled')
        self.clicked = get_color('account_button_clicked')
        self.hover = get_color('account_button_hover')
        self.onexit = get_color('account_button_cursor_exit')
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

    def color_on_cursor_exit(self):
        color_fade(self.frame, background=self.onexit)
        color_fade(self.acc_label, background=self.onexit)
        color_fade(self.acc_label, foreground=self.text)
        color_fade(self.profile_label, background=self.onexit)
        color_fade(self.profile_label, foreground=self.text)

    def __click(self):
        self.is_clicked = True
        self.color_clicked()

        # This method of checking cursor is ridiculously CPU intensive (releatively to other parts of the application)
        # It checks cursor location every cursor movement while MB1 is pressed.
        # Enter and leave event don't work properly with mouse button held down so I had to do it this way.
        self.frame.bind('<B1-Motion>', self.check_cursor)
        self.acc_label.bind('<B1-Motion>', self.check_cursor)
        self.profile_label.bind('<B1-Motion>', self.check_cursor)

        if self.avatar:
            self.avatar.bind('<B1-Motion>', self.check_cursor)

    def __release(self):
        self.is_clicked = False
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

        if self.is_clicked:
            self.color_clicked()
        elif self.enabled:
            self.color_hover()

    def __leave(self):
        self.onbutton = False

        if self.is_clicked:
            self.color_on_cursor_exit()
        elif self.enabled:
            self.color_normal()

    def enable(self):
        self.enabled = True
        self.frame.bind('<Button-1>', lambda event: self.__click())
        self.frame.bind('<ButtonRelease-1>', lambda event: self.__release())
        self.frame.config(background=self.normal, cursor='hand2')

        self.avatar.bind('<Button-1>', lambda event: self.__click())
        self.avatar.bind('<ButtonRelease-1>', lambda event: self.__release())

        self.acc_label.bind('<Button-1>', lambda event: self.__click())
        self.acc_label.bind('<ButtonRelease-1>', lambda event: self.__release())
        self.acc_label.config(background=self.normal, foreground=self.text)

        self.profile_label.bind('<Button-1>', lambda event: self.__click())
        self.profile_label.bind('<ButtonRelease-1>', lambda event: self.__release())
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

    def pack(self, **kw):
        self.frame.pack(**kw)

    def grid(self, **kw):
        self.frame.grid(**kw)


class ReadonlyEntryWithLabel:
    def __init__(self, master, label, text, bg='white'):
        self.frame = tk.Frame(master, bg=bg)
        label = tk.Label(self.frame, text=label, bg=bg)
        entry = tk.Entry(self.frame, width=21, readonlybackground='white', relief='solid')
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
        tk.Toplevel.__init__(self, self.master, bg='white')
        self.title(_('Setup'))

        self.geometry(geometry)
        self.resizable(False, False)

        if not debug:
            self.protocol("WM_DELETE_WINDOW", self.on_window_close)

        self.focus()

        try:
            self.iconbitmap('asset/icon.ico')
        except tk.TclError:
            pass

        self.style = ttk.Style()
        self.style.configure('welcome.TCheckbutton', background='white')
        self.style.configure('welcome.TRadiobutton', background='white')

        self.theme_radio_var = tk.IntVar()
        self.ui_radio_var = tk.IntVar()
        self.mode_radio_var = tk.IntVar()
        self.active_page = 0

        self.upper_frame = tk.Frame(self, bg='white')
        self.upper_frame.pack(side='top', fill='x')

        self.top_font = tkfont.Font(weight=tkfont.BOLD, size=17, family='Arial')
        self.title_font = tkfont.Font(weight=tkfont.BOLD, size=23, family='Arial')

        self.ok_button = ttk.Button(self, text=_('OK'), command=self.ok)
        self.ok_button.pack(side='bottom', padx=3, pady=3, fill='x')

        self.title_label = tk.Label(self, bg='white', text=_('Update complete'), font=self.title_font)

        if after_update:
            self.title_label['text'] = _('Update complete')
        else:
            self.title_label['text'] = _('Welcome')

        self.welcome_label = tk.Label(self, text=_('Click OK to continue.'), bg='white')
        self.title_label.pack(expand=True, pady=1)
        self.welcome_label.pack(expand=True, pady=1)

        self.grab_set()

    def on_window_close(self):
        os.remove('config.yml')
        sys.exit(0)

    def ok(self):
        if self.active_page == 0:
            self.title_label.destroy()
            self.welcome_label.destroy()
            self.top_label = tk.Label(self.upper_frame, bg='white', font=self.top_font)
            self.top_label.pack(side='left', padx=(10, 0), pady=10)
            self.page_1()
            self.focus()

        elif self.active_page == 1:
            if self.theme_radio_var.get() == 0:
                self.theme = 'light'
            elif self.theme_radio_var.get() == 1:
                self.theme = 'dark'

            self.radio_frame1.destroy()
            self.radio_frame2.destroy()
            self.dark_alert.destroy()
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

            self.top_label.pack_forget()
            self.top_label.pack(pady=10)
            self.save()
            self.page_5()
            self.focus()

        elif self.active_page == 5:
            if 'selected' in self.shortcut_chkb.state():
                create_shortcut()

            self.ok_button['text'] = _('Please wait...')
            self.ok_button['state'] = 'disabled'
            self.focus()
            self.master.update()
            self.destroy()

    def page_1(self):
        self.active_page = 1
        self.top_label['text'] = _('UI Appearance')
        self.bottomframe = tk.Frame(self, bg='white')
        self.bottomframe.pack(side='bottom', fill='x')

        self.dark_alert = tk.Label(self.bottomframe, bg='white',
                                   text=_(' '))
        self.dark_alert.pack(side='bottom', pady=(0, 4), fill='x')

        icon_w = 60
        icon_h = 96

        self.radio_frame1 = tk.Frame(self, bg='white')
        self.radio_frame1.pack(side='left', padx=(60, 0), pady=5)

        self.light_canvas = tk.Canvas(self.radio_frame1, width=icon_w, height=icon_h, bg='white', bd=0, highlightthickness=0)
        img = Image.open("asset/light.png").resize((icon_w, icon_h))

        self.light_imgtk = ImageTk.PhotoImage(img)
        self.light_canvas.create_image(icon_w / 2, icon_h / 2, image=self.light_imgtk)
        self.light_canvas.pack(side='top', padx=0, pady=5)

        def on_button():
            if self.theme_radio_var.get():
                self.dark_alert['text'] = _('Dark theme is applied only to main window.')
            else:
                self.dark_alert['text'] = ' '

        radio_light = ttk.Radiobutton(self.radio_frame1,
                                      text=_('Light'),
                                      variable=self.theme_radio_var,
                                      value=0,
                                      style='welcome.TRadiobutton',
                                      command=on_button)
        radio_light.pack(side='top', pady=2)

        self.radio_frame2 = tk.Frame(self, bg='white')
        self.radio_frame2.pack(side='right', padx=(0, 60), pady=5)

        self.dark_canvas = tk.Canvas(self.radio_frame2, width=icon_w, height=icon_h, bg='white', bd=0, highlightthickness=0)
        img = Image.open("asset/dark.png").resize((icon_w, icon_h))
        self.dark_imgtk = ImageTk.PhotoImage(img)
        self.dark_canvas.create_image(icon_w / 2, icon_h / 2, image=self.dark_imgtk)
        self.dark_canvas.pack(side='top', padx=0, pady=5)

        radio_dark = ttk.Radiobutton(self.radio_frame2,
                                     text=_('Dark'),
                                     variable=self.theme_radio_var,
                                     value=1,
                                     style='welcome.TRadiobutton',
                                     command=on_button)
        radio_dark.pack(side='top', pady=2)

    def page_2(self):
        self.active_page = 2
        self.radio_frame1 = tk.Frame(self, bg='white')
        self.radio_frame1.pack(side='left', padx=(43, 0), pady=5)

        self.list_canvas = tk.Canvas(self.radio_frame1, width=50, height=50, bg='white', bd=0, highlightthickness=0)
        img = Image.open("asset/list.png").resize((50, 50))

        self.list_imgtk = ImageTk.PhotoImage(img)
        self.list_canvas.create_image(25, 25, image=self.list_imgtk)
        self.list_canvas.pack(side='top', padx=0, pady=5)

        radio_list = ttk.Radiobutton(self.radio_frame1,
                                     text=_('List Mode'),
                                     variable=self.ui_radio_var,
                                     value=0,
                                     style='welcome.TRadiobutton')
        radio_list.pack(side='top', pady=2)

        tk.Label(self.radio_frame1, justify='left', bg='white',
                 text=_("Display accounts\nin vertical list")).pack(side='bottom', pady=5)

        self.radio_frame2 = tk.Frame(self, bg='white')
        self.radio_frame2.pack(side='right', padx=(0, 43), pady=5)

        self.grid_canvas = tk.Canvas(self.radio_frame2, width=50, height=50, bg='white', bd=0, highlightthickness=0)
        img = Image.open("asset/grid.png").resize((50, 50))

        self.grid_imgtk = ImageTk.PhotoImage(img)
        self.grid_canvas.create_image(25, 25, image=self.grid_imgtk)
        self.grid_canvas.pack(side='top', padx=0, pady=5)

        radio_grid = ttk.Radiobutton(self.radio_frame2,
                                     text=_('Grid Mode'),
                                     variable=self.ui_radio_var,
                                     value=1,
                                     style='welcome.TRadiobutton')
        radio_grid.pack(side='top', pady=2)

        tk.Label(self.radio_frame2, justify='left', bg='white',
                 text=_('Display accounts\nin 3 x n grid')).pack(side='bottom', pady=5)

    def page_3(self):
        self.active_page = 3
        self.top_label['text'] = _('Steam restart behaviour')

        self.radio_frame1 = tk.Frame(self, bg='white')
        self.radio_frame1.pack(side='top', padx=20, pady=(4, 10), fill='x')

        radio_normal = ttk.Radiobutton(self.radio_frame1,
                                       text=_('Normal Mode'),
                                       variable=self.mode_radio_var,
                                       value=0,
                                       style='welcome.TRadiobutton')
        radio_normal.pack(side='top', anchor='w', pady=2)

        tk.Label(self.radio_frame1, justify='left', bg='white',
                 text=_("In normal mode, you restart Steam\nby clicking 'Restart Steam' button.")).pack(side='left', pady=5)

        self.radio_frame2 = tk.Frame(self, bg='white')
        self.radio_frame2.pack(side='top', padx=20, pady=(0, 3), fill='x')

        radio_express = ttk.Radiobutton(self.radio_frame2,
                                        text=_('Express Mode'),
                                        variable=self.mode_radio_var,
                                        value=1,
                                        style='welcome.TRadiobutton')
        radio_express.pack(side='top', anchor='w', pady=2)

        tk.Label(self.radio_frame2, justify='left', bg='white',
                 text=_('In express mode, Steam will be automatically\nrestarted when you change account.')).pack(side='left', pady=5)

    def page_4(self):
        self.active_page = 4
        self.top_label['text'] = _('Other settings')

        self.softshutdown_frame = tk.Frame(self, bg='white')
        self.softshutdown_frame.pack(fill='x', side='top', padx=(14, 0), pady=(4, 0))

        self.soft_chkb = ttk.Checkbutton(self.softshutdown_frame,
                                         text=_('Try to soft shutdown Steam client'),
                                         style='welcome.TCheckbutton')

        self.soft_chkb.state(['!alternate'])
        self.soft_chkb.state(['selected'])

        self.soft_chkb.pack(side='top', anchor='w')
        tk.Label(self.softshutdown_frame, text=_('Shutdown Steam instead of killing Steam process'), bg='white').pack(side='top', anchor='w')

        self.autoexit_frame = tk.Frame(self, bg='white')
        self.autoexit_frame.pack(fill='x', side='top', padx=(14, 0), pady=15)

        self.autoexit_chkb = ttk.Checkbutton(self.autoexit_frame,
                                             text=_('Exit app after Steam is restarted'),
                                             style='welcome.TCheckbutton')

        self.autoexit_chkb.state(['!alternate'])
        self.autoexit_chkb.state(['selected'])

        self.autoexit_chkb.pack(side='top', anchor='w')
        tk.Label(self.autoexit_frame, text=_('Exit app automatically after restarting Steam'), bg='white').pack(side='top', anchor='w')

        self.avatar_frame = tk.Frame(self, bg='white')
        self.avatar_frame.pack(fill='x', side='top', padx=(14, 0))

        self.avatar_chkb = ttk.Checkbutton(self.avatar_frame,
                                           text=_('Show avatar images'),
                                           style='welcome.TCheckbutton')

        self.avatar_chkb.state(['!alternate'])
        self.avatar_chkb.state(['selected'])

        if self.ui_mode == 'grid':
            self.avatar_chkb.state(['disabled'])

        self.avatar_chkb.pack(side='top', anchor='w')
        tk.Label(self.avatar_frame, text=_('Show avatars in account list'), bg='white').pack(side='top', anchor='w')

    def page_5(self):
        self.active_page = 5
        self.top_label['text'] = _('Good to go!')

        # tkinter doesn't like three quotes string, so... yeah.
        self.finish_label = tk.Label(self, bg='white',
                                     text=_("Add or import accounts via Menu.\nRight click on accounts to see more options.\n\nYou can change settings in Menu > Settings\nif you don't like the settings you just set.\n\nPlease read GitHub README's How to use-4\nif you are using this app for first time.\n\nYou can open GitHub repo via Menu > About."))
        self.finish_label.pack(expand=True, fill='both')

        self.shortcut_chkb = ttk.Checkbutton(self,
                                             text=_('Create a desktop shortcut'),
                                             style='welcome.TCheckbutton')
        self.shortcut_chkb.state(['!alternate'])
        self.shortcut_chkb.state(['!selected'])

        self.shortcut_chkb.pack(anchor='center', pady=(3, 1))

    def save(self):
        dump_dict = {'locale': get_config('locale'),
                     'try_soft_shutdown': self.soft_shutdown,
                     'autoexit': self.autoexit,
                     'mode': self.mode,
                     'show_avatar': self.avatar,
                     'last_pos': get_config('last_pos'),
                     'steam_path': get_config('steam_path'),
                     'ui_mode': self.ui_mode,
                     'theme': self.theme}

        config_write_dict(dump_dict)


class ToolTipWindow(object):
    '''
    create a tooltip for a given widget
    '''
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.close)

    def enter(self, event=None):
        x = y = 0
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx()
        y += self.widget.winfo_rooty() + 40

        self.win = tk.Toplevel(self.widget)
        self.win.wm_overrideredirect(True)

        label = tk.Label(self.win, text=self.text, justify='left',
                         background='white', relief='solid', borderwidth=1)
        label.pack(ipadx=1)

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
    steamid_window = tk.Toplevel(master, bg='white')
    steamid_window.geometry()
    steamid_window.title('SteamID')
    steamid_window.geometry(geometry)
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
