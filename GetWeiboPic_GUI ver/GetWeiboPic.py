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

# import chardet
# logging.basicConfig(level=logging.DEBUG)

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

def format_time(tsp=0):
    """格式化时间戳，主要用在文件名中（冒号为全角）.

    Args:
        tsp: 时间戳.

    Returns:
        返回格式化好的时间.
    """
    time_struct = time.localtime(tsp if tsp else time.time())
    return time.strftime("[%Y-%m-%d %H：%M：%S]", time_struct)

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

class LoginError(Exception):
    pass

class GetWeiboPic(object):

    def _getJson(self, url):
        try:
            content = self._session.get(url).content
            the_json = json.loads(unicode(content, 'ISO-8859-2')) # cp936
        except requests.exceptions.ConnectionError, e:
            raise LoginError('网络连接失败！')
        except (UnicodeError, ValueError), e:
            print('####### 获取json信息失败： %s' % url)
            logging.exception(e)
            raise LoginError('获取失败！Cookies信息可能已过期！')
        return the_json

    def getAlbumListJson(self, uid):
        """获取用户相册列表json信息.

        Args:
            uid: 用户UID.

        Returns:
            相册json数据.
        """
        alb_list_url = 'http://photo.weibo.com/albums/get_all?uid=%s&count=99' % uid
        return self._getJson(alb_list_url)

    def getPicListJson(self, uid, album_id, pic_type, pic_page, pic_count):
        """获取相册内图片json信息

        Args:
            uid: 用户UID.
            album_id: 相册ID.
            pic_type: 从返回json中获得，意义不明.
            pic_page: 所在页
            pic_count: 要取得的信息量.

        Returns:
            图片列表json数据.
        """
        pic_list_url = ('http://photo.weibo.com/photos/get_all?'
                        'uid=%s&album_id=%s&type=%s&page=%s&count=%s' %
                        (uid, album_id, pic_type, pic_page, pic_count))
        return self._getJson(pic_list_url)

    def _downloadPic(self, pic_json, path, download_num, 
            download_error, last_pic_name, pic_index, pic_num, pbar):
        """下载图片，最底层下载方法。

        Args:
            pic_json: 图片列表json数据.
            path: 路径.
            download_num: 已下载数.
            download_error: 下载失败数.
            last_pic_name: 上一个图片名.
            pic_index: 图片序号.
            pic_num: 要下载的图片数量.
            pbar: 进度条.

        Returns:
            download_num: 已下载数.
            download_error: 下载失败数.
            last_pic_name: 上一个图片名.
            pic_index: 图片序号.
        """
        # pic_num = pic_json['data']['total']
        for pic in pic_json['data']['photo_list']:
            download_num += 1
            pbar.update(download_num, pic_num)
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
                    pic_index = 1
                last_pic_name = pic_name
                pic_name = u'%s[%d]%s%s' % (pic_time, pic_index, pic_caption, pic_ext)
                pic_name = re.sub('#', '＃', pic_name)
                # 按时间创建文件夹: N-不按时间分类，Y-按年分类，M-按月分类
                time_models = {'N': '', 'Y': pic_time[1:5], 'M': pic_time[1:8]}
                time_part = time_models.get(self.dir_model, '')
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
                    self._pub_count += 1
                else:
                    print((u'% 3d / % 3d. download %d%% : %sFile already exists! Ignore download.' %
                          (download_num, pic_num, download_percent, pic_time)).encode('utf-8'))
                    self._pub_jump += 1
            except IOError, e:
                print((u'\n----------\n\nThis picture download failed!\n Picture url: %s\n'
                      ' Error: %s\n\n----------\n' % (pic_url, e)).encode('utf-8'))
                download_error += 1
            if download_num == pic_num: break
        return (download_num, download_error, last_pic_name, pic_index)

    def getAlbumsPic(self, album, name, uid, info_file):
        """下载相册内图片，根据相册json，调用self._downloadPic()下载

        Args:
            album: 相册json数据
            name: 用户名
            uid: 用户UID
            info_file: 相册信息文件句柄，收集各相册信息

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
        except KeyError:
            # 【微博配图】相册只能一次取30条数据
            pic_count = 30
        if pic_num:
            # 要下载的图片数量
            pic_num = pic_num if pic_num < self.amount else self.amount
            # 创建进度条
            pbar = PBar(self.fm, '%s_%s' % (name, album_name), pic_num)
            pbar.pack()
            self.fm.update()
            # 创建路径
            path = create_path(path_name)
            # 下载所用变量初始化（已下载数，下载失败数，上一个图片名，图片序号）
            download_num, download_error, last_pic_name, pic_index = 0, 0, '', 1
            print((u'%s : Total %s , downloading...' % (album_name, pic_num)).encode('utf-8'))
            # 总页数
            count_page = int(math.ceil(pic_num / pic_count))
            current_page = 1
            for i in range(count_page):
                print((u'\n---limit:%s\ncurrent: %s / count: %s ' %
                      (pic_count, current_page, count_page)).encode('utf-8'))
                # continue
                # 获取相册json信息
                pic_json = self.getPicListJson(uid, album_id, pic_type, current_page, pic_count)
                # 下载图片，保存下载信息
                download_num, download_error, last_pic_name, pic_index = self._downloadPic(
                    pic_json, path, download_num, download_error,
                    last_pic_name, pic_index, pic_num, pbar)
                current_page += 1
            # 闭合标签
            info_file.write('<h2 class="tags">#  %s</h2>\n'
                            '<div class="update">更新时间：%s</div>\n'
                            '<div class="num">图片数量：%d</div>\n' %
                            (album_name, format_time(album['updated_at_int']), download_num))
            print((u'download complete!\n\tsuccessful : %d\n\tfailed : %d\n' %
                  (download_num, download_error)).encode('utf-8'))
            self._pub_total += download_num
            self._pub_error += download_error
        else:
            print((u'%s is empty!' % album_name).encode('utf-8'))

    def getUserPic(self, user):
        """运行.

        Args:
            user: 微博用户信息 (nickname, weibo_id).

        Returns:
            下载图片，显示信息.
        """
        # 获取用户信息
        name, uid = user
        # 获取用户相册列表json信息
        albums_json = self.getAlbumListJson(uid)
        albums_total = albums_json['data']['total']
        if albums_total:
            # 存储各相册概略信息
            info_path = create_path(name)
            with open(os.path.join(info_path,'相册信息.html'), 'w') as info_file:
                # # 开启多线程下载相册图片
                # thread_list = [threading.Thread(target=self.getAlbumsPic,
                #                args=(album, name, uid, info_file),
                #                name=(name + '_' + album['caption'].encode('utf-8')))
                #                for album in albums_json['data']['album_list']]
                # if self.is_thread is True:
                #     for t in thread_list:
                #         t.start()
                #     for t in thread_list:
                #         t.join()
                # else:
                #     for t in thread_list:
                #         t.start()
                #         t.join()
                for album in albums_json['data']['album_list']:
                    self.getAlbumsPic(album, name, uid, info_file)
                info_file.write('<h4>文件更新时间:<em>%s</em></h4>' % format_time())
        else:
            print('not found albums!')

    def getWeiboPic(self, parent=None, session='', users=[], amount=99999, dir_model='N', is_thread=True):
        """启用多线程下载多个用户的相册.

        Args:
            users: [(nickname, weibo_id),].
            amounts: 下载数量.
            dir_model: 按时间创建文件夹: N-不按时间分类，Y-按'年'分类，M-按'月'分类.
            is_thread: 是否启用多线程.

        Returns:
            下载图片，显示信息.
        """
        self._session = session
        self.amount = amount
        self.dir_model = dir_model
        self.is_thread = is_thread
        self.fm = Tk.Frame(parent)
        self._msg = Tk.StringVar()
        self.fm.pack()
        Tk.Label(parent, textvariable=self._msg, fg='#191').pack()
        try:
            start = time.clock()
            self._pub_total = 0
            self._pub_count = 0
            self._pub_jump = 0
            self._pub_error = 0
            error = ''
            # thread_list = [threading.Thread(
            #                target=self.getUserPic,
            #                args=(user,),
            #                name=user[1])
            #                for user in users]
            # if self.is_thread is True:
            #     for t in thread_list:
            #         t.start()
            #     for t in thread_list:
            #         t.join()
            # else:
            #     for t in thread_list:
            #         t.start()
            #         t.join()
            for user in users:
                self.getUserPic(user)
        except requests.exceptions.ConnectionError, e:
            error = 'Network connect failed!\n\tError: %s' % e
            print(error)
        except Exception, e:
            error = 'Download failed!\nError: %s\n' % e
            print(error)
            # logging.exception(e)
        finally:
            runtime = time.clock() - start
            msg = ('%s\n-------------\nrun time: %dmin %dsec\ntotal: %d\ndownload: %d\njump: %d\nerror: %d' %
                  (error, runtime//60, runtime%60, self._pub_total, self._pub_count, self._pub_jump, self._pub_error))
            print(msg)
            self._msg.set(msg)


class PBar(Tk.Frame):

    def __init__(self, parent, text, count=30, side=Tk.LEFT, anchor=Tk.W, **kw):
        """"""
        # self.parent = parent
        Tk.Frame.__init__(self, parent, kw)
        Tk.Label(self, text=text, width=20, anchor=Tk.E).pack(side=side, expand=Tk.YES)
        self._val = Tk.IntVar()
        self._pbar = ttk.Progressbar(self, length=500, variable=self._val, maximum=count)
        self._pbar.pack(side=side, expand=Tk.YES)
        self._percent = Tk.StringVar()
        self._percent.set('0% 0/0')
        Tk.Label(self, textvariable=self._percent, width=15, anchor=anchor).pack(side=side, expand=Tk.YES)

    def update(self, i, tatol):
        self._val.set(i)
        self._percent.set('%.1f%% %d/%d' % (i/tatol*100, i, tatol))
        self._pbar.update()
        # self.parent.update()

    def start(self):
        self._pbar.start()

    def stop(self):
        self._pbar.stop()

class DownloadPic(Tk.Frame):

    def __init__(self, parent, **kw):
        Tk.Frame.__init__(self, parent, **kw)
        self.pack()
        self.canvas=Tk.Canvas(self, width=750, height=250)
        self.scrollb=ttk.Scrollbar(self, orient=Tk.VERTICAL,command=self.canvas.yview)
        self.scrollb.pack(side=Tk.RIGHT, fill=Tk.Y)
        self.canvas['yscrollcommand'] = self.scrollb.set
        self.canvas.pack()
        self.canvas.bind_all("<MouseWheel>", self._onMousewheel)
        self.wb = GetWeiboPic()

    def update(self, users, session, amount=30):
        self.users = users
        self._session = session
        self.amount = amount

    def download(self):
        if hasattr(self, 'fm'):
            self.fm.destroy()
        self.fm = Tk.Frame(self.canvas)
        self.fm.pack()
        self.canvas.create_window((0,0), window=self.fm, tags="self.fm")
        self.fm.bind("<Configure>", self._onFrameConfigure)
        self._last_h = self.fm.winfo_height()
        self.wb.getWeiboPic(self.fm, self._session, self.users, self.amount)

    def _onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("self.fm"))
        new_h = self.fm.winfo_height()
        if self._last_h != new_h:
            self._last_h = new_h
            self.canvas.yview_moveto(1)

    def _onMousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta//120), "units")


if __name__ == '__main__':

    def get_session():
        session = requests.Session()
        with open('data/cookies.txt', 'r') as f:
            cookies = f.read()
        session.cookies.update({'Cookie': cookies,})
        session.headers.update({
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.8 Safari/537.36',
        })
        return session
    top = Tk.Tk()
    fm = Tk.Frame(top)
    fm.pack()
    down_fm = DownloadPic(fm)
    down_fm.update([('ruri', 3669076064), ('Sheep', 5228056212)], get_session())
    ttk.Button(top, text="run", command=down_fm.download).pack()
    down_fm.pack()
    top.mainloop()




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
