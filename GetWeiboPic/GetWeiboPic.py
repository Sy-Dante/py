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
import urlparse
import ConfigParser
import threading
# import chardet
from bs4 import BeautifulSoup
# logging.basicConfig(level=logging.DEBUG)

from WBLogin import wblogin
import WeiboDB

reload(sys)
sys.setdefaultencoding("utf-8")

def pr_e(arg='STOP'):
    """断点调试.
    """
    try:
        print(json.dumps(arg, sort_keys=True, indent=4))
        print(' ↑↑\n ↑↑\tIt`s used json.dumps().\n')
    except:
        print(arg)
    exit()

# 头信息
html_meta = '<meta content="text/html; charset=utf-8" http-equiv="Content-Type" />\n'
# js脚本
html_js = '\n<script type="text/javascript">window.onload=function(){var img = document.querySelectorAll(".pic img"); var len = img.length; var padding = 80; for (var i = 0; i < len; i++){img[i].onclick = function(){if (this.offsetWidth <= 100 || this.offsetHeight <= 100){var width = window.innerWidth - padding > this.naturalWidth ? this.naturalWidth : window.innerWidth - padding; var height = this.naturalHeight * (width / this.naturalWidth); this.style.maxWidth = width; this.style.maxHeight = height; this.style.cursor = "zoom-out"; }else{this.style.maxWidth = 100; this.style.maxHeight = 100; this.style.cursor = "zoom-in"; } } } }</script>\n'
# css样式
html_css = '\n<style type="text/css">* {padding: 0px; margin: 0px; } body {margin: 0px auto; max-width: 1000px; padding: 10px; } .update, .num {padding: 10px 0px 10px 670px; font-weight: bolder; color: grey; } ul::after {content:""; display: block; clear: both; } li {float: left; list-style: none; margin: 5px; border: 1px solid gold; padding: 1px; box-shadow: 0 0 5px gold; } .pic img {max-height: 100px; max-width: 100px; cursor: zoom-in; display: block; } .weibo {border-radius: 15px; border: 1px solid grey; padding: 10px; box-shadow: 0 0 5px grey; } .time {border-radius: 5px; border: 1px solid pink; padding: 2px; box-shadow: 0 0 5px pink; margin-bottom: 5px; } .content {border-radius: 5px; border: 1px solid lightblue; padding: 2px; box-shadow: 0 0 5px lightblue; margin-bottom: 5px; } .pic {border-radius: 5px; border: 1px solid lightblue; padding: 2px; box-shadow: 0 0 5px lightblue; margin-bottom: 25px; }</style>\n'

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
    url = str(url)
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
        name = soup.find('meta', attrs={'name': 'keywords'})['content'].split('，')[0]
    except Exception:
        name = uid
    msg = u'Weibo name is : %s\n' % name
    print(msg.encode('utf-8'))
    return (name, uid)

def get_album_list_json(uid):
    """获取用户相册列表json信息.

    Args:
        uid: 用户UID.

    Returns:
        json albums_json: 相册json数据.
    """
    alb_list_url = 'http://photo.weibo.com/albums/get_all?uid=%s&count=99' % uid
    albums_content = session.get(alb_list_url).content
    try:
        albums_json = json.loads(unicode(albums_content, 'ISO-8859-2')) # cp936
    except Exception, e:
        print('####### %s' % alb_list_url)
        logging.exception(e)
        time.sleep(5)
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
                    'uid=%s&album_id=%s&type=%s&page=%s&count=%s' %
                    (uid, album_id, pic_type, pic_page, pic_count))
    pic_content = session.get(pic_list_url).content
    try:
        pic_json = json.loads(unicode(pic_content, 'ISO-8859-2'))
    except Exception, e:
        print('####### %s' % pic_list_url)
        logging.exception(e)
        time.sleep(5)
    # pr_e(pic_json)
    return pic_json

def create_path(path_name):
    """在当前文件夹的weibo文件夹下创建目录.

    Args:
        path_name: 用户名/相册名  如： sy/face_album.

    Returns:
        path: 路径如 ./weibo/sy/face_album.
    """
    path = os.getcwd()
    path = os.path.join(path, 'weibo')
    path = os.path.join(path, path_name)
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
            # 2010-11月以前[pic_name]没有带文件拓展名
            pic_ext = os.path.splitext(pic['pic_name'])[1] if os.path.splitext(pic['pic_name'])[1] else '.jpg'
            pic_name = u'%s%s' % (pic_time, pic_caption)
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
                                 '<div class="content">%s</div>\n\t'
                                 '<div class="pic">\n\t\t<ul>\n' %
                                 (pic_time, pic_content)).encode('utf-8'))
            last_pic_name = pic_name
            pic_name = u'%s[%d]%s%s' % (pic_time, pic_index, pic_caption, pic_ext)
            pic_name = re.sub('#', '＃', pic_name)
            # 按时间创建文件夹: N-不按时间分类，Y-按年分类，M-按月分类
            time_models = {'N': '', 'Y': pic_time[1:5], 'M': pic_time[1:8]}
            global dir_model
            time_part = time_models.get(dir_model, '')
            # 写入图片信息
            weibo_file.write((u'\t\t\t<li><img src="./%s/%s" /></li>\n' %
                             (time_part, pic_name)).encode('utf-8'))
            # continue
            # 保存图片
            time_path = os.path.join(path, time_part)
            if not os.path.exists(time_path):
                os.makedirs(time_path)
            file_path = os.path.join(time_path, pic_name.encode('utf-8'))
            download_percent = download_num * 100 / pic_num
            if not os.path.exists(file_path):
                print((u'% 3d / % 3d. download %d%% : %s' %
                      (download_num, pic_num,
                      download_percent, pic_name)).encode('utf-8'))
                fpic = requests.get(pic_url).content
                with open(file_path, 'wb') as f:
                    f.write(fpic)
                global pub_count
                pub_count += 1
            else:
                print((u'% 3d / % 3d. download %d%% : %sFile already exists! Ignore download.' %
                      (download_num, pic_num, download_percent, pic_time)).encode('utf-8'))
                global pub_jump
                pub_jump += 1
                continue
        except BaseException, e:
            print((u'\n----------\n\nThis picture download failed!\n Picture url: %s\n'
                  ' Error: %s\n\n----------\n' % (pic_url, e)).encode('utf-8'))
            download_error += 1
    return (download_num, download_error, last_pic_name, pic_index)

def get_albums_pic(album, name, uid, info_file, amount, download_only_weibo_map):
    """下载相册内图片

    Args:
        album: 相册json数据
        name: 用户名
        uid: 用户UID
        info_file: 相册信息文件句柄
        amount: 要下载的信息数量.
        download_only_weibo_map: 下载模式.
            True 只下载微博配图
            False 下载全部相册

    Returns:
        下载图片，显示信息.
    """
    # 获取相册信息
    album_id = album['album_id']
    caption = album['caption']
    pic_num = int(album['count']['photos'])
    pic_type = album['type']
    album_name = ('%s' % caption).decode('utf-8')
    # 图片存储路径
    path_name = os.path.join(name, album_name)
    if caption == '面孔专辑':return
    try:
        # 微博配图没有这个数据，所以可以用于判断是否为微博配图
        is_set = album['cover_photo_id']
        pic_count = 100
        if download_only_weibo_map:
            return #当只需要微博配图时
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
        with open(os.path.join(path, '微博信息.html'), 'w') as weibo_file:
            weibo_file.write(html_meta)
            # 样式
            weibo_file.write(html_css)
            # 脚本
            weibo_file.write(html_js)
            # 相册信息
            weibo_file.write('<h2 class="tags">#  %s</h2>\n'
                             '<div class="update">更新时间：%s</div>\n'
                             '<div class="num">图片数量：%d</div>\n'
                             '<div class="weibo">\n' %
                             (album_name, format_time(), pic_num))
            for i in range(count_page):
                print((u'\n---limit:%s\ncurrent: %s / count: %s ' %
                      (pic_count, current_page, count_page)).encode('utf-8'))
                # continue
                # 获取相册json信息
                pic_json = get_pic_list_json(uid, album_id, pic_type, current_page, pic_count)
                # 下载图片，保存下载信息
                download_num, download_error, last_pic_name, pic_index = download_pic(
                    pic_json, path, download_num, download_error,
                    last_pic_name, pic_index, weibo_file, pic_num)
                current_page += 1
            # 闭合标签
            weibo_file.write('\t\t</ul>\n\t</div>\n</div>\n')
        info_file.write('%s<h2 class="tags">#  %s</h2>\n'
                        '<div class="update">更新时间：%s</div>\n'
                        '<div class="num">图片数量：%d</div>\n' %
                        (html_meta, album_name, format_time(album['updated_at_int']), download_num))
        print((u'download complete!\n\tsuccessful : %d\n\tfailed : %d\n' %
              (download_num, download_error)).encode('utf-8'))
        global pub_total
        global pub_error
        pub_total += download_num
        pub_error += download_error
    else:
        print((u'%s is empty!' % album_name).encode('utf-8'))

def run(url, amount, download_only_weibo_map, is_thread):
    """运行.

    Args:
        url: 微博用户首页链接.
        amount: 要下载的信息数量.
        download_only_weibo_map: 下载模式.
            True 只下载微博配图
            False 下载全部相册
        is_thread: 是否启用多线程

    Returns:
        下载图片，显示信息.
    """
    # 获取用户信息
    name, uid = get_user_info(url)
    # 获取用户相册列表json信息
    albums_json = get_album_list_json(uid)
    albums_total = albums_json['data']['total']
    if albums_total:
        # 存储各相册概略信息
        info_path = create_path(name)
        with open(os.path.join(info_path,'相册信息.html'), 'w') as info_file:
            # 开启多线程下载相册图片
            thread_list = [threading.Thread(target=get_albums_pic,
                           args=(album, name, uid, info_file, amount, download_only_weibo_map),
                           name=(name + '_' + album['caption'].encode('utf-8')))
                           for album in albums_json['data']['album_list']]
            if is_thread is True:
                for t in thread_list:
                    t.start()
                for t in thread_list:
                    t.join()
            else:
                for t in thread_list:
                    t.start()
                    t.join()
            info_file.write('<h4>文件更新时间:<em>%s</em></h4>' % format_time())
    else:
        print('not found albums!')

def format_time(tsp=0):
    """格式化时间戳，主要用于加在文件名中（冒号为全角）.

    Args:
        tsp: 时间戳.

    Returns:
        返回格式化好的时间.
    """
    time_struct = time.localtime(tsp if tsp else time.time())
    return time.strftime("[%Y-%m-%d %H：%M：%S]", time_struct)

def get_weibo_pic(urls, amounts=99999, download_only_weibo_map=False, is_thread=True):
    """启用多线程下载多个用户的相册.

    Args:
        urls: 用户链接或id字典(字典的键名只是为了标识，与程序不相关).
        amounts: 下载数量，当为数组时，按顺序与用户匹配.
        download_only_weibo_map: 下载模式.
            True 只下载微博配图
            False 下载全部相册
        is_thread: 是否启用多线程

    Returns:
        下载图片，显示信息.
    """
    try:
        start = time.clock()
        global pub_total
        global pub_count
        global pub_jump
        global pub_error
        global session
        global dir_model
        dir_model='N'
        pub_total = 0
        pub_count = 0
        pub_jump = 0
        pub_error = 0
        conf = ConfigParser.ConfigParser()
        conf.read('user.conf')
        name = conf.get('weibo', 'name')
        pw = conf.get('weibo', 'pw')
        session = wblogin(name, pw)
        if isinstance(urls, dict) and isinstance(amounts, (int, list)):
            for i in range(5):
                if isinstance(amounts, int):
                    thread_list = [threading.Thread(
                                   target=run,
                                   args=(url, amounts, download_only_weibo_map, is_thread),
                                   name=key)
                                   for key, url in urls.iteritems()]
                elif isinstance(amounts, list):
                    thread_list = [threading.Thread(
                                   target=run,
                                   args=(url, amount, download_only_weibo_map, is_thread),
                                   name=key)
                                   for key, url, amount in zip(urls.keys(), urls.values(), amounts)]
                else:
                    break
                if is_thread is True:
                    for t in thread_list:
                        t.start()
                    for t in thread_list:
                        t.join()
                else:
                    for t in thread_list:
                        t.start()
                        t.join()
                if pub_error == 0:
                    break
                else:
                    runtime = time.clock() - start
                    print('\n-------------\nrun time: %dmin %dsec\ntotal: %d\ndownload: %d\njump: %d\nerror: %d\n------continue(%d)---\n' %
                          (runtime//60, runtime%60, pub_total, pub_count, pub_jump, pub_error, i))
                    pub_total = 0
                    pub_count = 0
                    pub_jump = 0
                    pub_error = 0
                    time.sleep(5)
        else:
            raise TypeError('Unexpect Arguement Type!')
    except requests.exceptions.ConnectionError, e:
        print('Network connect failed!\n\tError: %s' % e)
    except BaseException, e:
        print('Download failed!\nError: %s\n' % e)
        # logging.exception(e)
    finally:
        runtime = time.clock() - start
        print('\n-------------\nrun time: %dmin %dsec\ntotal: %d\ndownload: %d\njump: %d\nerror: %d\nrun(%d)' %
              (runtime//60, runtime%60, pub_total, pub_count, pub_jump, pub_error, i+1))
        os.system('pause')

def parse_json(filename):
    """将带注释的json文件解析为json数据
    """
    with open(filename, 'r') as json_info:
        json_str = json_info.read()
    json_str = re.sub(r'//.*?\n', '', json_str)
    json_str = re.sub(r'[ |\n]', '', json_str)
    json_str = re.sub(r',\}', '}', json_str)
    return json.loads(json_str)

if __name__ == '__main__':
    # with WeiboDB.WeiboDB() as db:
    #     urls = db.selectDict()

    urls = parse_json('data/weibo.json')

    get_weibo_pic(urls, 120, download_only_weibo_map=False, is_thread=False)





"""
{
    # Team SⅡ
    'XiaoAi': 3050708243,
    'SiSi': 3050742117,
    # Team NⅡ
    'LuLi': 3669076064,
    'kiku': 3669102477,
    # Team HⅡ
    'Sheep': 5228056212,
    'Monster': 5230466807,
    'LuBao': 5229864870,
    'WanQing': 5229579490,
    'kuma-李清扬': 5231168847,
    # Team X
    'Maruko': 5490958194,
    'coco': 5460952383,
    'RanRan': 5479678683,
    'ws': 5491330253,

    # Team Fans
    # 'SoRuri': 5581868113,
    # '会长fans-加菲': 2316839037, # 大图 撸力
    # '孟孟fans-微凉': 1837085131, # 小图
    # # 400
    # '大哥fans-芒果': 278332254, # 30+ ++ 大图
    # '小菊fans-双子座': 2623190960, # 30+ ++ 大图
    # '小菊fans-Eg': 3240835062, # 60+ ++ 大图
    # '阿黄fans-zzh': 1889585464, # 160+ ++ 大图
    # '阿黄fans-雪山': 1701598311, # 300+ ++ 大图
    # '小菊fans-zxs': 1694575520, # 350+ ++ 大图

    # '小四fans-塞纳河': 5473551372, # 600+ 大图
    # '发卡fans-山里人': 1533507090, # 1600+ 大图
    # '小菊fans-Wils': 1244586691, # 3300+ 大图
    # '阿黄fans-Sy_桃': 2195845005, # 150+ 小图
    # '小菊fans-LY': 2252395501, # 600+ 小图
    # '朵朵fans-115': 2962312110, # 750+ -- 小图

    # 'test1': 5047712285,
    # 'test2': 2390627070,

    # Team Out
    # # '夏奈-杨吟雨': 5225561029,
}
"""

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
            //and so on...
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
            //and so on...
        ], 
        "total": 11
    }, 
    "msg": "", 
    "result": true, 
    "timestamp": 1433219899
}
"""
