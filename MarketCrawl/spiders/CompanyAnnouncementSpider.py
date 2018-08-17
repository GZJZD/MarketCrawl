#!/usr/bin/env python
# encoding: utf-8

'''
@author: panhongfa
@license: (C) Copyright 2017-2020, Node Supply Chain Manager Corporation Limited.
@contact: panhongfas@163.com
@software: PyCharm
@file: ShareBuybackSpider.py
@time: 2018/8/10 14:52
@desc: 公司公告爬虫, 需要根据股票代码构造url分页查询
@format: {count: 10, page: 1, list: {[symbol_id: ..., description: ...]}, maxPage: N}
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
from lxml import etree
import pymysql
import time
import demjson
import re
import random
import string
import pytz
import datetime
import sys

class CompanyAnnouncementSpider(Spider):
    name = 'CompanyAnnouncementSpider'
    allowed_domains = ['xueqiu.com', ]
    start_urls = ['https://xueqiu.com', 'https://xueqiu.com/statuses/stock_timeline.json']
    custom_settings = {
        'DOWNLOAD_DELAY': 0.1,
        'RETRY_TIMES': 5,
        'DOWNLOAD_TIMEOUT': 30
    }

    handle_httpstatus_list = [400]

    db_connect = None
    share_codes = []
    last_announce_id = {}
    partial_update = False

    def __init__(self, db, partial=False):
        self.db_connect = db
        self.partial_update = partial

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
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

        s = cls(db, *args, **kwargs)
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
            code_bound = ''
            result = cursor.fetchall()
            for feild in result:
                assert isinstance(feild, tuple)
                share = {
                    'code': feild[0],
                    'type': feild[1],
                    'name': feild[2],
                }
                self.share_codes.append(share)

                # 组织下一个查询的过滤条件
                code_bound += share['code']
                code_bound += ','

            code_bound = code_bound + 'NULL'
            sql = '''SELECT shares_code, MAX(announce_id) FROM crawler_company_announcement 
            WHERE shares_code IN ({}) GROUP BY shares_code'''.format(code_bound)

            cursor.execute(sql)
            self.db_connect.commit()

            result = cursor.fetchall()
            for feild in result:
                assert isinstance(feild, tuple)
                self.last_announce_id[feild[0]] = feild[1]

        else:
            raise RuntimeError('db_pool is None')

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
    def transfrom_beijing_time(time_m_second=int(time.time())):
        # 设置为东八区
        tz = pytz.timezone('Asia/Shanghai')

        # 将毫秒级的UTC时间转换成北京时间字符串，精确到分钟
        t = datetime.datetime.fromtimestamp(time_m_second / 1000, tz).strftime('%Y-%m-%d %H:%M')
        return t

    @staticmethod
    def current_milli_time():
        milli_time = lambda: int(round(time.time() * 1000))
        return milli_time()

    # 股票类型+股票代码构成KEY，1代表SH，表示上交所，2代表SZ，表示深交所
    def encode_share_prefix(self, index):
        if self.share_codes[index]['type'] == u'1':
            share_prefix = 'SH'
        elif self.share_codes[index]['type'] == u'2':
            share_prefix = 'SZ'
        else:
            raise RuntimeError('share_type is invalid')

        return share_prefix + self.share_codes[index]['code']

    def start_requests(self):
        home_page_url = self.start_urls[0]
        logger.info('home_page_url=%s', home_page_url)

        yield Request(
            url=home_page_url,
            callback=self.start_home_requests
        )

    def start_home_requests(self, response):
        # 爬取的主页数据不需要解析，只获取cache即可
        if len(self.share_codes) == 0:
            raise RuntimeError('share_codes is empty')

        # 默认的dict无序，遍历时不能保证安装插入顺序获取
        param_list = OrderedDict()

        # 股票类型+股票代码构成KEY，1代表SH，表示上交所，2代表SZ，表示深交所
        begin_index = 0
        param_list['symbol_id'] = self.encode_share_prefix(begin_index)

        # 每次请求的数据个数，最大只能是20
        param_list['count'] = 20

        # ‘公告’的UTF-8编码，表示查询的是公告
        param_list['source'] = '公告'

        # 当前页码
        param_list['page'] = 1

        # 组织查询参数
        query_param = ''
        for kv in param_list.items():
            if kv[0] is 'symbol_id':
                query_param += '?{0}={1}'.format(*kv)
            else:
                query_param += '&{0}={1}'.format(*kv)

        begin_url = self.start_urls[1] + query_param
        logger.info('begin_url=%s', begin_url)

        # yield请求
        yield Request(
            url=begin_url,
            callback=self.parse_page_data,
            meta={
                'page_index': param_list['page'],
                'page_size': param_list['count'],
                'share_index': begin_index,
                'share_total': len(self.share_codes),
            }
        )

    def parse_page_data(self, response):
        assert isinstance(response, Response)
        share_total = response.meta['share_total']
        share_index = response.meta['share_index']

        json_obj = demjson.decode(response.body)
        page_index = json_obj['page']
        page_total = json_obj['maxPage']
        page_size = json_obj['count']
        logger.info('share_total=%s, share_index=%s, page_total=%s, page_index=%s, page_size=%s',
                    share_total, share_index, page_total, page_index, page_size)

        min_announce_id = sys.maxint
        if 'list' in json_obj and len(json_obj['list']) > 0:
            page_data = json_obj['list']
            for unit in page_data:
                item = CompanyAnnouncementItem()
                item['symbol'] = self.share_codes[share_index]['code']
                item['name'] = self.share_codes[share_index]['name']

                item['announce_type'] = ''

                desc_text = unit['description']
                desc_list = re.split(u'(<a.+/a>)', desc_text)
                if len(desc_list) >= 2:
                    item['announce_title'] = desc_list[0]

                    desc_obj = etree.HTML(desc_list[1])
                    hrefs = desc_obj.xpath(u'//a')
                    for href in hrefs:
                        item['announce_url'] = href.attrib['href']

                else:
                    item['announce_title'] = desc_text
                    item['announce_url'] = ''

                # 转换为北京时间
                item['announce_date'] = self.transfrom_beijing_time(string.atoi(str(unit['created_at'])))

                # 获取公告的ID
                announce_id = string.atoi(str(unit['id']))
                item['announce_id'] = announce_id

                if min_announce_id > announce_id:
                    min_announce_id = announce_id

                yield item
        else:
            logger.info('page_data data is empty')

        cur_code = self.share_codes[share_index]['code']
        cur_name = self.share_codes[share_index]['name']

        if cur_code in self.last_announce_id:
            cur_last_announce_id = self.last_announce_id[cur_code]
        else:
            cur_last_announce_id = 0

        if page_total == page_index and share_index < share_total:
            logger.info('share_total=%s, share_index=%s, share_code=%s, share_name=%s is finished',
                        share_total, share_index, cur_code, cur_name)
            share_index += 1

            # 首先更换code
            next_url = re.sub('symbol_id=\w+', 'symbol_id={}'.format(self.encode_share_prefix(share_index)), response.url)

            # 然后更换page，初始值设置为1
            next_url = re.sub('page=\d+', 'page={}'.format(1), next_url)
            yield Request(
                url=next_url,
                callback=self.parse_page_data,
                meta={
                    'page_index': 1,
                    'page_size': page_size,
                    'share_index': share_index,
                    'share_total': len(self.share_codes),
                }
            )
            logger.info('next_url=%s', next_url)

        elif self.partial_update and min_announce_id < cur_last_announce_id:
            logger.info('share_total=%s, share_index=%s, share_code=%s, share_name=%s is partial update finished',
                        share_total, share_index, cur_code, cur_name)
            share_index += 1

            # 首先更换code
            next_url = re.sub('symbol_id=\w+', 'symbol_id={}'.format(self.encode_share_prefix(share_index)), response.url)

            # 然后更换page，初始值设置为1
            next_url = re.sub('page=\d+', 'page={}'.format(1), next_url)
            yield Request(
                url=next_url,
                callback=self.parse_page_data,
                meta={
                    'page_index': 1,
                    'page_size': page_size,
                    'share_index': share_index,
                    'share_total': len(self.share_codes),
                }
            )
            logger.info('next_url=%s', next_url)

        elif page_index < page_total and share_index < share_total:
            page_index += 1
            next_url = re.sub('page=\d+', 'page={}'.format(page_index), response.url)
            yield Request(
                url=next_url,
                callback=self.parse_page_data,
                meta={
                    'page_index': page_index,
                    'page_size': page_size,
                    'share_index': share_index,
                    'share_total': len(self.share_codes),
                }
            )
            logger.info('next_url=%s', next_url)
        else:
            logger.info('{} is finished'.format(self.name))
