import tkinter as tk
import tkinter.font as tkfont


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


class ButtonwithLabels:
    def __init__(self, master, text='<>', command=None, rightcommand=None):
        self.f, self.command = tk.Frame(master, borderwidth=3), command
        self.f.config(bg='white')
        self.f.bind('<Button-1>', lambda event: self.__click())
        self.f.bind('<ButtonRelease-1>', lambda event: self.__release())
        self.f.bind('<Button-3>', rightcommand)

        sections = [i.split('>') for i in text.split('<')[1:]]

        self.label_dict = {}
        self.alt_label_dict = {}

        for index, section in enumerate(sections):

            font_decomp, kw = section[0].split('_'), {}
            for keyword in font_decomp:
                if keyword == 'BOLD':
                    kw['weight'] = tkfont.BOLD
                else:
                    try:
                        kw['size'] = int(keyword)
                    except ValueError:
                        pass

            temp_font = tkfont.Font(**kw)
            self.label_dict[index] = tk.Label(self.f, text=section[1].replace('\n', ''), font=temp_font)
            self.label_dict[index].config(bg='white')
            self.label_dict[index].pack(anchor='w', padx=(3, 0))
            self.label_dict[index].bind('<Button-1>', lambda event: self.__click())
            self.label_dict[index].bind('<ButtonRelease-1>', lambda event: self.__release())
            self.label_dict[index].bind('<Button-3>', rightcommand)

            if section[1].count('\n') >= 1:
                for i in range(section[1].count('\n') - 1):
                    self.alt_label_dict[i] = tk.Label(self.f, text='', font=temp_font)
                    self.alt_label_dict[i].pack()
                    self.alt_label_dict[i].bind('<Button-1>', lambda event: self.__click())
                    self.alt_label_dict[i].bind('<ButtonRelease-1>', lambda event: self.__release())
                    self.alt_label_dict[i].bind('<Button-3>', rightcommand)

    def __click(self):
        self.f.config(bg='grey')

        for label in self.label_dict.values():
            label.config(bg='grey')

    def __release(self):
        self.f.config(bg='white')

        for label in self.label_dict.values():
            label.config(bg='white')

        if self.command:
            self.command()

    def enable(self):
        self.f.bind('<Button-1>', lambda event: self.__click())
        self.f.bind('<ButtonRelease-1>', lambda event: self.__release())
        self.f.config(bg='white')

        for label in self.label_dict.values():
            label.bind('<Button-1>', lambda event: self.__click())
            label.bind('<ButtonRelease-1>', lambda event: self.__release())
            label.config(bg='white')

        for label in self.alt_label_dict.values():
            label.bind('<Button-1>', lambda event: self.__click())
            label.bind('<ButtonRelease-1>', lambda event: self.__release())
            label.config(bg='white')

    def disable(self):
        self.f.unbind('<Button-1>')
        self.f.unbind('<ButtonRelease-1>')
        self.f.config(bg='#bdbdbd')

        for label in self.label_dict.values():
            label.unbind('<Button-1>')
            label.unbind('<ButtonRelease-1>')
            label.config(bg='#bdbdbd')

        for label in self.alt_label_dict.values():
            label.unbind('<Button-1>')
            label.unbind('<ButtonRelease-1>')
            label.config(bg='#bdbdbd')

    def pack(self, **kw):
        self.f.pack(**kw)
