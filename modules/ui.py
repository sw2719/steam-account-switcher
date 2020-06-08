import tkinter as tk
import tkinter.font as tkfont

COLOR_DISABLED = '#cfcfcf'
COLOR_CLICKED = '#363636'
COLOR_HOVER = '#ededed'


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


class ButtonwithLabels:
    def __init__(self, master, username, profilename, command=None, rightcommand=None):
        self.master = master
        self.frame = tk.Frame(master, borderwidth=3)
        self.command = command
        self.frame.config(bg='white')

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
        persona_font = tkfont.Font(size=10)

        self.acc_label = tk.Label(self.frame, text=username, font=username_font)
        self.acc_label.config(bg='white')
        self.acc_label.pack(anchor='w', padx=(3, 0))
        self.acc_label.bind('<Button-1>', lambda event: self.__click())
        self.acc_label.bind('<ButtonRelease-1>', lambda event: self.__release())
        self.acc_label.bind('<Button-3>', rightcommand)

        self.profile_label = tk.Label(self.frame, text=profilename, font=persona_font)
        self.profile_label.config(bg='white')
        self.profile_label.pack(anchor='w', padx=(3, 0))
        self.profile_label.bind('<Button-1>', lambda event: self.__click())
        self.profile_label.bind('<ButtonRelease-1>', lambda event: self.__release())
        self.profile_label.bind('<Button-3>', rightcommand)

    def check_cursor(self, event):
        widget = event.widget.winfo_containing(event.x_root, event.y_root)

        if widget in (self.frame, self.acc_label, self.profile_label):
            self.__enter()
        else:
            self.__leave()

    def color_clicked(self):
        self.frame.config(bg=COLOR_CLICKED)

        self.acc_label.config(bg=COLOR_CLICKED, fg='white')
        self.profile_label.config(bg=COLOR_CLICKED, fg='white')

    def color_hover(self):
        self.frame.config(bg=COLOR_HOVER)

        self.acc_label.config(bg=COLOR_HOVER)
        self.profile_label.config(bg=COLOR_HOVER)

    def color_normal(self):
        self.frame.config(bg='white')

        self.acc_label.config(bg='white', fg='black')
        self.profile_label.config(bg='white', fg='black')

    def __click(self):
        self.clicked = True
        self.color_clicked()
        self.frame.bind('<B1-Motion>', self.check_cursor)
        self.acc_label.bind('<B1-Motion>', self.check_cursor)
        self.profile_label.bind('<B1-Motion>', self.check_cursor)

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
        self.frame.config(bg='white')

        self.acc_label.bind('<Button-1>', lambda event: self.__click())
        self.acc_label.bind('<ButtonRelease-1>', lambda event: self.__release())
        self.acc_label.config(bg='white')

        self.profile_label.bind('<Button-1>', lambda event: self.__click())
        self.profile_label.bind('<ButtonRelease-1>', lambda event: self.__release())
        self.profile_label.config(bg='white')

    def disable(self):
        self.enabled = False
        self.frame.unbind('<Button-1>')
        self.frame.unbind('<ButtonRelease-1>')
        self.frame.config(bg=COLOR_DISABLED)

        self.acc_label.unbind('<Button-1>')
        self.acc_label.unbind('<ButtonRelease-1>')
        self.acc_label.config(bg=COLOR_DISABLED)

        self.profile_label.unbind('<Button-1>')
        self.profile_label.unbind('<ButtonRelease-1>')
        self.profile_label.config(bg=COLOR_DISABLED)

    def pack(self, **kw):
        self.frame.pack(**kw)
