#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""通过Cookies实现Weibo登录"""
from __future__ import absolute_import, division, print_function, unicode_literals
import os
import re
import sys
import Tkinter
import requests
import tkMessageBox
from time import sleep
from bs4 import BeautifulSoup

from WeiboDB import WeiboDB

class WeiboLG(object):
    """通过Cookies实现Weibo登录"""

    def __init__(self, cookies=''):
        """创建requests会话

        Args:
            cookies: string 用户的cookies信息
        """
        self._session = requests.Session()
        self._session.cookies.update({'Cookie': cookies,})

    def session(self):
        """返回会话"""
        return self._session

    def check_login(self):
        """验证Cookie可用性"""
        try:
            # 获取内容
            url = 'http://weibo.com/'
            content = self._session.get(url).content
            # soup = BeautifulSoup(content)
            # 获取微博名
            # name = soup.find('meta', attrs={'name': 'keywords'})['content'].split('，')[0]
            name = re.search(r'CONFIG\[\'nick\'\]\=\'(.*?)\';', content).group(1)
            print(name)
        except Exception, e:
            print('login failed!')
            print(content)
            return {'login': False, 'error': e}
        # msg = u'Weibo name is : %s\n' % name
        # print(msg.encode('utf-8'))
        return {'login': True, 'name': name}

if __name__ == '__main__':
    with open('data/cookies.txt', 'r') as f:
        cookies = f.read()
    wb = WeiboLG(cookies)
    print(wb.check_login())
