#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""获取微博图片"""
from __future__ import absolute_import, division, print_function, unicode_literals
import os
import sys
import time
import re
import json
import math
import logging
import requests
import threading
import Tkinter as Tk
import ttk
from bs4 import BeautifulSoup
# import chardet
# logging.basicConfig(level=logging.DEBUG)

reload(sys)
sys.setdefaultencoding("utf-8")

class PBar(Tk.Frame):

    def __init__(self, parant, uid, session, count=30, side=Tk.LEFT, anchor=Tk.W, **kw):
        """"""
        Tk.Frame.__init__(self, parant, kw)
        ttk.Label(self, text=uid).pack(side=side, anchor=anchor, expand=Tk.YES)

        self.val = Tk.IntVar()
        self.pbar = ttk.Progressbar(self, length=500, variable=self.val, maximum=count)
        self.pbar.pack(side=side, anchor=anchor, expand=Tk.YES)

    def _getName(self):
        pass

    def run(self):
        for i in range(31):
            self.val.set(i)
            self.pbar.update()
            time.sleep(0.05)
        print('success')

if __name__ == '__main__':

    def one():
        wp = PBar(top, 12345678, 'session')
        wp.pack()

    def run():
        thread = [threading.Thread(target=one) for i in range(2)]
        for t in thread:
            t.start()


    top = Tk.Tk()
    ttk.Button(top, text='run', command=run).pack()
    # wp = PBar(top, 12345678, 'session')
    # wp.pack()
    top.mainloop()
