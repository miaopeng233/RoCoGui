from tkinter import *


class Main():
    def __init__(self):
        root = Tk()
        self.entry = Entry(root)
        self.button = Button(root, text='执行', command=self.do_something)
        self.grid()
        root.mainloop()

    def grid(self):
        self.entry.grid(row=0, column=0)
        self.button.grid(row=0, column=1)

    def do_something(self):
        self.entry.insert('0', '结束了')


if __name__ == '__main__':
    Main()
