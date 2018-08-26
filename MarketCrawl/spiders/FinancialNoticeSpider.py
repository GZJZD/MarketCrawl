#!/usr/bin/env python
# encoding: utf-8

'''
@author: panhongfa
@license: (C) Copyright 2017-2020, Node Supply Chain Manager Corporation Limited.
@contact: panhongfas@163.com
@software: PyCharm
@file: MainInfluxSpider.py
@time: 2018/8/10 14:52
@desc: 财报披露爬虫
@format: html
'''

from scrapy.spiders import Spider
from scrapy.http import Request
from scrapy.http import Response
from scrapy import signals
from scrapy.selector import Selector
from MarketCrawl.items import *
from pymysql.connections import Connection
from pymysql.cursors import Cursor
import pymysql
import time
import re
import random
import string

class FinancialNoticeSpider(Spider):
    name = 'FinancialNoticeSpider'
    allowed_domains = ['data.eastmoney.com', ]
    start_urls = ['http://data.eastmoney.com/bbsj/']
    custom_settings = {
        'DOWNLOAD_DELAY': 0.1,
        'LOG_FILE': './log/{}'.format(__name__)
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
        self.logger.info('###############################%s Start###################################', spider.name)

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

    def spider_closed(self, spider):
        assert isinstance(self.db_connect, Connection)
        self.db_connect.close()

        assert isinstance(spider, Spider)
        self.logger.info('###############################%s End#####################################', spider.name)

    @staticmethod
    # 生成一个指定长度的随机字符串
    def generate_random_prefix(length=8):
        str_list = [random.choice(string.digits + string.ascii_letters) for i in range(length)]
        random_str = ''.join(str_list)
        return random_str

    @staticmethod
    def current_utc_time(ty='s'):
        milli_time = lambda: int(round(time.time()))

        if ty is not None and ty.upper() == 'S':
            mt = milli_time()
        elif ty is not None and ty.upper() == 'MS':
            mt = milli_time() * 1000
        else:
            mt = milli_time()
        return mt

    def start_requests(self):
        if len(self.share_codes) == 0:
            raise RuntimeError('share_codes is empty')

        # 组织查询参数
        begin_index = 0
        query_param = self.share_codes[begin_index]['code']
        query_param += '.html'

        begin_url = self.start_urls[0] + query_param
        self.logger.info('begin_url=%s', begin_url)

        yield Request(
            url=begin_url,
            meta={'share_index': begin_index, 'share_total': len(self.share_codes)}
        )

    def parse(self, response):
        assert isinstance(response, Response)
        share_total = response.meta['share_total']
        share_index = response.meta['share_index']
        self.logger.info('share_total=%s, share_index=%s, share_code=%s, share_name=%s', share_total, share_index,
                    self.share_codes[share_index]['code'], self.share_codes[share_index]['name'])

        page = Selector(response)

        # 匹配到table2下head中的所有列, 并且判断列数是否与item字段数量匹配
        table_head = page.xpath('//*[@id="Table2"]/thead/tr/th')
        if len(table_head) != 8:
            raise RuntimeError('table format is changed')

        # 匹配到table2下的所有行
        table_body = page.xpath('//*[@id="Table2"]/tbody/tr')

        for i in range(len(table_body)):
            item = FinancialNoticeItem()
            item['symbol'] = self.share_codes[share_index]['code']
            item['name'] = self.share_codes[share_index]['name']

            # 业绩变动内容
            path = '//*[@id="Table2"]/tbody/tr[{}]/td[2]/span/text()'.format(i+1)
            item['forecast_content'] = page.xpath(path).extract()

            # 预计净利润
            path = '//*[@id="Table2"]/tbody/tr[{}]/td[3]/text()'.format(i+1)
            item['forecast_left'] = page.xpath(path).extract()

            # 业绩变动幅度
            path = '//*[@id="Table2"]/tbody/tr[{}]/td[4]/span/text()'.format(i+1)
            increase_left_list = page.xpath(path).extract()
            if len(increase_left_list) == 1:
                item['increase_left'] = increase_left_list[0]
            elif len(increase_left_list) == 2:
                item['increase_left'] = increase_left_list[0]
                item['increase_left'] = '~'
                item['increase_left'] = increase_left_list[1]
            else:
                item['increase_left'] = ''

            # 过期字段，占位用
            item['forecast_right'] = ''
            item['increase_right'] = ''

            # 业绩变动原因
            path = '//*[@id="Table2"]/tbody/tr[{}]/td[5]/text()'.format(i+1)
            item['change_reason'] = page.xpath(path).extract()

            # 预告类型
            path = '//*[@id="Table2"]/tbody/tr[{}]/td[6]/span/text()'.format(i + 1)
            item['preview_type'] = page.xpath(path).extract()

            # 上年同期净利润
            path = '//*[@id="Table2"]/tbody/tr[{}]/td[7]/span/text()'.format(i + 1)
            item['previous_year_profit'] = page.xpath(path).extract()

            # 公告日期
            path = '//*[@id="Table2"]/tbody/tr[{}]/td[8]/span/text()'.format(i + 1)
            item['announcement_date'] = page.xpath(path).extract()

            # 过滤掉那些没有业绩变动的内容
            if len(item['announcement_date']):
                yield item

        # 更新下一个待爬取的url后返回
        if not self.is_share_done(share_index, share_total):
            yield self.post_next_share(share_index, share_total, response)
        else:
            self.logger.info('{} is finished'.format(self.name))

    def post_next_share(self, share_index, share_total, response):
        share_index += 1

        # 更换code
        next_url = re.sub('\d+', '{}'.format(self.share_codes[share_index]['code']), response.url)
        self.logger.info('next_url=%s', next_url)

        request = Request(
            url=next_url,
            meta={'share_index': share_index, 'share_total':share_total}
        )
        return request

    def is_share_done(self, share_index, share_total):
        if share_index < share_total - 1:
            return False
        else:
            return True
