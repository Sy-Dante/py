#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""微博数据库操作"""
from __future__ import absolute_import, division, print_function, unicode_literals
import os
import sqlite3

class WeiboDB(object):
    """微博数据库操作"""

    def __init__(self):
        """初始化微博数据库"""
        db_dir = 'data'
        if not os.path.exists(db_dir):
            os.mkdir(db_dir)
        self.conn = sqlite3.connect(os.path.join(db_dir, 'weibo.db'))
        self.cursor = self.conn.cursor()
        self._creatTable()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.exit()

    def _creatTable(self):
        """创建数据表"""
        create_sql = '''CREATE table if not exists weibo(
                            nickname varchar(20),
                            weibo_id int PRIMARY KEY,
                            download int default 1
                        )'''
        self.cursor.execute(create_sql)

    def select(self, *arg):
        """默认查询download=1的数据

        Return:
            a dict {nickname: weibo_id}
        """
        data = arg if arg else (1,)
        sql = 'SELECT nickname, weibo_id from weibo where download in (%s)' % \
                ','.join(['?' for x in data])
        # print(sql)
        self.cursor.execute(sql, data)
        results = self.cursor.fetchall()
        return {key: val for key, val in results}

    def insert(self, urls):
        """插入或更新数据

        Args:
            urls:
                array 数据结构 [(nickname, weibo_id, download),]
                or
                dict 数据结构 {nickname: weibo_id,}
                             download default 1

        Return:
            影响行数
        """
        if type(urls) == dict:
            urls = [(nick, wbid, 1) for nick, wbid in urls.iteritems()]
        format_sql = lambda urls : ' union '.join([
                             "SELECT ? as nickname, ? as weibo_id, ? as download"
                             for x in urls])
        sql = 'INSERT OR REPLACE into weibo(nickname, weibo_id, download) %s' % format_sql(urls)
        data = [v for tup in urls for v in tup]
        self.cursor.execute(sql, data)
        return self.cursor.rowcount

    def getAll(self):
        """获取全部数据"""
        self.cursor.execute('SELECT nickname, weibo_id, download from weibo order by download desc')
        return self.cursor.fetchall()

    def delete(self, wbid):
        """删除数据
        
        Args:
            wbid: array 要删除的weibo_id列表
        """
        sql = 'DELETE from weibo where weibo_id in (%s)' % ','.join(['?' for x in wbid])
        self.cursor.execute(sql, wbid)
        return self.cursor.rowcount

    def commit(self):
        """提交更改"""
        self.conn.commit()

    def exit(self):
        """提交更改并退出"""
        self.commit()
        self.cursor.close()
        self.conn.close()

if __name__ == '__main__':
    import json
    with WeiboDB() as db:
        # db.insert({
        #             'fans[小四]-塞纳河': 5473551372, # 600+ 大图
        #             'fans[发卡]-山里人': 1533507090, # 1600+ 大图
        #             'fans[小菊]-Wils': 1244586691, # 3300+ 大图
        #             'fans[阿黄]-Sy_桃': 2195845005, # 150+ 小图
        #             'fans[小菊]-LY': 2252395501, # 600+ 小图
        #             'fans[朵朵]-115': 2962312110, # 750+ -- 小图
        #             })
        print(json.dumps(db.select(), indent=4))


    #     db.insert({
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