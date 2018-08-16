#!/usr/bin/env python
# encoding: utf-8

'''
@author: panhongfa
@license: (C) Copyright 2017-2020, Node Supply Chain Manager Corporation Limited.
@contact: panhongfas@163.com
@software: PyCharm
@file: ShareHolderSpider.py
@time: 2018/8/10 14:52
@desc: 股东增减持爬虫, JS接口支持全量查询，不需要按照code进行分页查询
@format: var xxxx={pages: N, data: [..., ...], url: ...}
'''

from scrapy.spiders import Spider
from scrapy.http import Request
from scrapy.http import Response
from scrapy import signals
from collections import OrderedDict
from MarketCrawl.logger import logger
from MarketCrawl.items import *
import time
import demjson
import re
import random
import string

class ShareHolderSpider(Spider):
    name = 'ShareHolderSpider'
    allowed_domains = ['data.eastmoney.com', 'dcfm.eastmoney.com']
    start_urls = ['http://data.eastmoney.com/DataCenter_V3/gdzjc.ashx']

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
        logger.info('###############################%s Start###################################', spider.name)

    def spider_closed(self, spider):
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
        # 默认的dict无序，遍历时不能保证安装插入顺序获取
        param_list = OrderedDict()

        # 初始赋值
        param_list['pagesize'] = 300
        param_list['page'] = 1
        param_list['js'] = 'var%20{}'.format(self.generate_random_prefix())
        param_list['param'] = ''
        param_list['sortRule'] = -1
        param_list['sortType'] = 'BDJZ'
        param_list['tabid'] = 'all'
        param_list['code'] = ''
        param_list['name'] = ''
        param_list['rt'] = self.current_milli_time()

        # 组织查询参数
        query_param = ''
        for kv in param_list.items():
            if kv[0] is 'pagesize':
                query_param += '?{0}={1}'.format(*kv)
            else:
                query_param += '&{0}={1}'.format(*kv)

        begin_url = self.start_urls[0] + query_param
        logger.info('begin_url=%s', begin_url)

        yield Request(
            url=begin_url,
            meta={'page_no': param_list['page'], 'page_size': param_list['pagesize']}
        )

    def parse(self, response):
        assert isinstance(response, Response)
        # 去除头部的'=', 得到json格式的文本
        body_list = re.split('^[^=]*(=+)', str(response.body).decode('gbk'))
        json_text = body_list[2]

        # 解析pagedata的JSON数据体，构造并填充item对象后返回
        json_obj = demjson.decode(json_text)
        if 'data' in json_obj and len(json_obj['data']) > 0:
            page_data = json_obj['data']

            assert isinstance(page_data, list)
            for unit_text in page_data:
                assert isinstance(unit_text, unicode)
                unit = unit_text.split(u',')

                item = ShareHolderItem()
                item['symbol'] = unit[0]
                item['name'] = unit[1]
                item['shareholders_name'] = unit[4]

                item['change_type'] = unit[5]
                item['change_share'] = unit[6]
                item['change_share_ratio'] = unit[7]

                item['total_hold'] = unit[9]
                item['total_equity_ratio'] = unit[10]

                item['total_share'] = unit[11]
                item['total_share_ratio'] = unit[12]

                item['begin_date'] = unit[13]
                item['end_date'] = unit[14]
                item['announcement_date'] = unit[15]

                item['change_equity_ratio'] = unit[16]

                yield item
        else:
            logger.info('page_data data is empty')

        page_total = json_obj['pages']
        page_size = response.meta['page_size']
        page_no = response.meta['page_no']
        logger.info('page_total=%s, page_no=%s, page_size=%s', page_total, page_no, page_size)

        if page_no < page_total:
            page_no += 1
            next_url = re.sub('page=\d+', 'page={}'.format(page_no), response.url)
            yield Request(
                url=next_url,
                meta={'page_no': page_no, 'page_size': page_size}
            )

            logger.info('next_url=%s', next_url)
        else:
            logger.info('{} is finished'.format(self.name))