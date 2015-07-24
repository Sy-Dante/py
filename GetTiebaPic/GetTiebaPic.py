# coding:utf-8

import requests
import os
import json
import re
import time
import urlparse
from threading import Thread
from bs4 import BeautifulSoup

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

def get_info(url):
    """获取url信息

    Args:
        url: 帖子链接

    Returns:
        一个字典，包括:
            title: 帖子名
            kw: 吧名，如：firefox
            tid: 帖子的id
            url: 帖子链接，如：tieba.baidu.com_p_1234567890
    """
    if url.isdigit():
        url = 'http://tieba.baidu.com/p/%s' % url
    content = requests.get(url).content
    soup = BeautifulSoup(content)

    # 用title做文件名，所以需要转义一些非法字符
    title = re.sub('[\\\/\:\*\?\|\"<>]', '_', soup.find('title').text)
    try:
        result = urlparse.urlparse(url)
        params = urlparse.parse_qs(result.query,True)
        kw = params['kw'][0]
        tid = params['tid'][0]
    except:
        try:
            kw = soup.find('meta', attrs = {'fname' : True})['fname']
            url = url.split('?')[0].split('#')[0]
            tid = url.split('/')[-1]
            if not tid.isdigit():
                raise TypeError('tid isn`t a number.')
        except:
            exit('url error, please check.')
    url = '_'.join(url.split('/')[2:])
    return {'title' : title, 'kw' : kw, 'tid' : tid, 'url' : url}

def get_download_path(info, total):
    """
    创建下载路径：
    """
    title = '[%d]%s' % (total, info['title'])
    title += ' @ %s' % (info['url'])
    # title += ' @ %s_%s' % (info['kw'], info['tid'])
    title = re.sub('[\\\/\:\*\?\|\"<>]', '_', title).encode('utf-8')
    # 在当前目录下创建文件夹
    print title
    path = os.getcwd()
    path = os.path.join(path,info['kw'])
    path = os.path.join(path,title)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def get_pic_json_url(pic_json_addr_s, info):
    return pic_json_addr_s + 'kw=%s&tid=%s' % (info['kw'], info['tid'])

def get_pic_json(json_url):
    json_string = requests.get(json_url).content
    json_info = json.loads(unicode(json_string, 'cp936'))
    json_info['url'] = json_url
    return json_info

def get_pic_json_full(json_url):
    json_info = get_pic_json(json_url)
    total = json_info['data']['pic_amount']
    index = 30
    for i in range(total/15+1):
        # print i
        # print json_info['data']['pic_list'][pos]['img']['medium']['id']
        try:
            # print index
            pos = '#%s' % index
            pid = json_info['data']['pic_list'][pos]['img']['medium']['id']
            new_json_url = json_url + '&pic_id=' + pid
            new_json_info = get_pic_json(new_json_url)
            json_info['data']['pic_list'] = dict(json_info['data']['pic_list'],
                                               **new_json_info['data']['pic_list'])
            index += 14
            # print new_json_url
        except Exception:
            break
    return json_info


def create_json(json_info, model=1):
    # print json.dumps(json_info, sort_keys=True, indent=4)
    if json_info['error'] != "sucess!":
        exit('json get error: %s\njson url: %s' % (json_info['error'], json_info['url']))
        return
    new_json = {}
    pic_list = []
    print 'json model: %d' % model
    if model:
        new_json['total'] = json_info['data']['total_num']
        for key, pic in enumerate(json_info['data']['pic_list']):
            pic_dict = {}
            pic_dict['descr'] = pic['descr']
            pic_dict['id'] = pic['pic_id']
            pic_dict['url'] = pic['purl'] if pic['purl'] else pic['murl']
            pic_dict['key'] = key+1
            pic_list.append(pic_dict)
    else:
        new_json['total'] = json_info['data']['pic_amount']
        if new_json['total'] == 0:
            pic_dict = {}
        else:
            for key, pic in json_info['data']['pic_list'].iteritems():
                pic_dict = {}
                pic_dict['descr'] = pic['descr']
                pic_url_list = pic['img']
                pic_dict['id'] = pic_url_list['medium']['id']
                pic_dict['url'] = pic_url_list['original']['waterurl'] \
                            if pic_url_list['original']['waterurl'] else pic_url_list['screen']['waterurl'] \
                            if pic_url_list['screen']['waterurl'] else pic_url_list['medium']['url']
                pic_dict['key'] = int(key[1:])
                pic_list.append(pic_dict)
    new_json['error'] = json_info['error']
    new_json['url'] = json_info['url']
    new_json['list'] = pic_list
    return new_json


def download_pic(json_info, pic_url_s, info, show_descr):
    # print json.dumps(json_info,sort_keys=True,indent=4)
    total_num = json_info['total']
    if total_num:
        path = get_download_path(info, total_num)
        print 'picture amount: %s' % total_num
        print 'download start:'
        num = 1
        download_error = 0
        for pic in json_info['list']:
            pic_descr = pic['descr'].encode('utf-8')
            pic_url = pic['url']
            index = pic['key']
            pic_url = pic_url_s + pic_url.split('/')[-1]
            pic_ext = pic_url.split('.')[-1]
            try:
                file_name = '[%03d]%s.%s' % (index, pic_descr, pic_ext) if show_descr else '%03d.%s' % (index, pic_ext)
                file_name = re.sub('[\\\/\:\*\?\|\"<>]', '_', file_name)
                file_path = os.path.join(path,file_name)
                if not os.path.exists(file_path):
                    print '%03d.download %d%% : %s' % (num, num * 100 / total_num, file_name)
                    fpic = requests.get(pic_url).content
                    with open(file_path, 'wb') as f:
                        f.write(fpic)
                    global pub_count
                    pub_count += 1
                else:
                    print '%03d.download %d%% : File already exists! Ignore.' % (num, num * 100 / total_num)

            except Exception,e:
                print '\n----------\n\ndownload failed! \n URL: %s\n Error: %s\n\n----------\n' % (pic_url, e)
                download_error += 1
            num += 1
    else:
        print 'picture not found!'
    print 'download complete!\n\tsuccessful : %d\n\tfailed : %d\n' % (total_num-download_error, download_error)
    global pub_total
    global pub_error
    pub_total += total_num
    pub_error += download_error

def run(url, show_descr):
    '''
    运行
    @arg    url: 百度贴吧帖子链接
    @return 下载图片到【./tieba/】
    PS：只能下载楼主所发图片。
    '''
    # # json_1 # 
    # model 1
    # 贴吧图册基本都是通过这个链接获取，效果良好
    # 可以获得缩略图的链接[json][因为json_2链接显示不全，所以改用这个链接，能获取到图片ID就好]
    # + 'kw = %s & tid = %s'  pe为要获得的图片数量
    pic_json_url_s1 = 'http://tieba.baidu.com/photo/g/bw/picture/list?alt=jview&rn=200&pn=1&ps=1&pe=999999&'

    # # json_2 # 
    # model 0
    # 可以获得缩略图的链接[json][只能获取部分图片]
    # + 'kw = %s & tid = %s & pic_id = %s &see_lz=0'
    pic_json_url_s2 = 'http://tieba.baidu.com/photo/bw/picture/guide?from_page=0&alt=jview&next=15&prev=15&see_lz=0&'

    # 此链接可以通过ID直接获取到原图
    # + pic_id
    pic_url_s = 'http://imgsrc.baidu.com/forum/pic/item/'
    try:
        print 'getting infomation, please waiting...'
        info = get_info(url)
        # 获取json链接
        pic_json_url = get_pic_json_url(pic_json_url_s1, info)
        # 获取json信息
        pic_json = get_pic_json(pic_json_url)

        if pic_json['error'] != "success!":
            # 普通帖子只能通过以下方式获得json
            # 获取json链接
            pic_json_url = get_pic_json_url(pic_json_url_s2, info)
            # 获取json信息
            pic_json = get_pic_json_full(pic_json_url)
            # print json.dumps(pic_json, sort_keys=True, indent=4)
            # exit()
            # 格式化为通用json
            pic_json = create_json(pic_json, 0)
        else:
            # 格式化为通用json
            pic_json = create_json(pic_json)

        print 'get successfully!'
        download_pic(pic_json, pic_url_s, info, show_descr)
    except Exception, e:
        print e

def get_tieba_pic(urls, show_descr=True):
    try:
        start = time.clock()
        global pub_count
        global pub_total
        global pub_error
        pub_count = 0
        pub_total = 0
        pub_error = 0
        thread_list = [Thread(target=run, args=(url, show_descr)) for url in urls]
        for t in thread_list:
            t.start()
        for t in thread_list:
            t.join()
    except requests.exceptions.ConnectionError, e:
        print('Network connect failed!\n\tError: %s' % e)
    except BaseException, e:
        print('Download failed!\nError: %s' % e)
    finally:
        runtime = time.clock() - start
        print('\n-------------\nrun time: %dmin %dsec\ntotal: %d\ndownload: %d\nerror: %d' %
              (runtime // 60, runtime % 60, pub_total, pub_count, pub_error))
        os.system('pause')
        
if __name__ == '__main__':
    urls = [
        # '2815006867',
        # '3527150891',
        # '3828722569',
        # '3580538474',
        # '3209143081',
        # '3736537369',
        # '3783256214',
        # '3560473182',
        # '2520397699',
        # '3682297933',
        # '2129002724',
        # '3782641122',
        # '3783028294',
        # '3828621260',
        # '3191126828',
        # '3307598167',
        # '3527150891',

        # '3789151741',
        # '3191028878',
        # '3377735261',
        # '3752868261',

        'http://tieba.baidu.com/p/2522915602'
    ]
    get_tieba_pic(urls)



# json_1 
# 'http://tieba.baidu.com/photo/g/bw/picture/list?alt=jview&rn=200&pn=1&ps=1&pe=1&' # + 'kw = %s & tid = %s'  pe为要获得的图片数量
# return:
"""
{
    "data": {
        "cur_page": 1, 
        "page_size": 200, 
        "pe": "2", 
        "pic_list": [
            {
                "crop_height": 0, 
                "crop_width": 0, 
                "descr": "20150405224040", 
                "height": 541, 
                "index": 0, 
                "mheight": 200, 
                "mleft": 0, 
                "mtop": 0, 
                "murl": "http://imgsrc.baidu.com/forum/wh%3D224%2C200/sign=0292b1a5d4160924dc70aa19e63319c8/b0c88012c8fcc3ce77921fc09645d688d63f20c8.jpg", 
                "mwidth": 224, 
                "mwrapper_height": 200, 
                "mwrapper_width": 224, 
                "pheight": 357, 
                "pic_id": "b0c88012c8fcc3ce77921fc09645d688d63f20c8", 
                "purl": "http://imgsrc.baidu.com/forum/w%3D399/sign=9ab2400f78d98d1076d40a38183eb807/b0c88012c8fcc3ce77921fc09645d688d63f20c8.jpg", 
                "pwidth": 399, 
                "pwrapper_height": 357, 
                "pwrapper_width": 400, 
                "width": 608
            }, 
            {
                "crop_height": 0, 
                "crop_width": 748, 
                "descr": "kv140513a", 
                "height": 330, 
                "index": 1, 
                "mheight": 200, 
                "mleft": 232, 
                "mtop": 0, 
                "murl": "http://imgsrc.baidu.com/forum/h%3D200%3Bcrop%3D13%2C0%2C748%2C200/sign=75b26a7248ed2e73e3e9812cb73ac2f9/fda33b087bf40ad121114215552c11dfabecceac.jpg", 
                "mwidth": 775, 
                "mwrapper_height": 200, 
                "mwrapper_width": 748, 
                "pheight": 259, 
                "pic_id": "fda33b087bf40ad121114215552c11dfabecceac", 
                "purl": "http://imgsrc.baidu.com/forum/h%3D259%3Bcrop%3D18%2C0%2C968%2C259/sign=b11be7ea13dfa9ece22e51125beb9471/fda33b087bf40ad121114215552c11dfabecceac.jpg", 
                "pwidth": 968, 
                "pwrapper_height": 259, 
                "pwrapper_width": 972, 
                "width": 1280
            }
        ], 
        "ps": "1", 
        "total_num": 937, 
        "total_page": 5, 
        "wall_height": 208, 
        "wall_type": "h"
    }, 
    "error": "sucess!", 
    "no": 0
}
"""


# json_2 
# 'http://tieba.baidu.com/photo/bw/picture/guide?from_page=0&alt=jview&next=15&prev=15&see_lz=0&' # + 'kw=%s&tid=%s&pic_id=%s'
# return:
# 因为信息中某些图的大图没显示链接，所以换这个链接通过id直接拿：http://imgsrc.baidu.com/forum/pic/item/ + id + .jpg
"""
{
    "no":0,
    "error":"sucess!",
    "data":{
        "pic_amount":69,
        "pic_list":{
            "#1":{
                "img":{
                    "original":{
                        "id":"ee00853eb13533fa1e49791fadd3fd1f40345b59",
                        "width":"580",
                        "height":"1031",
                        "size":"88329",
                        "format":"1",
                        "waterurl":"http://imgsrc.baidu.com/forum/pic/item/ee00853eb13533fa1e49791fadd3fd1f40345b59.jpg"
                    },
                    "medium":{
                        "id":"ee00853eb13533fa1e49791fadd3fd1f40345b59",
                        "url":"http://imgsrc.baidu.com/forum/w%3D194/sign=9ff984b4ccea15ce41eee40082013a25/ee00853eb13533fa1e49791fadd3fd1f40345b59.jpg",
                        "width":194,
                        "height":344,
                        "size":0,
                        "format":"1"
                    },
                    "screen":{
                        "id":"ee00853eb13533fa1e49791fadd3fd1f40345b59",
                        "width":432,
                        "height":768,
                        "size":0,
                        "format":"1",
                        "waterurl":"http://imgsrc.baidu.com/forum/wh%3D1024%2C768/sign=ef4f76763c12b31bc739c528b62a0256/ee00853eb13533fa1e49791fadd3fd1f40345b59.jpg"
                    }
                },
                "descr":"5b7717dda3cc7cd91c77b4143d01213fba0e91fa",
                "src_url":"",
                "src_text":"",
                "pic_type":null,
                "post_id":"0"
            }
        },
        "has_sep":0
    }
}
"""
