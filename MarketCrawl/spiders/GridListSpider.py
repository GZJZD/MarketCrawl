#!/usr/bin/env python
# encoding: utf-8

'''
@author: panhongfa
@license: (C) Copyright 2017-2020, Node Supply Chain Manager Corporation Limited.
@contact: panhongfas@163.com
@software: PyCharm
@file: GridListSpider.py
@time: 2018/8/10 14:50
@desc: 基本指标爬虫
@format: jQuery({data: [..., ...], recordsFiltered: num})
'''

from scrapy.spiders import Spider
from scrapy.http import Request
from scrapy.http import Response
from scrapy import signals
from scrapy.loader import ItemLoader
from collections import OrderedDict
from MarketCrawl.items import BasicIndicatorItem
import time
import demjson
import re

class GridListSpider(Spider):
    name = 'GridListSpider'
    allowed_domains = ['nufm.dfcfw.com']
    start_urls = ['http://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx']

    custom_settings = {
        #'LOG_FILE': './log/{}'.format(__name__)
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
    def current_milli_time():
        milli_time = lambda: int(round(time.time() * 1000))
        return milli_time()

    def start_requests(self):
        # 默认的dict无序，遍历时不能保证安装插入顺序获取
        param_list = OrderedDict()

        # 初始赋值
        param_list['cb'] = 'jQuery'
        param_list['type'] = 'CT'
        param_list['token'] = '4f1862fc3b5e77c150a2b985b12db0fd'
        param_list['sty'] = 'FCOIATC'
        param_list['js'] = '(%7Bdata%3A%5B(x)%5D%2CrecordsFiltered%3A(tot)%7D)'
        param_list['cmd'] = 'C._A'
        param_list['st'] = '(ChangePercent)'
        param_list['sr'] = -1
        param_list['p'] = 1
        param_list['ps'] = 300
        # 更新当前时间戳，注意是十三位UTC时间
        param_list['_'] = self.current_milli_time()

        # 组织查询参数
        query_param = ''
        for kv in param_list.items():
            if kv[0] is 'cb':
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
        # 去除头尾的'()', 得到json格式的文本
        body_list = re.split('[()]', str(response.body))

        # 正则分割得到的list结构为['jQuery', {data: [..., ...], recordsFiltered: num}, '']
        json_text = body_list[1]

        # 解析JSON串
        json_obj = demjson.decode(json_text)
        assert isinstance(json_obj, dict)
        page_data = json_obj['data']

        assert isinstance(page_data, list)
        for unit_text in page_data:
            assert isinstance(unit_text, unicode)
            unit = unit_text.split(u',')

            l = ItemLoader(item=BasicIndicatorItem())
            l.add_value('type', unit[0])
            l.add_value('symbol', unit[1])
            l.add_value('name', unit[2])
            l.add_value('last_price', unit[3])
            l.add_value('change_amount', unit[4])
            l.add_value('change_rate', unit[5])
            l.add_value('turnover_volume', unit[6])
            l.add_value('turnover_amount', unit[7])

            l.add_value('highest', unit[9])
            l.add_value('lowest', unit[10])
            l.add_value('price_open', unit[11])
            l.add_value('prev_close', unit[12])

            l.add_value('quantity_ratio', unit[14])
            l.add_value('turnover_hand', unit[15])
            l.add_value('pe_ratio', unit[16])
            l.add_value('pb_ratio', unit[17])

            l.add_value('market_begin_time', unit[23])
            l.add_value('last_update_time', unit[24])
            yield l.load_item()

        record_total = json_obj['recordsFiltered']
        page_size = response.meta['page_size']
        page_no = response.meta['page_no']
        self.logger.info('record_total = %s, page_no = %s, page_size = %s, undo_size = %s',
                    record_total, page_no, page_size, record_total - page_no * page_size)

        if page_no * page_size < record_total:
            page_no += 1
            next_url = re.sub('p=\d+', 'p={}'.format(page_no), response.url)
            yield Request(
                url=next_url,
                meta={'page_no': page_no, 'page_size': page_size}
            )

            self.logger.info('next_url=%s', next_url)
        else:
            self.logger.info('{} is finished'.format(self.name))
