#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals



import re
import json
import base64
import binascii

import rsa
import requests

# import logging
# logging.basicConfig(level=logging.DEBUG)

# ----------------------------------------

# import requests
import os
# import json
# import re
import urlparse
import time
from bs4 import BeautifulSoup
import math
import ConfigParser

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

WBCLIENT = 'ssologin.js(v1.4.5)'
user_agent = (
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.11 (KHTML, like Gecko) '
    'Chrome/20.0.1132.57 Safari/536.11'
)
session = requests.session()
session.headers['User-Agent'] = user_agent


def encrypt_passwd(passwd, pubkey, servertime, nonce):
    key = rsa.PublicKey(int(pubkey, 16), int('10001', 16))
    message = str(servertime) + '\t' + str(nonce) + '\n' + str(passwd)
    passwd = rsa.encrypt(message.encode('utf-8'), key)
    return binascii.b2a_hex(passwd)


def wblogin(username, password):
    resp = session.get(
        'http://login.sina.com.cn/sso/prelogin.php?'
        'entry=sso&callback=sinaSSOController.preloginCallBack&'
        'su=%s&rsakt=mod&client=%s' %
        (base64.b64encode(username.encode('utf-8')), WBCLIENT)
    )

    pre_login_str = re.match(r'[^{]+({.+?})', resp.text).group(1)
    pre_login = json.loads(pre_login_str)

    data = {
        'entry': 'weibo',
        'gateway': 1,
        'from': '',
        'savestate': 7,
        'userticket': 1,
        'ssosimplelogin': 1,
        'su': base64.b64encode(requests.utils.quote(username).encode('utf-8')),
        'service': 'miniblog',
        'servertime': pre_login['servertime'],
        'nonce': pre_login['nonce'],
        'vsnf': 1,
        'vsnval': '',
        'pwencode': 'rsa2',
        'sp': encrypt_passwd(password, pre_login['pubkey'],
                             pre_login['servertime'], pre_login['nonce']),
        'rsakv' : pre_login['rsakv'],
        'encoding': 'UTF-8',
        'prelt': '115',
        'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.si'
               'naSSOController.feedBackUrlCallBack',
        'returntype': 'META'
    }
    resp = session.post(
        'http://login.sina.com.cn/sso/login.php?client=%s' % WBCLIENT,
        data=data
    )
    login_url = re.search(r'replace\([\"\']([^\'\"]+)[\"\']', resp.text).group(1)
    resp = session.get(login_url)
    json_data = json.loads(re.search(r'\((.*)\)', resp.text).group(1))
    result = json_data['result'] == True
    if result is False and 'reason' in json_data:
        return result, json_data['reason']
    return result
    # return json.loads(login_str)

# --------------------------------------------------------------------------------------
def get_user_info(url):
    """获取用户信息，包括：
            用户微博名（keywords的第一个），
            用户uid（去掉url查询信息后的最后一串数字）.

    Args:
        url: 微博用户首页链接.

    Returns:
        name: 用户微博名.
        uid: 用户UID.
    """
    # 当输入为数字时，将它当成微博ID，拼凑完整网址
    if url.isdigit():
        url = 'http://weibo.com/%s' % url
    # 获取微博ID
    uid = urlparse.urlparse(url).path.split('/')[-1]
    uid = re.search('[0-9]{5,20}', url).group()
    # pr_e(uid)
    if not uid:
        exit('url error, please check.')
    try:
        # 获取内容
        content = session.get(url).content
        soup = BeautifulSoup(content)
        # 获取微博名
        name = soup.find('meta', attrs = {'name' : 'keywords'})['content'].split('，')[0]
    except Exception:
        name = uid
    msg = u'Weibo name is : %s' % name
    print(msg.encode('utf-8'))
    return name, uid

def get_album_list_json(uid):
    """获取用户相册列表json信息.

    Args:
        uid: 用户UID.

    Returns:
        json albums_json: 相册json数据.
    """
    alb_list_url = 'http://photo.weibo.com/albums/get_all?uid=%s&count=99' % uid
    albums_content = session.get(alb_list_url).content
    albums_json = json.loads(unicode(albums_content, 'cp936'))
    # pr_e(albums_json)
    return albums_json

def get_pic_list_json(uid, album_id, pic_type, pic_page, pic_count):
    """获取相册内图片信息

    Args:
        uid: 用户UID.
        album_id: 相册ID.
        pic_type: 从返回json中获得，意义不明.
        pic_count: 要取得的信息量.

    Returns:
        pic_json: 图片列表json数据.
    """
    pic_list_url = ('http://photo.weibo.com/photos/get_all?'
                    'uid=%s&album_id=%s&type=%s&page=%s&count=%s' 
                    % (uid, album_id, pic_type, pic_page, pic_count))
    pic_content = session.get(pic_list_url).content
    pic_json = json.loads(unicode(pic_content, 'cp936'))
    # pr_e(pic_json)
    return pic_json

def create_path(path_name):
    """path路径应该为：./weibo/用户名/相册名/ .

    Args:
        path_name: 路径名如 sy/face_album

    Returns:
        path: 路径如 ./weibo/sy/face_album.
    """
    path = os.getcwd()
    path = os.path.join(os.getcwd(), 'weibo/%s' % path_name)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def download_pic(pic_json, path, download_num, download_error,
                 last_pic_name, pic_index, weibo_file, pic_num):
    """下载图片.

    Args:
        pic_json: 图片列表json数据.
        path: 路径.
        download_num: 已下载数.
        download_error: 下载失败数.
        last_pic_name: 上一个图片名.
        pic_index: 图片序号.
        weibo_file: 存储相册内微博具体信息.

    Returns:
        download_num: 已下载数.
        download_error: 下载失败数.
        last_pic_name: 上一个图片名.
        pic_index: 图片序号.
    """
    # pic_num = pic_json['data']['total']
    for pic in pic_json['data']['photo_list']:
        download_num += 1
        try:
            # 获取图片信息
            pic_url = '%s/large/%s' % (pic['pic_host'], pic['pic_name'])
            pic_time = format_time(pic['timestamp'])
            caption = pic['caption_render'].decode('utf-8')[:80].encode('utf-8')
            pic_caption = re.sub('[\\\/\:\*\?\|\"<>]', '_', caption)
            pic_content = pic['caption']
            pic_ext = os.path.splitext(pic['pic_name'])[1]
            pic_name = u'%s%s%s' % (pic_time, pic_caption, pic_ext)
            # 判断是否属于同一微博图片
            if pic_name == last_pic_name:
                pic_index += 1
            else:
                if download_num != 1:
                    # 闭合标签
                    weibo_file.write('\t\t</ul>\n\t</div>\n')
                pic_index = 1
                # 写入微博信息
                weibo_file.write((u'\t<div class="time">发博时间：%s</div>\n\t'
                                 '<div class="content" title="%s">%s</div>\n\t'
                                 '<div class="pic">\n\t\t<ul>\n'
                                 % (pic_time, pic['caption_render'], pic_content)).encode('utf-8'))
            last_pic_name = pic_name
            pic_name = u'%s[%d]%s%s' % (pic_time, pic_index, pic_caption, pic_ext)
            pic_name = re.sub('#', '＃', pic_name)
            # 写入图片信息
            weibo_file.write((u'\t\t\t<li><img src="./%s" title="%s" /></li>\n'
                              % (pic_name, pic['caption_render'])).encode('utf-8'))
            # continue
            # 保存图片
            file_path = os.path.join(path,pic_name.encode('utf-8'))
            if not os.path.exists(file_path):
                print((u'% 3d / % 3d. download %d%% : %s'
                      % (download_num, pic_num, download_num * 100 / pic_num, pic_name)).encode('utf-8'))
                fpic = requests.get(pic_url).content
                with open(file_path, 'wb') as f:
                    f.write(fpic)
            else:
                print((u'% 3d / % 3d. download %d%% : File already exists! Ignore download.'
                      % (download_num, pic_num, download_num * 100 / pic_num)).encode('utf-8'))
                # continue
        except Exception,e:
            print((u'\n----------\n\nThis picture download failed!\n Picture url: %s\n'
                  ' Error: %s\n\n----------\n' % (pic_url, e)).encode('utf-8'))
            download_error += 1
    return download_num, download_error, last_pic_name, pic_index


def get_weibo_pic_run(url, amount=9999):
    """运行.

    Args:
        url: 微博用户首页链接.
        amount: 要下载的信息数量.

    Returns:
        下载图片，显示信息.
    """
    # 获取用户信息
    name, uid = get_user_info(url)
    # 获取用户相册列表json信息
    albums_json = get_album_list_json(uid)
    albums_total = albums_json['data']['total']
    # 存储各相册概略信息
    info_path = create_path(name)
    info_file = open(os.path.join(info_path,'相册信息.html'), 'w')
    if albums_total:
        for album in albums_json['data']['album_list']:
            # 获取相册信息
            album_id = album['album_id']
            caption = album['caption']
            pic_num = int(album['count']['photos'])
            pic_type = album['type']
            album_name = ('%s' % caption).decode('utf-8')
            # 图片存储路径
            path_name = '%s/%s' % (name, album_name)
            try:
                # 微博配图没有这个数据，所以可以用于判断是否为微博配图
                is_set = album['cover_photo_id']
                pic_count = amount
                continue #当只需要微博配图时，可以取消此处注释
            except:
                # 【微博配图】相册只能一次取30条数据
                pic_count = 30
            if pic_num:
                pic_num = pic_num if pic_num < amount else amount
                # 创建路径
                path = create_path(path_name)
                # 下载所用变量初始化（已下载数，下载失败数，上一个图片名，图片序号）
                download_num, download_error, last_pic_name, pic_index = 0, 0, '', 1
                print((u'%s : Total %s , downloading...' % (album_name, pic_num)).encode('utf-8'))
                # 总页数
                count_page = int(math.ceil(pic_num / pic_count))
                current_page = 1
                # 存储相册内微博具体信息
                with open(os.path.join(path,'微博信息.html'), 'w') as weibo_file:
                    weibo_file.write('<meta content="text/html; charset=utf-8" http-equiv="Content-Type" />\n')
                    # 样式
                    weibo_file.write('\n<style type="text/css">* {padding: 0px; margin: 0px; } body {margin: 0px auto; width: 1000px; padding: 10px; } .update, .num {padding: 10px 0px 10px 670px; font-weight: bolder; color: grey; } ul::after {content:""; display: block; clear: both; } li {float: left; list-style: none; margin: 5px; border: 1px solid gold; padding: 1px; box-shadow: 0 0 5px gold; } .pic img {max-height: 100px; max-width: 100px; cursor: zoom-in; } .weibo {border-radius: 15px; border: 1px solid grey; padding: 10px; box-shadow: 0 0 5px grey; } .time {border-radius: 5px; border: 1px solid pink; padding: 2px; box-shadow: 0 0 5px pink; margin-bottom: 5px; } .content {border-radius: 5px; border: 1px solid lightblue; padding: 2px; box-shadow: 0 0 5px lightblue; margin-bottom: 5px; } .pic {border-radius: 5px; border: 1px solid lightblue; padding: 2px; box-shadow: 0 0 5px lightblue; margin-bottom: 25px; }</style>\n')
                    # 脚本
                    weibo_file.write('\n<script type="text/javascript">window.onload=function(){var img = document.querySelectorAll(".pic img"); var len = img.length; for (var i = 0; i < len; i++){img[i].onclick = function(){if (this.offsetWidth <= 100 || this.offsetHeight <= 100){this.style.maxWidth = this.naturalWidth; this.style.maxHeight = this.naturalHeight; this.style.cursor = "zoom-out"; }else{this.style.maxWidth = 100; this.style.maxHeight = 100; this.style.cursor = "zoom-in"; } } } }</script>\n')
                    # 相册信息
                    weibo_file.write('<h2 class="tags">#  %s</h2>\n'
                                     '<div class="update">更新时间：%s</div>\n'
                                     '<div class="num">图片数量：%d</div>\n'
                                     '<div class="weibo">\n' % (album_name, format_time(), pic_num))
                    for i in range(count_page):
                        print((u'\n---\ncurrent: %s / count: %s ' % (current_page, count_page)).encode('utf-8'))
                        # continue
                        # 获取相册json信息
                        pic_json = get_pic_list_json(uid, album_id, pic_type, current_page, pic_count)
                        # 下载图片，保存下载信息
                        download_num, download_error, last_pic_name, pic_index = download_pic(pic_json, path, download_num, download_error,
                                                                                              last_pic_name, pic_index, weibo_file, pic_num)
                        current_page += 1
                    # 闭合标签
                    weibo_file.write('\t\t</ul>\n\t</div>\n</div>\n')
                info_file.write('<h2 class="tags">#  %s</h2>\n'
                                '<div class="update">更新时间：%s</div>\n'
                                '<div class="num">图片数量：%d</div>\n'
                                % (album_name, format_time(), download_num))
                print((u'download complete!\n\tsuccessful : %d\n\tfailed : %d\n'
                                       % (download_num, download_error)).encode('utf-8'))
            else:
                print((u'%s is empty!' % album_name).encode('utf-8'))
    else:
        print('not found albums!')
    info_file.close()

def format_time(tsp=0):
    """格式化时间戳，主要用于加在文件名中（冒号为全角）.

    Args:
        tsp: 时间戳.

    Returns:
        返回格式化好的时间.
    """
    if not tsp:
        tsp = time.time()
    time_struct = time.localtime(tsp)
    return time.strftime("[%Y-%m-%d %H：%M：%S]", time_struct)

def get_weibo_pic(urls, amounts=9999):
    """循环下载多个用户的相册.

    Args:
        urls: 用户链接或id数组.
        amounts: 下载数量，当为数组时，按顺序与用户匹配.

    Returns:
        下载图片，显示信息.
    """
    if isinstance(urls, basestring) and isinstance(amounts, int):
        get_weibo_pic_run(urls, amounts)
    elif isinstance(urls, dict):
        if isinstance(amounts, int):
            for url in urls.values():
                get_weibo_pic_run(url, amounts)
        elif isinstance(amounts, list):
            for url,amount in zip(urls.values(), amounts):
                get_weibo_pic_run(url, amount)
    else:
        raise Exception('Arguement Error!')
# --------------------------------------------------------------------------------------


def pr_e(arg='STOP'):
    """断点调试.
    """
    try:
        print(json.dumps(arg, sort_keys=True, indent=4))
        print(' ↑↑\n ↑↑\tIt`s used json.dumps().\n')
    except:
        print(arg)
    exit()


if __name__ == '__main__':
    try:
        conf = ConfigParser.ConfigParser()
        conf.read('user.conf')
        name = conf.get('weibo', 'name')
        pw = conf.get('weibo', 'pw')
        if wblogin(name, pw):
            print('login successful!')
            get_weibo_pic({
                    # 'XiaoAi': '3050708243',
                    # 'LuLi': '3669076064',
                    # 'Monster': '5230466807',
                    # 'XiaoJu': '3669102477',
                    # 'Sheep': '5228056212',
                    # 'LuBao': '5229864870',
                    'test': '5581868113'
                })
        else:
            print('login failed!')
    except Exception, e:
        print('Download failed!\nError: %s' % e)
    finally:
        os.system('pause')




# 相册列表json数据格式：http://photo.weibo.com/albums/get_all?uid=5228056212&count=5
"""
{
    "code": 0, 
    "data": {
        "album_list": [
            {
                "album_id": "3736684058509627", 
                "album_order": "1406378366", 
                "answer": true, 
                "caption": "\u5934\u50cf\u76f8\u518c", 
                "count": {
                    "comments": 0, 
                    "likes": 0, 
                    "photos": 11, 
                    "retweets": 0
                }, 
                "cover_photo_id": 0, 
                "cover_pic": "http://tp1.sinaimg.cn/5228056212/180/5722853540/0", 
                "created_at": "2014-07-26", 
                "description": "", 
                "is_favorited": false, 
                "is_private": false, 
                "property": 1, 
                "question": "", 
                "source": "3818214747", 
                "sq612_pic": "http://tp1.sinaimg.cn/5228056212/180/5722853540/0", 
                "status": 255, 
                "thumb120_pic": "http://tp1.sinaimg.cn/5228056212/180/5722853540/0", 
                "thumb300_pic": "http://tp1.sinaimg.cn/5228056212/180/5722853540/0", 
                "timestamp": "1406378366", 
                "type": "18", 
                "uid": "5228056212", 
                "updated_at": "4\u67081\u65e5", 
                "updated_at_int": 1427886244, 
                "usort": null
            }, 
            and so on...
        ], 
        "total": 4
    }, 
    "msg": "", 
    "result": true, 
    "timestamp": 1433219753
}
"""

# 图片列表json数据：http://photo.weibo.com/photos/get_all?uid=5228056212&album_id=3736684058509627&count=30
"""
{
    "code": 0, 
    "data": {
        "album_id": "3736684058509627", 
        "photo_list": [
            {
                "album_id": "3736684058509627", 
                "caption": "", 
                "caption_render": "", 
                "count": {
                    "clicks": 2, 
                    "comments": 0, 
                    "likes": 0, 
                    "retweets": 0
                }, 
                "created_at": "4\u67081\u65e5", 
                "data": "{\"forbid_like\":0}", 
                "from": "<a href=\"http://app.weibo.com/t/feed/1FFmkH\" title=\"\u5fae\u76f8\u518c\">\u5fae\u76f8\u518c</a>", 
                "geo_description": "", 
                "is_cover": false, 
                "is_favorited": false, 
                "is_liked": false, 
                "latitude": 0, 
                "longitude": 0, 
                "longtitude": 0, 
                "mid": "0", 
                "original_time": 0, 
                "photo_id": "3826894637295801", 
                "pic_host": "http://ww2.sinaimg.cn", 
                "pic_name": "005HOofijw8eqq9w0wrz0j3050050mx5.jpg", 
                "pic_pid": "005HOofijw8eqq9w0wrz0j3050050mx5", 
                "pic_type": 1, 
                "pid": "005HOofijw8eqq9w0wrz0j3050050mx5", 
                "property": 1, 
                "source": "1039857299", 
                "status": "0", 
                "tags": "", 
                "timestamp": 1427886244, 
                "type": 2, 
                "uid": 5228056212, 
                "updated_at": "4\u67081\u65e5", 
                "visible": 1, 
                "visible_type": null
            }, 
            and so on...
        ], 
        "total": 11
    }, 
    "msg": "", 
    "result": true, 
    "timestamp": 1433219899
}
"""
