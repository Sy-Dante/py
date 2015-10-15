#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from Tkinter import Tk, Label, Button, Scale, X, Y, HORIZONTAL

def resize(ev):
    test.config(font=('Consolas', ev))


top = Tk()
top.geometry('500x500')
Label(top, text='Directory list view').pack()

test = Label(top, text='test', fg='grey', font=('Consolas', 12))
test.pack()

scale = Scale(from_=10, to=40, orient=HORIZONTAL, command=resize)
scale.set(12)
scale.pack(fill=X)

Button(top, text='QUIT', bg='red', fg='blue', command=top.quit).pack(fill=X)

top.mainloop()
