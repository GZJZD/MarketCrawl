# -*- coding: utf-8 -*-
from scrapy.spiders import Spider
from scrapy.http import Request
from scrapy.http import Response
from scrapy import signals
from scrapy.loader import ItemLoader
from collections import OrderedDict
from MarketCrawl.logger import logger
from MarketCrawl.items import *
import time
import demjson
import re
import random
import string

class MainInfluxSpider(Spider):
    name = 'MainInfluxSpider'
    allowed_domains = ['quote.eastmoney.com', 'nufm.dfcfw.com']
    start_urls = ['http://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx']

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
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
        param_list['type'] = 'ct'
        param_list['st'] = '(BalFlowMain)'
        param_list['sr'] = -1
        param_list['p'] = 1
        param_list['ps'] = 300
        param_list['js'] = 'var%20{}='.format(self.generate_random_prefix()) \
                           + '{pages:(pc),date:%222014-10-22%22,data:[(x)]}'

        param_list['token'] = '894050c76af8597a853f5b408b759f5d'
        param_list['cmd'] = 'C._AB'
        param_list['sty'] = 'DCFFITA'
        param_list['rt'] = self.current_milli_time()

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
            meta={'page_no': param_list['p'], 'page_size': param_list['ps']}
        )

    def parse(self, response):
        assert isinstance(response, Response)
        # 去除头部的'=', 得到json格式的文本
        body_list = re.split('^[^=]*(?=)=', str(response.body))
        json_text = body_list[1]

        json_obj = demjson.decode(json_text)
        assert isinstance(json_obj, dict)

        page_data = json_obj['data']
        assert isinstance(page_data, list)
        for unit_text in page_data:
            assert isinstance(unit_text, unicode)
            unit = unit_text.split(u',')

            item = MainInfluxItem()
            item['symbol'] = unit[1]
            item['name'] = unit[2]

            item['main_influx_price'] = unit[5]
            item['main_influx_ratio'] = unit[6]

            item['huge_influx_price'] = unit[7]
            item['huge_influx_ratio'] = unit[8]

            item['large_influx_price'] = unit[9]
            item['large_influx_ratio'] = unit[10]

            item['middle_influx_price'] = unit[11]
            item['middle_influx_ratio'] = unit[12]

            item['small_influx_price'] = unit[13]
            item['small_influx_ratio'] = unit[14]

            item['last_update_time'] = unit[15]

            yield item

        page_total = json_obj['pages']
        page_size = response.meta['page_size']
        page_no = response.meta['page_no']
        logger.info('page_total=%s, page_no=%s, page_size=%s', page_total, page_no, page_size)

        if page_no < page_total:
            page_no += 1
            next_url = re.sub('p=\d+', 'p={}'.format(page_no), response.url)
            yield Request(
                url=next_url,
                meta={'page_no': page_no, 'page_size': page_size}
            )

            logger.info('next_url=%s', next_url)