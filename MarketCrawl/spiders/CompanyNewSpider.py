#!/usr/bin/env python
# encoding: utf-8

'''
@author: panhongfa
@license: (C) Copyright 2017-2020, Node Supply Chain Manager Corporation Limited.
@contact: panhongfas@163.com
@software: PyCharm
@file: CompanyNewSpider.py
@time: 2018/8/10 14:52
@desc: 公司新闻爬虫, 需要根据股票代码构造url分页查询
@format: {count: 10, page: 1, list: {[symbol_id: ..., description: ...]}, maxPage: N}
'''

from scrapy.spiders import Spider
from scrapy.http import Request
from scrapy.http import Response
from scrapy import signals
from collections import OrderedDict
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

class CompanyNewSpider(Spider):
    name = 'CompanyNewSpider'
    allowed_domains = ['xueqiu.com', ]
    start_urls = ['https://xueqiu.com/', 'https://xueqiu.com/statuses/stock_timeline.json']
    custom_settings = {
        'DOWNLOAD_DELAY': 0.3,
        'LOG_FILE': './log/{}'.format(__name__)
    }

    # 定义如下的http返回码是爬取过程中正常的，可预期的
    website_possible_httpstatus_list = []

    def __init__(self, db, mode='all'):
        self.db_connect = db
        # mode参数含义 all: 全量数据爬取; period: 只爬取周期内的数据; newest: 只爬取最新的数据
        self.mode = mode
        # 周期定义为3个月
        self.period = (3600 * 24 * 30) * 3
        # 开始爬取的utc时间
        self.cur_utc = self.current_utc_time(ty='ms')

        self.share_codes = []
        self.last_news = {}

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

    def fetch_all_shares(self, connect):
        assert isinstance(connect, Connection)
        cursor = connect.cursor()

        sql = """SELECT shares_code, shares_type, shares_name FROM crawler_basic_index 
         WHERE shares_type IS NOT NULL GROUP BY shares_code ORDER BY shares_code ASC"""

        # 同步执行sql查询指令
        assert isinstance(cursor, Cursor)
        cursor.execute(sql)
        connect.commit()

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

    def fetch_last_news_info(self, connect):
        assert isinstance(connect, Connection)
        cursor = connect.cursor()

        sql = '''SELECT shares_code, MAX(news_id), MAX(date) 
        FROM crawler_company_news GROUP BY shares_code'''

        # 同步执行sql查询指令
        assert isinstance(cursor, Cursor)
        cursor.execute(sql)
        connect.commit()

        # 获取查询结果集
        result = cursor.fetchall()
        for feild in result:
            assert isinstance(feild, tuple)
            share = {
                'code': feild[0],
                'news_id': feild[1],
                'news_utc': self.bj_to_utc(feild[2], ty='ms', fm='%Y-%m-%d %H:%M'),
            }

            self.last_news[feild[0]] = share

    def spider_opened(self, spider):
        assert isinstance(spider, Spider)
        self.logger.info('###############################%s Start###################################', spider.name)

        if self.db_connect is not None:
            self.fetch_all_shares(self.db_connect)
            self.fetch_last_news_info(self.db_connect)
        else:
            raise RuntimeError('db_connect is None')

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
    def utc_to_bj(utc, ty='s', fm='%Y-%m-%d %H:%M:%S'):
        # 时区设置为东八区
        tz = pytz.timezone('Asia/Shanghai')

        # 判断是毫秒还是秒
        if ty is not None and ty.upper() == 'S':
            str_bj = datetime.datetime.fromtimestamp(utc, tz).strftime(fm)
        elif ty is not None and ty.upper() == 'MS':
            str_bj = datetime.datetime.fromtimestamp(utc / 1000, tz).strftime(fm)
        else:
            str_bj = ''
        return str_bj

    @staticmethod
    def bj_to_utc(str, ty='s', fm='%Y-%m-%d %H:%M:%S'):
        # 时区设置为东八区
        tz = pytz.timezone('Asia/Shanghai')

        # 判断是毫秒还是秒
        if ty is not None and ty.upper() == 'S':
            bj_dt = datetime.datetime.strptime(str, fm)
            bj_dt.replace(tzinfo=pytz.utc).astimezone(tz)
            utc = int(time.mktime(bj_dt.timetuple()))
        elif ty is not None and ty.upper() == 'MS':
            bj_dt = datetime.datetime.strptime(str, fm)
            bj_dt.replace(tzinfo=pytz.utc).astimezone(tz)
            utc = int(time.mktime(bj_dt.timetuple()) * 1000)
        else:
            utc = 0
        return utc

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
        self.logger.info('home_page_url=%s', home_page_url)

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

        # ‘新闻’的UTF-8编码，表示查询的是新闻
        param_list['source'] = '自选股新闻'

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
        self.logger.info('begin_url=%s', begin_url)

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

    def parse_json_data(self, json_obj, share_index):
        item_list = []
        page_data = json_obj['list']

        min_create_utc = sys.maxint * 10000
        max_create_utc = 0
        for unit in page_data:
            item = CompanyNewItem()
            item['symbol'] = self.share_codes[share_index]['code']
            item['name'] = self.share_codes[share_index]['name']

            item['news_title'] = unit['title']
            desc_text = unit['description']
            desc_list = re.split(u'(<a.+/a>)', desc_text)
            if len(desc_list) >= 2:
                item['news_text'] = desc_list[0]

                desc_obj = etree.HTML(desc_list[1])
                hrefs = desc_obj.xpath(u'//a')
                for href in hrefs:
                    item['news_url'] = href.attrib['href']

            else:
                item['news_text'] = desc_text
                item['news_url'] = ''

            # 转换为北京时间
            create_utc = string.atoi(str(unit['created_at']))
            item['date'] = self.utc_to_bj(create_utc, ty='ms', fm='%Y-%m-%d %H:%M')

            if min_create_utc > create_utc:
                min_create_utc = create_utc

            if max_create_utc < create_utc:
                max_create_utc = create_utc

            # 获取新闻的ID
            news_id = string.atoi(str(unit['id']))
            item['news_id'] = news_id

            item_list.append(item)

        return item_list, min_create_utc, max_create_utc

    def post_next_share(self, share_index, share_total, page_size, response):
        share_index += 1

        # 首先更换code
        next_url = re.sub('symbol_id=\w+', 'symbol_id={}'.format(self.encode_share_prefix(share_index)), response.url)

        # 然后更换page，初始值设置为1
        next_url = re.sub('page=\d+', 'page={}'.format(1), next_url)
        self.logger.info('next_url=%s', next_url)

        request = Request(
            url=next_url,
            callback=self.parse_page_data,
            meta={
                'page_index': 1,
                'page_size': page_size,
                'share_index': share_index,
                'share_total': share_total,
            }
        )
        return request

    def post_next_page(self, share_index, share_total, page_index, page_size, response):
        page_index += 1

        # 直接更换page
        next_url = re.sub('page=\d+', 'page={}'.format(page_index), response.url)
        self.logger.info('next_url=%s', next_url)

        request = Request(
            url=next_url,
            callback=self.parse_page_data,
            meta={
                'page_index': page_index,
                'page_size': page_size,
                'share_index': share_index,
                'share_total': share_total,
            }
        )
        return request

    def is_exceed_bound(self, min_create, max_create, code=None):
        dead_create = self.cur_utc - self.period * 1000
        # 按给定周期爬取模式
        if code is None:
            if min_create > dead_create:
                return False  # 最小时间都比截止时间大，表示还需要继续爬取下一个页面
            else:
                return True  # 最小时间已经比截止时间小，表示已经爬取完区间内的数据，不需要爬取下一页面

        # 只爬取最新数据模式
        else:
            if code in self.last_news and self.last_news[code]:
                last_create = self.last_news[code]['news_utc']
            else:
                last_create = dead_create

            if self.cur_utc <= last_create:
                return True  # 启动时间与最后更新时间相等，则每只股票取第一页数据即可
            elif min_create > last_create:
                return False  # 最小时间都比最近更新时间大，表示还需要继续爬取下一个页面
            else:
                return True  # 最小时间已经比最近更新时间小，表示已经爬取完更新的数据，不需要爬取下一页面

    def is_page_done(self, page_index, page_total):
        if page_index < page_total:
            return False
        else:
            return True

    def is_share_done(self, share_index, share_total):
        if share_index < share_total - 1:
            return False
        else:
            return True

    def parse_page_data(self, response):
        assert isinstance(response, Response)
        share_total = response.meta['share_total']
        share_index = response.meta['share_index']

        try:
            json_obj = demjson.decode(str(response.body).decode('utf-8'))

        # 获取到返回的页面，但是数据不是json格式，表示触发了反爬的图形验证码，此时强制切换代理IP
        except Exception:
            req = response.request
            req.meta["change_proxy"] = True
            req.dont_filter = True
            yield req
        else:
            page_index = json_obj['page']
            page_total = json_obj['maxPage']
            page_size = json_obj['count']

            min_create = max_create = 0
            self.logger.info('share_total=%s, share_index=%s, page_total=%s, page_index=%s, page_size=%s',
                             share_total, share_index, page_total, page_index, page_size)

            if 'list' in json_obj and len(json_obj['list']) > 0:
                # 解析页面中的json数据
                items, min_create, max_create = self.parse_json_data(json_obj, share_index)
                for item in items:
                    yield item
            else:
                self.logger.info('page data is empty')

            cur_code = self.share_codes[share_index]['code']
            cur_name = self.share_codes[share_index]['name']

            # 如果是全量爬取
            if self.mode is not None and self.mode.upper() == 'ALL':
                if not self.is_share_done(share_index, share_total):
                    if not self.is_page_done(page_index, page_total):
                        yield self.post_next_page(share_index, share_total, page_index, page_size, response)
                    else:
                        self.logger.info('share_total=%s, share_index=%s, share_code=%s, share_name=%s is finished',
                                         share_total, share_index, cur_code, cur_name)
                        yield self.post_next_share(share_index, share_total, page_size, response)
                else:
                    self.logger.info('{} is finished'.format(self.name))

            # 如果是爬取周期内的数据
            elif self.mode is not None and self.mode.upper() == 'PERIOD':
                if not self.is_share_done(share_index, share_total):
                    if not self.is_page_done(page_index, page_total):
                        if not self.is_exceed_bound(min_create, max_create):
                            yield self.post_next_page(share_index, share_total, page_index, page_size, response)
                        else:
                            self.logger.info('share_total=%s, share_index=%s, share_code=%s, share_name=%s is finished',
                                             share_total, share_index, cur_code, cur_name)
                            yield self.post_next_share(share_index, share_total, page_size, response)
                    else:
                        self.logger.info('share_total=%s, share_index=%s, share_code=%s, share_name=%s is finished',
                                         share_total, share_index, cur_code, cur_name)
                        yield self.post_next_share(share_index, share_total, page_size, response)
                else:
                    self.logger.info('{} is finished'.format(self.name))

            # 如果是增量爬取
            elif self.mode is not None and self.mode.upper() == 'NEWEST':
                if not self.is_share_done(share_index, share_total):
                    if not self.is_page_done(page_index, page_total):
                        if not self.is_exceed_bound(min_create, max_create, cur_code):
                            yield self.post_next_page(share_index, share_total, page_index, page_size, response)
                        else:
                            self.logger.info('share_total=%s, share_index=%s, share_code=%s, share_name=%s is finished',
                                             share_total, share_index, cur_code, cur_name)
                            yield self.post_next_share(share_index, share_total, page_size, response)
                    else:
                        self.logger.info('share_total=%s, share_index=%s, share_code=%s, share_name=%s is finished',
                                         share_total, share_index, cur_code, cur_name)
                        yield self.post_next_share(share_index, share_total, page_size, response)
                else:
                    self.logger.info('{} is finished'.format(self.name))
            else:
                raise RuntimeError('param mode is error')
