#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2015-09-01 16:07:53
# @Author  : Your Name (you@example.org)
# @Link    : http://example.org
# @Version : $Id$

import Tkinter

def resize(ev=None):
    label.config(font='Helvetica -%d bold' % scale.get())

top = Tkinter.Tk()

top.geometry('250x150')



label = Tkinter.Label(top, text='Hello world!', font='Helvetica -12 bold')
label.pack(fill=Tkinter.Y, expand=1)

scale = Tkinter.Scale(top, from_=10, to=40, orient=Tkinter.HORIZONTAL, command=resize)
scale.set(12)
scale.pack(fill=Tkinter.X, expand=1)

quit = Tkinter.Button(top, text='quit', command=top.quit, activeforeground='white', activebackground='red')
quit.pack(fill=Tkinter.X, expand=1)

Tkinter.mainloop()