#!/usr/bin/env python
# encoding: utf-8

'''
@author: panhongfa
@license: (C) Copyright 2017-2020, Node Supply Chain Manager Corporation Limited.
@contact: panhongfas@163.com
@software: PyCharm
@file: MainInfluxSpider.py
@time: 2018/8/10 14:52
@desc: 主力流入爬虫
@format: aff_data={data: [..., ...]}
'''

from scrapy.spiders import Spider
from scrapy.http import Request
from scrapy.http import Response
from scrapy import signals
from collections import OrderedDict
from MarketCrawl.logger import logger
from MarketCrawl.items import *
from pymysql.connections import Connection
from pymysql.cursors import Cursor
import pymysql
import time
import demjson
import re
import random
import string


class MainInfluxSpider(Spider):
    name = 'MainInfluxSpider'
    allowed_domains = ['ff.eastmoney.com', ]
    start_urls = ['http://ff.eastmoney.com//EM_CapitalFlowInterface/api/js']
    custom_settings = {
        'DOWNLOAD_DELAY': 0.2,
        'RETRY_TIMES': 5,
        'DOWNLOAD_TIMEOUT': 60
    }

    db_connect = None
    share_codes = []

    def __init__(self, db):
        self.db_connect = db

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        # 连接数据库
        db = pymysql.connect(
            host=crawler.settings["DATABASE_CONNECTION"]['MYSQL_HOST'],
            port=crawler.settings["DATABASE_CONNECTION"]['MYSQL_PORT'],
            user=crawler.settings["DATABASE_CONNECTION"]['MYSQL_USER'],
            passwd=crawler.settings["DATABASE_CONNECTION"]['MYSQL_PASSWORD'],
            db=crawler.settings["DATABASE_CONNECTION"]['MYSQL_DATABASE'],
            use_unicode=True,
            charset="utf8",
        )

        s = cls(db)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        s.set_crawler(crawler)

        return s

    def spider_opened(self, spider):
        assert isinstance(spider, Spider)
        logger.info('###############################%s Start###################################', spider.name)

        if self.db_connect is not None:
            assert isinstance(self.db_connect, Connection)
            cursor = self.db_connect.cursor()

            sql = """SELECT shares_code, shares_type, shares_name FROM crawler_basic_index 
            WHERE shares_type IS NOT NULL GROUP BY shares_code ORDER BY shares_code ASC"""

            # 同步执行sql查询指令
            assert isinstance(cursor, Cursor)
            cursor.execute(sql)
            self.db_connect.commit()

            # 获取查询结果集
            result = cursor.fetchall()
            for feild in result:
                assert isinstance(feild, tuple)
                share = {
                    'code': feild[0],
                    'type': feild[1],
                    'name': feild[2],
                }
                self.share_codes.append(share)

        else:
            raise RuntimeError('db_pool is None')

        print spider.crawler.stats

    def spider_closed(self, spider):
        assert isinstance(self.db_connect, Connection)
        self.db_connect.close()

        assert isinstance(spider, Spider)
        logger.info('###############################%s End#####################################', spider.name)

    @staticmethod
    # 生成一个指定长度的随机字符串
    def generate_random_prefix(length=8):
        str_list = [random.choice(string.digits + string.ascii_letters) for i in range(length)]
        random_str = ''.join(str_list)
        return random_str

    @staticmethod
    def current_milli_time():
        milli_time = lambda: int(round(time.time() * 1000))
        return milli_time()

    def start_requests(self):
        if len(self.share_codes) == 0:
            raise RuntimeError('share_codes is empty')

        # 默认的dict无序，遍历时不能保证安装插入顺序获取
        param_list = OrderedDict()

        # 初始赋值
        param_list['type'] = 'hff'
        param_list['rtntype'] = 2
        param_list['js'] = '{data:[(x)]}'
        param_list['cb'] = 'var%20aff_data='
        param_list['check'] = 'TMLBMSPROCR'
        param_list['acces_token'] = '1942f5da9b46b069953c873404aad4b5'

        begin_index = 0
        param_list['id'] = self.share_codes[begin_index]['code'] + self.share_codes[begin_index]['type']
        param_list['_'] = self.current_milli_time()

        # 组织查询参数
        query_param = ''
        for kv in param_list.items():
            if kv[0] is 'type':
                query_param += '?{0}={1}'.format(*kv)
            else:
                query_param += '&{0}={1}'.format(*kv)

        begin_url = self.start_urls[0] + query_param
        logger.info('begin_url=%s', begin_url)

        yield Request(
            url=begin_url,
            meta={'page_index': begin_index, 'page_total': len(self.share_codes)}
        )

    def parse(self, response):
        assert isinstance(response, Response)

        page_total = response.meta['page_total']
        page_index = response.meta['page_index']
        logger.info('page_total=%s, page_index=%s, share_code=%s, share_name=%s',page_total, page_index,
                    self.share_codes[page_index]['code'], self.share_codes[page_index]['name'])

        # 去除头部的'=', 得到json格式的文本
        body_list = re.split('^[^=]*(=+)', str(response.body))
        json_text = body_list[2]

        # 解析pagedata的JSON数据体，构造并填充item对象后返回
        json_obj = demjson.decode(json_text)
        if 'data' in json_obj and len(json_obj['data']) > 0:
            page_data = json_obj['data'][0]

            for unit_text in page_data:
                assert isinstance(unit_text, unicode)
                unit = unit_text.split(u',')

                item = MainInfluxItem()
                item['symbol'] = self.share_codes[page_index]['code']
                item['name'] = self.share_codes[page_index]['name']
                item['last_update_time'] = unit[0]
                item['main_influx_price'] = unit[1]
                item['main_influx_ratio'] = unit[2]
                item['huge_influx_price'] = unit[3]
                item['huge_influx_ratio'] = unit[4]
                item['large_influx_price'] = unit[5]
                item['large_influx_ratio'] = unit[6]
                item['middle_influx_price'] = unit[7]
                item['middle_influx_ratio'] = unit[8]
                item['small_influx_price'] = unit[9]
                item['small_influx_ratio'] = unit[10]

                yield item
        else:
            logger.info('page_data data is empty')

        # 更新下一个待爬取的url后返回
        if page_index < page_total:
            # 更新下一支股票由code+type组成的key
            page_index += 1
            next_share_key = self.share_codes[page_index]['code'] + self.share_codes[page_index]['type']
            next_url = re.sub('id=\w+', 'id={}'.format(next_share_key), response.url)
            yield Request(
                url=next_url,
                meta={'page_index': page_index, 'page_total': page_total}
            )
            logger.info('next_url=%s', next_url)
        else:
            logger.info('{} is finished'.format(self.name))
