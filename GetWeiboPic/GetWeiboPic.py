# coding:utf-8

import requests
import os
import json
import re
import urlparse
import time
from bs4 import BeautifulSoup

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

# alb_list_url : 根据uid获取用户相册列表：http://photo.weibo.com/albums/get_all?uid=5228056212&page=1&count=5&__rnd=1432862078976
# pic_list_url : 根据uid和相册album_id获取相册所有照片信息：http://photo.weibo.com/photos/get_all?uid=5228056212&album_id=3736693483152486&count=30&page=1&type=3&__rnd=1432862078693
# pic_url : 照片地址为：pic_host + '/large/' + pic_name

headers = {'User-Agent': 'Baiduspider ( http://www.baidu.com/search/spider.htm)'}

def get_user_info(url):
    """
    获取用户信息，包括：
        用户微博名（keywords的第一个），
        用户uid（去掉url查询信息后的最后一串数字）
    return dict {'name' : name, 'uid' : uid}
    """
    if url.isdigit():
        url = 'http://weibo.com/%s' % url
    uid = urlparse.urlparse(url).path.split('/')[-1]
    if not uid.isdigit():
        exit('url error, please check.')
    try:
        # print url
        content = requests.get(url, headers = headers).content
        soup = BeautifulSoup(content)
        # print soup
        name = soup.find('meta', attrs = {'name' : 'keywords'})['content'].split('，')[0]
    except Exception,e:
        name = uid
    # print name
    # exit()
    print 'Weibo name is : %s' % name
    return {'name' : name, 'uid' : uid}

def get_album_list_json(uid):
    """
    获取用户相册列表json信息
    return json
    """
    alb_list_url = 'http://photo.weibo.com/albums/get_all?uid=%s&count=99' % uid
    albums_content = requests.get(alb_list_url, headers = headers).content
    print unicode(albums_content, 'cp936')
    exit()
    albums_json = json.loads(unicode(albums_content, 'cp936'))
    return albums_json

def get_pic_list_json(uid, album_id):
    """
    获取相册内全部图片信息
    return json
    """
    pic_list_url = 'http://photo.weibo.com/photos/get_all?uid=%s&album_id=%s&count=9999' % (uid, album_id)
    pic_content = requests.get(pic_list_url, headers = headers).content
    pic_json = json.loads(unicode(pic_content, 'cp936'))
    return pic_json

def create_path(path_name):
    """
    path路径应该为：./weibo/用户名/相册名/
    return 路径path
    """
    path = os.getcwd()
    path = os.path.join(os.getcwd(), 'weibo/%s' % path_name)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def download_pic(pic_json, path):
    """
    下载图片
    """
    pic_num = pic_json['data']['total']
    num = 1
    for pic in pic_json['data']['photo_list']:
        pic_url = '%s/large/%s' % (pic['pic_host'], pic['pic_name'])
        pic_time = format_time(pic['timestamp'])
        pic_caption = pic['caption_render'].decode('utf-8')[:80].encode('utf-8')
        pic_ext = os.path.splitext(pic['pic_name'])[1]
        pic_name = '%s%s%s' % (pic_time, pic_caption, pic_ext)
        print pic_name


def get_weibo_pic_start(url):
    """
    运行

    """
    # 获取用户信息
    info = get_user_info(url)
    uid = info['uid']
    # 获取用户相册列表json信息
    albums_json = get_album_list_json(uid)
    albums_total = albums_json['data']['total']
    if albums_total:
        for album in albums_json['data']['album_list']:
            album_id = album['album_id']
            capton = album['caption']
            pic_num = album['count']['photos']
            album_name = ('[%s]%s' % (pic_num, caption)).decode('utf-8')
            if pic_num:
                pic_json = get_pic_list_json(uid, album_id)
                path_name = '%s/%s' % (info['name'], album_name)
                path = create_path(path_name)
                download_pic(pic_json, path)
            else:
                print '%s is empty!' % album_name
    else:
        print 'not found albums!'

def format_time(tsp = 0):
    if not tsp:
        tsp = time.time()
    time_struct = time.localtime(tsp)
    return time.strftime("[%Y-%m-%d %H：%M：%S]", time_struct)

get_weibo_pic_start('http://weibo.com/u/5228056212')