import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkfont
from PIL import Image, ImageTk
from modules.config import get_config

COLOR_DISABLED = '#cfcfcf'
COLOR_CLICKED = '#363636'
COLOR_HOVER = '#f2f2f2'


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

        username_font = tkfont.Font(weight=tkfont.BOLD, size=13)

        if get_config('show_avatar') == 'true':
            self.avatar = tk.Canvas(self.frame, width=40, height=40, bd=0, highlightthickness=0)
            img = Image.open(f"avatar/{image}.jpg").resize((40, 40))
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
        self.avatar.bind('<B1-Motion>', self.check_cursor)

    def __release(self):
        self.clicked = False
        self.color_normal()
        self.frame.unbind('<B1-Motion>')
        self.acc_label.unbind('<B1-Motion>')
        self.profile_label.unbind('<B1-Motion>')

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
