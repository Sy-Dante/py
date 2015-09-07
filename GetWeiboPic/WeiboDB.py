#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""微博数据库操作"""
from __future__ import absolute_import, division, print_function, unicode_literals
import os
import sqlite3

class WeiboDB(object):
    """微博数据库操作
    """

    def __init__(self):
        db_dir = 'data'
        if not os.path.exists(db_dir):
            os.mkdir(db_dir)
        self.conn = sqlite3.connect('data/weibo.db')
        self.cursor = self.conn.cursor()
        self._creatTable()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

    exit = __exit__

    def _creatTable(self):
        create_sql = '''CREATE table if not exists weibo(
                            nickname varchar(20),
                            weibo_id int PRIMARY KEY,
                            download int default 1
                        )'''
        self.cursor.execute(create_sql)

    def selectDict(self, *arg):
        """默认查询需下载数据

        Return:
            a dict {nickname: weibo_id}
        """
        arg = arg if arg else (1,)
        select_sql = 'SELECT nickname, weibo_id from weibo where download in (%s)' % \
                        ','.join([str(x) for x in arg])
        # print(select_sql)
        self.cursor.execute(select_sql)
        results = self.cursor.fetchall()
        return {key: val for key, val in results}

    def insertDict(self, urls, download=1):
        """插入或更新数据

        Args:
            urls: a dict 数据信息 {nickname: weibo_id}
            download: default 1 是否下载
                0 不下载
                1 下载
                2 其他

        Return:
            影响行数
        """
        data = lambda urls, down : ' union '.join([
                     'SELECT \'%s\' as \'nickname\', %s as \'weibo_id\', %s as \'download\'' %
                     (key, val, down) for key, val in urls.iteritems()])
        self.cursor.execute('INSERT OR REPLACE into weibo(nickname, weibo_id, download) %s' % data(urls, download))
        return self.cursor.rowcount

    # def updateDict(self, urls, download=1):
    #     for nickname, weibo_id in urls.iteritems():
    #         row = self.cursor.execute('UPDATE weibo set nickname=\'%s\', weibo_id=%s, download=%s where weibo_id=%s' %
    #                             (nickname, weibo_id, download, weibo_id))
    #         if row == 0:
    #             self.cursor.execute('INSERT OR IGNORE into weibo(nickname, weibo_id, download) values(\'%s\', %s, %s)' %
    #                                 (nickname, weibo_id, download))

if __name__ == '__main__':
    import json
    with WeiboDB() as db:
        # db.insertDict({'Ruri': 3669076064,})
        print(json.dumps(db.selectDict(), indent=4))


    #     db.insertDict({
    #         # # Team SⅡ
    #         # 'XiaoAi': 3050708243,
    #         # 'SiSi': 3050742117,
    #         # # Team NⅡ
    #         # 'Ruri': 3669076064,
    #         # 'Kiku': 3669102477,
    #         # # Team HⅡ
    #         # 'Sheep': 5228056212,
    #         # 'Monster': 5230466807,
    #         # 'LuBao': 5229864870,
    #         # 'WanQing': 5229579490,
    #         # 'Kuma-李清扬': 5231168847,
    #         # # Team X
    #         # 'Maruko': 5490958194,
    #         # 'CoCo': 5460952383,
    #         # 'RanRan': 5479678683,
    #         # 'WangShu': 5491330253,

    #         # # Team Fans
    #         # 'SoRuri': 5581868113,
    #         # 'fans[会长]-加菲': 2316839037, # 大图 撸力
    #         # 'fans[孟孟]-微凉': 1837085131, # 小图
    #         # # 400
    #         # 'fans[大哥]-芒果': 278332254, # 30+ ++ 大图
    #         # 'fans[小菊]-双子座': 2623190960, # 30+ ++ 大图
    #         # 'fans[小菊]-Eg': 3240835062, # 60+ ++ 大图
    #         # 'fans[阿黄]-zzh': 1889585464, # 160+ ++ 大图
    #         # 'fans[阿黄]-雪山': 1701598311, # 300+ ++ 大图
    #         # 'fans[小菊]-zxs': 1694575520, # 350+ ++ 大图

    #         # 'fans[小四]-塞纳河': 5473551372, # 600+ 大图
    #         # 'fans[发卡]-山里人': 1533507090, # 1600+ 大图
    #         # 'fans[小菊]-Wils': 1244586691, # 3300+ 大图
    #         # 'fans[阿黄]-Sy_桃': 2195845005, # 150+ 小图
    #         # 'fans[小菊]-LY': 2252395501, # 600+ 小图
    #         # 'fans[朵朵]-115': 2962312110, # 750+ -- 小图

    #         # Team Out
    #         # # '夏奈-杨吟雨': 5225561029,
    # })