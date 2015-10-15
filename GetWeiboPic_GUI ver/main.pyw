#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import os
import re
import sys
import requests
import tkMessageBox
import Tkinter as Tk
import ttk

from GetWeiboPic import DownloadPic
from WeiboDB import WeiboDB

reload(sys)
sys.setdefaultencoding("utf-8")

def center_window(root, width, height):  
    screenwidth = root.winfo_screenwidth()  
    screenheight = root.winfo_screenheight()  
    size = '%dx%d+%d+%d' % (width, height, (screenwidth - width)/2, (screenheight - height)/2)  
    print(size)
    root.geometry(size)

class CookiesBox(Tk.Frame):
    """建立Cookies输入框"""

    def __init__(self, parent=None, side=Tk.LEFT, anchor=Tk.W, **kw):
        """建立Cookies输入框"""
        Tk.Frame.__init__(self, parent, kw)
        self._session = requests.Session()

        pack_conf = {
            'side': side,
            # 'anchor': anchor,
            'expand': Tk.YES,
        }
        Tk.Label(self, text='Cookies：').pack(pack_conf)
        # 载入cookies
        cookies = self._load()
        # cookies文本框 & 验证按钮 & 提示
        self._cookies = Tk.StringVar()
        self._prompt = Tk.StringVar()
        self._cookies.set(cookies)
        self._prompt.set('')
        ttk.Entry(self, text=self._cookies, width=50).pack(pack_conf, padx=5)
        ttk.Button(self, text='验证', command=self.check, width=10).pack(pack_conf)
        Tk.Label(self, textvariable=self._prompt, width=40, fg='#5C5').pack(pack_conf)

    def set(self, cookies):
        """设置Cookies"""
        self._cookies.set(str(cookies))

    def get(self):
        """获取Cookies"""
        return self._cookies.get()

    def _load(self):
        """从文件载入Cookies"""
        try:
            with open('data/cookies.txt', 'r') as f:
                cookies = f.read()
        except IOError:
            cookies = ''
        return cookies

    def save(self):
        """将cookies信息存入文件"""
        with open('data/cookies.txt', 'w') as f:
            f.write(self.get())

    def session(self):
        """获取会话"""
        cookies = self.get()
        self._session.cookies.update({'Cookie': cookies,})
        self._session.headers.update({
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.8 Safari/537.36',
        })
        return self._session

    def check(self):
        """验证Cookies是否有效"""
        self._prompt.set('checking...')
        self.update()
        try:
            # 获取内容
            url = 'http://weibo.com/'
            session = self.session()
            content = session.get(url, timeout=2).content
            # 获取微博名
            name = re.search(r'CONFIG\[\'nick\'\]\=\'(.*?)\';', content).group(1)
        except IOError, e:
            msg = '网络超时，请重试！'
            self._prompt.set(msg)
            raise IOError(e)
        except AttributeError, e:
            msg = '登录失败！'
            self._prompt.set(msg)
            return {'login': False, 'msg': e}
        msg = '微博名：%s' % name
        self._prompt.set(msg)
        return {'login': True, 'msg': name}

class CheckBox(Tk.Frame):
    """建立一组多选按钮组"""

    def __init__(self, parent=None, picks=[], row=5, side=Tk.LEFT, anchor=Tk.W, **kw):
        """建立一组多选按钮组

        Args:
            parent: Frame 父框架
            picks: array 按钮数据[(nick, wbid, down),]
            row: int 每行选框的数量 default 5
        """
        Tk.Frame.__init__(self, parent, kw)
        Tk.Label(self, text='成员：').pack(side=side, anchor=anchor, expand=Tk.YES)
        # 多选框框架
        chk_main = Tk.Frame(self)
        chk_main.pack(side=side, anchor=anchor, expand=Tk.YES)
        # 建立多选框
        self._vals = [] # 存储值
        self._chks = [] # 存储选框对象
        num = 0
        for nick, wbid, down in picks:
            # 分行框架
            if num % row == 0:
                chk_list = Tk.Frame(chk_main)
                chk_list.pack(side=Tk.TOP, anchor=Tk.W)
            # 创建选框
            val = Tk.StringVar()
            value = u'%s:%s' % (nick, wbid)
            on_val = value + ':1'
            off_val = value + ':0'
            val.set(u'%s:%s:%s' % (nick, wbid, down))
            chk = Tk.Checkbutton(chk_list, text=nick, variable=val, 
                            onvalue=on_val, offvalue=off_val, width=15, anchor=anchor)
            chk.pack(side=side, anchor=anchor, expand=Tk.YES)
            self._vals.append(val)
            self._chks.append(chk)
            num += 1

    def state(self):
        """获取选框状态"""
        return [val.get().split(':') for val in self._vals]

    def toggle(self):
        """全反选"""
        for chk in self._chks:
            chk.toggle()

    def select(self):
        """全选"""
        for chk in self._chks:
            chk.select()

    def deselect(self):
        """全不选"""
        for chk in self._chks:
            chk.deselect()

class AddWindow(Tk.Toplevel):
    """创建一个子窗口，用于添加数据"""

    def __init__(self, app, **kw):
        """窗口初始化"""
        Tk.Toplevel.__init__(self, app.top, kw)
        self.app = app
        self.title('添加成员')
        center_window(self, 300, 200)
        self.protocol("WM_DELETE_WINDOW", self.quit)
        self.config(pady=30)
        self.focus()
        # 载入输入框
        self._loadText(self)
        # 载入提示框
        self._prompt = Tk.StringVar()
        prompt_fm = Tk.Frame(self)
        prompt_fm.pack()
        Tk.Label(prompt_fm, textvariable=self._prompt, fg='#292', pady=5).pack()
        # 载入功能按钮
        bt_fm = Tk.Frame(self)
        bt_fm.pack(ipady=5)
        self._loadButton(bt_fm)

    def _loadText(self, parent, side=Tk.TOP, anchor=Tk.W):
        self._val = Tk.StringVar()
        frame = Tk.Frame(parent)
        frame.pack(side=side)
        Tk.Label(frame, text='微博链接').pack()
        ttk.Entry(frame, textvariable=self._val).pack(anchor=Tk.W)

    def _loadButton(self, parent):
        """加载底部系统按钮"""
        footer_bt_conf = {
            'side': Tk.LEFT,
            'padx': 30,
        }
        ttk.Button(parent, text='确定', command=self.add).pack(**footer_bt_conf)
        ttk.Button(parent, text='取消', command=self.quit).pack(**footer_bt_conf)

    def add(self):
        """将数据存入数据库并提交 & 返回主窗口"""
        app = self.app
        url = self._val.get()
        if url == '' or url[:7].lower() != 'http://':
            self._prompt.set('请填写正确值')
            return
        data = self.get(url)
        print(data)
        if data:
            self._prompt.set('添加成功：%s' % data.keys()[0])
            app.db.insert(data)
            app.db.commit()
            app.fresh()
            self.quit()

    def get(self, url):
        app = self.app
        session = app.cookies_fm.session()
        try:
            res = session.get(url, timeout=2).content  # $CONFIG['oid']='2689280541'; $CONFIG['onick']='SNH48'; 
            oid = re.search(r'CONFIG\[\'oid\'\]=\'(.*?)\'', res).group(1)
            onick = re.search(r'CONFIG\[\'onick\'\]=\'(.*?)\'', res).group(1)
            onick = unicode(onick)
        except (IOError, AttributeError), e:
            self._prompt.set('链接或网络错误！')
            print(e)
            return False
        if oid and onick:
            return {onick: oid}
        else:
            self._prompt.set('链接错误！')
            return False

    def quit(self):
        """退出"""
        del self.app.add_window
        self.app.top.focus()
        self.destroy()

class App(object):
    
    def __init__(self):
        # 载入数据库
        self.db = WeiboDB()
        # 初始化窗口
        self.top = Tk.Tk()
        self.top.title('Get Weibo Picture Tools v1.0')
        # self.top.geometry('800x500')
        center_window(self.top, 800, 500)
        self.top.resizable(False, False)
        self.top.protocol("WM_DELETE_WINDOW", self.quit)
        self.top.config(pady=5)
        # Cookies框
        self.cookies_fm = CookiesBox(self.top)
        self.cookies_fm.pack(padx=22)
        # 多选框架
        self.chk_fm = Tk.Frame(self.top)
        self.chk_fm.pack()
        self.fresh()
        # 添、删按钮
        self._loadADButton(self.top)
        # 下载区
        self.down_fm = DownloadPic(self.top)
        self.down_fm.pack()
        # 底部按钮
        footer_fm = Tk.Frame(self.top)
        footer_fm.pack(ipady=20)
        self._loadButton(footer_fm)

        self.top.mainloop()

    def _loadChk(self, parent=None):
        """载入多选框"""
        picks = self.db.getAll()
        self.chk = CheckBox(parent, picks)
        self.chk.pack(ipady=20)
        self._loadChkButton(self.chk)

    def _loadChkButton(self, parent=None, side=Tk.LEFT, width=10):
        """载入选框功能按钮（全选、不选、反选、添加）"""
        button_fm = Tk.Frame(parent)
        button_fm.pack(side=side)
        ttk.Button(button_fm, text='全选', command=parent.select, width=width).pack()
        ttk.Button(button_fm, text='全不选', command=parent.deselect, width=width).pack()
        # ttk.Button(button_fm, text='toggle', command=parent.toggle, width=width).pack()

    def _loadADButton(self, parent=None, side=Tk.LEFT, width=10):
        """载入添加、删除按钮"""
        button_fm = Tk.Frame(parent)
        button_fm.pack()
        ttk.Button(button_fm, text='添加', command=self._addWindow, width=width).pack(side=side)
        ttk.Button(button_fm, text='删除', command=self.delete, width=width).pack(side=side)

    def _loadButton(self, parent=None, side=Tk.LEFT, width=10):
        """加载底部系统按钮"""
        footer_bt_conf = {
            'side': side,
            'padx': 30,
        }
        ttk.Button(parent, text='运行', width=width, command=self.run).pack(**footer_bt_conf)
        # ttk.Button(parent, text='刷新', width=width, command=self.fresh).pack(**footer_bt_conf)
        ttk.Button(parent, text='关闭', width=width, command=self.quit).pack(**footer_bt_conf)

    def _addWindow(self):
        """载入添加窗口"""
        try:
            self.add_window.focus()
        except AttributeError:
            self.add_window = AddWindow(self)

    def save(self, chk_states):
        """保存cookie信息和选框信息"""
        self.cookies_fm.save()
        self.db.insert(chk_states)

    def fresh(self):
        """刷新多选框内容"""
        try:
            self.chk.destroy()
        except AttributeError:
            pass
        self._loadChk(self.chk_fm)

    def delete(self):
        """删除选定项"""
        if tkMessageBox.askokcancel("删除", "确认删除选中的数据？"):
            chks = self.chk.state()
            data = [row[1] for row in chks if row[2] == '1']
            print(self.db.delete(data))
            self.fresh()

    def run(self):
        """运行下载"""
        chk_states = self.chk.state()
        self.save(chk_states)
        data = [(row[0], row[1]) for row in chk_states if row[2] == '1']
        session = self.cookies_fm.session()
        self.down_fm.update(data, session)
        self.down_fm.download()


    def quit(self):
        """自定义退出"""
        self.db.exit()
        self.top.quit()

if __name__ == '__main__':

    # def dump(msg):
    #     import json
    #     try:
    #         print(json.dumps(msg, indent=4))
    #     except:
    #         print(msg)

    app = App()
    
