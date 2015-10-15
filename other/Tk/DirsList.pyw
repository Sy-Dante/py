#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from time import sleep
from Tkinter import *
import tkMessageBox

reload(sys)
sys.setdefaultencoding("utf-8")

class DirList(object):

    def __init__(self, initdir=None):
        self.top = Tk()
        self.top.title('Directoty Lister v1.0')
        # self.label = Label(self.top, 
        #                 text='Directoty Lister v1.0')
        # self.label.pack()

        self.cwd = StringVar(self.top)

        self.dirl = Label(self.top, fg='blue', 
                        font=('Consolas', 12), wraplength=350)
        self.dirl.pack()

        self.dirfm = Frame(self.top)
        self.dirsb = Scrollbar(self.dirfm)
        self.dirsb.pack(side=RIGHT, fill=Y)

        self.dirs = Listbox(self.dirfm, height=15, 
                        width=50, 
                        yscrollcommand=self.dirsb.set)
        self.dirs.bind('<Double-1>', self.setDirAndGo)
        self.dirs.bind('<Return>', self.setDirAndGo)
        self.dirsb.config(command=self.dirs.yview)
        self.dirs.pack(side=LEFT, fill=BOTH)
        self.dirfm.pack()

        self.dirn = Entry(self.top, width=50, 
                        textvariable=self.cwd)
        self.dirn.bind('<Return>', self.doLS)
        self.dirn.pack()

        self.bfm = Frame(self.top)
        self.clr = Button(self.bfm, text='Clear', 
                        command=self.clrDir,
                        activeforeground='white',
                        activebackground='blue')
        self.ls = Button(self.bfm,
                        text='List Directory',
                        command=self.doLS,
                        activeforeground='white',
                        activebackground='green')
        self.quit = Button(self.bfm, text='Quit', 
                        command=self.myQuit,
                        activeforeground='white',
                        activebackground='red')
        self.clr.pack(side=LEFT)
        self.ls.pack(side=LEFT)
        self.quit.pack(side=LEFT)
        self.bfm.pack()

        self.top.protocol("WM_DELETE_WINDOW", self.myQuit)
        if initdir:
            self.doLS()

    def clrDir(self, ev=None):
        self.cwd.set('')

    def setDirAndGo(self, ev=None):
        self.last = self.cwd.get()
        self.dirs.config(selectbackground='red')
        check = self.dirs.get(self.dirs.curselection())
        if not check:
            check = os.curdir
        self.cwd.set(check)
        self.doLS()

    def doLS(self, ev=None):
        error = ''
        tdir = self.cwd.get()
        if not tdir: tdir = os.curdir

        if not os.path.exists(tdir):
            error = tdir + ': no such file'
        elif not os.path.isdir(tdir):
            error = tdir + ': not a directory'

        if error:
            # self.cwd.set(error)
            self.dirl.config(text=error, fg='red')
            # self.top.update()
            # sleep(2)
            if not (hasattr(self, 'last') and self.last):
                self.last = os.curdir
            self.cwd.set(self.last)
            self.dirs.config(selectbackground='LightSkyBlue')
            # self.top.update()
            return
        # self.cwd.set('FETCHING DIRECTORY CONTENTS...')
        # self.top.update()
        dirlist = os.listdir(unicode(tdir))
        dirlist.sort()
        os.chdir(tdir)
        file_path = os.getcwd().decode('GBK')
        import chardet
        try:
            print chardet.detect(self.cwd.get())
        except:
            print '....'
        print chardet.detect(os.getcwd())
        print file_path
        print '----------------------'
        self.dirl.config(text=file_path, fg='blue')
        self.dirs.delete(0, END)
        self.dirs.insert(END, os.pardir)
        for eachFile in dirlist:
            self.dirs.insert(END, eachFile)
            self.dirs.config(selectbackground='LightSkyBlue')
        self.cwd.set(file_path)
        self.dirs.selection_set(0)
        self.dirs.focus()

    def myQuit(self):
        if tkMessageBox.askokcancel("Quit", "Do you really wish to quit?"):
            self.top.destroy()

def run():
    d = DirList(os.curdir)
    mainloop()

if __name__ == '__main__':
    run()
