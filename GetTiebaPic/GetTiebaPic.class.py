# -*- coding:utf-8 -*-

import os, sys, json, re, requests, urlparse
from bs4 import BeautifulSoup

reload(sys)
sys.setdefaultencoding('utf-8')

class GetTiebaPic(object):
    _url = 'sdsd'

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value


t = GetTiebaPic()

t.url = 'http://sdasdf/'

print t.url
    