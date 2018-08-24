#!/usr/bin/env python
# encoding: utf-8

'''
@author: panhongfa
@license: (C) Copyright 2017-2020, Node Supply Chain Manager Corporation Limited.
@contact: panhongfas@163.com
@software: PyCharm
@file: ShareBuybackSpider.py
@time: 2018/8/10 14:52
@desc: 股权质押爬虫, JS接口支持全量查询，可不需要按照code进行分页查询
@format: var xxxx={code: 0,count: N, data: [{...}, {...}], pageindex: N, pages: N, pagesize: N}
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

class SharePledgeSpider(Spider):
    name = 'SharePledgeSpider'
    allowed_domains = ['api.dataide.eastmoney.com',]
    start_urls = ['http://api.dataide.eastmoney.com/data/GDZY_GD_SUM']

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
    def current_milli_time():
        milli_time = lambda: int(round(time.time() * 1000))
        return milli_time()

    def start_requests(self):
        # 默认的dict无序，遍历时不能保证安装插入顺序获取
        param_list = OrderedDict()

        # 初始赋值
        param_list['pageindex'] = 1
        param_list['pagesize'] = 200
        param_list['orderby'] = 'updatedate'
        param_list['order'] = 'desc'
        param_list['jsonp_callback'] = 'var%20{}=(x)'.format(self.generate_random_prefix())
        param_list['rt'] = self.current_milli_time()

        # 组织查询参数
        query_param = ''
        for kv in param_list.items():
            if kv[0] is 'pageindex':
                query_param += '?{0}={1}'.format(*kv)
            else:
                query_param += '&{0}={1}'.format(*kv)

        begin_url = self.start_urls[0] + query_param
        self.logger.info('begin_url=%s', begin_url)

        yield Request(
            url=begin_url,
            meta={'page_no': param_list['pageindex'], 'page_size': param_list['pagesize']}
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

                item = SharePledgeItem()
                item['symbol'] = unit['scode']
                item['name'] = unit['sname']
                item['shareholders_name'] = unit['gd_name']

                item['pledge_number'] = unit['new_zy_count']
                item['pledge_volumn'] = unit['amtsharefrozen']
                item['pledge_price'] = unit['sz']

                # 占所持股份比例需要乘以100%
                item['share_ratio'] = string.atof(str(unit['zb'])) * 100
                item['equity_datio'] = unit['zzb']

                item['close_position_range_left'] = unit['pcx_minvalue']
                item['close_position_range_right'] = unit['pcx_maxvalue']

                item['warning_position_range_left'] = unit['yjx_minvalue']
                item['warning_position_range_right'] = unit['yjx_maxvalue']

                # 获取到的是UTC时间，这里将UTC时间转换成字符串时间
                if unit['updatedate'] is None:
                    l_update_date = 0
                else:
                    l_update_date = string.atoi(str(unit['updatedate']))

                # 获取UTC时间转换后的时间戳
                item['update_date'] = self.transfrom_beijing_time(l_update_date)

                yield item
        else:
            self.logger.info('page_data data is empty')

        page_total = json_obj['pages']
        page_size = response.meta['page_size']
        page_no = response.meta['page_no']
        self.logger.info('page_total=%s, page_no=%s, page_size=%s', page_total, page_no, page_size)

        if page_no < page_total:
            page_no += 1
            next_url = re.sub('pageindex=\d+', 'pageindex={}'.format(page_no), response.url)
            yield Request(
                url=next_url,
                meta={'page_no': page_no, 'page_size': page_size}
            )
            self.logger.info('next_url=%s', next_url)
        else:
            self.logger.info('{} is finished'.format(self.name))
