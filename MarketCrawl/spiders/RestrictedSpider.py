#!/usr/bin/env python
# encoding: utf-8

'''
@author: panhongfa
@license: (C) Copyright 2017-2020, Node Supply Chain Manager Corporation Limited.
@contact: panhongfas@163.com
@software: PyCharm
@file: ShareBuybackSpider.py
@time: 2018/8/10 14:52
@desc: 股权限售解禁爬虫, JS接口支持全量查询，可不需要按照code进行分页查询
@format: var xxxx={pages: N, data: ['...', '...'], url: ...}
'''

from scrapy.spiders import Spider
from scrapy.http import Request
from scrapy.http import Response
from scrapy import signals
from collections import OrderedDict
from MarketCrawl.items import *
import time
import pytz
import datetime
import demjson
import re
import random
import string

class RestrictedSpider(Spider):
    name = 'RestrictedSpider'
    allowed_domains = ['dcfm.eastmoney.com',]
    start_urls = ['http://dcfm.eastmoney.com/em_mutisvcexpandinterface/api/js/get']

    custom_settings = {
        'LOG_FILE': './log/{}'.format(__name__)
    }

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        s.set_crawler(crawler)

        return s

    def spider_opened(self, spider):
        assert isinstance(spider, Spider)
        self.logger.info('###############################%s Start###################################', spider.name)

    def spider_closed(self, spider):
        assert isinstance(spider, Spider)
        self.logger.info('###############################%s End#####################################', spider.name)

    @staticmethod
    # 生成一个指定长度的随机字符串
    def generate_random_prefix(length=8):
        str_list = [random.choice(string.digits + string.ascii_letters) for i in range(length)]
        random_str = ''.join(str_list)
        return random_str

    @staticmethod
    def transfrom_beijing_time(time_second=int(time.time())):
        # 设置为东八区
        tz = pytz.timezone('Asia/Shanghai')
        t = datetime.datetime.fromtimestamp(time_second / 1000, tz).strftime('%Y-%m-%d %H:%M:%S')
        return t

    @staticmethod
    def is_float_string(float_number):
        value = re.compile(r'^[-+]?[0-9]+\.[0-9]+$')
        result = value.match(float_number)
        if result:
            return True
        else:
            return False

    @staticmethod
    def current_milli_time():
        milli_time = lambda: int(round(time.time() * 1000))
        return milli_time()

    def start_requests(self):
        # 默认的dict无序，遍历时不能保证安装插入顺序获取
        param_list = OrderedDict()

        # 初始赋值
        param_list['token'] = '70f12f2f4f091e459a279469fe49eca5'
        param_list['st'] = 'ltsj'
        param_list['sr'] = -1
        param_list['p'] = 1
        param_list['ps'] = 300
        param_list['type'] = 'XSJJ_NJ_PC'
        param_list['js'] = 'var%20{}='.format(self.generate_random_prefix()) \
                           + '{pages:(tp),data:(x)}'
        param_list['filter'] = '(gpdm=)'
        param_list['rt'] = self.current_milli_time()

        # 组织查询参数
        query_param = ''
        for kv in param_list.items():
            if kv[0] is 'token':
                query_param += '?{0}={1}'.format(*kv)
            else:
                query_param += '&{0}={1}'.format(*kv)

        begin_url = self.start_urls[0] + query_param
        self.logger.info('begin_url=%s', begin_url)

        yield Request(
            url=begin_url,
            meta={'page_no': param_list['p'], 'page_size': param_list['ps']}
        )

    def parse(self, response):
        assert isinstance(response, Response)
        # 去除头部的'=', 得到json格式的文本
        body_list = re.split('^[^=]*(=+)', str(response.body))
        json_text = body_list[2]

        # 解析pagedata的JSON数据体，构造并填充item对象后返回
        json_obj = demjson.decode(json_text)
        if 'data' in json_obj and len(json_obj['data']) > 0:
            page_data = json_obj['data']
            assert isinstance(page_data, list)
            for unit in page_data:
                assert isinstance(unit, dict)

                item = RestrictedItem()
                item['symbol'] = unit['gpdm']
                item['name'] = unit['sname']

                # 解禁时间，注意日期与时间采用'T'字符分割
                item['circulation_date'] = unit['ltsj']
                item['shareholders_num'] = unit['gpcjjgds']
                item['share_num'] = unit['jjsl']
                item['real_share_num'] = unit['kjjsl']
                item['non_share_num'] = unit['wltsl']
                item['real_share_price'] = unit['jjsz']

                # 占总市值比例需要乘以100%
                zzb_string = str(unit['zzb'])
                if self.is_float_string(zzb_string):
                    item['equity_ratio'] = string.atof(zzb_string) * 100
                else:
                    item['equity_ratio'] = zzb_string

                # 占流通市值比例需要乘以100%
                zb_string = str(unit['zb'])
                if self.is_float_string(zb_string):
                    item['share_ratio'] = string.atof(zb_string) * 100
                else:
                    item['share_ratio'] = zb_string

                item['close_price'] = unit['newPrice']
                item['share_type'] = unit['xsglx']
                item['before_range'] = unit['jjqesrzdf']
                item['after_range'] = unit['jjhesrzdf']

                yield item
        else:
            self.logger.info('page_data data is empty')

        page_total = json_obj['pages']
        page_size = response.meta['page_size']
        page_no = response.meta['page_no']
        self.logger.info('page_total=%s, page_no=%s, page_size=%s', page_total, page_no, page_size)

        if page_no < page_total:
            page_no += 1
            next_url = re.sub('p=\d+', 'p={}'.format(page_no), response.url)
            yield Request(
                url=next_url,
                meta={'page_no': page_no, 'page_size': page_size}
            )
            self.logger.info('next_url=%s', next_url)
        else:
            self.logger.info('{} is finished'.format(self.name))
