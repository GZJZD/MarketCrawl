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

class FinancialNoticeSpider(Spider):
    name = 'FinancialNoticeSpider'
    allowed_domains = ['quote.eastmoney.com', 'nufm.dfcfw.com', 'dcfm.eastmoney.com']
    start_urls = ['http://dcfm.eastmoney.com//em_mutisvcexpandinterface/api/js/get']

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
        param_list['type'] = 'YJBB20_YJYG'
        param_list['token'] = '70f12f2f4f091e459a279469fe49eca5'
        param_list['st'] = 'ndate'
        param_list['sr'] = -1
        param_list['p'] = 1
        param_list['ps'] = 300
        param_list['js'] = 'var%20{}='.format(self.generate_random_prefix()) \
                           + '{pages:(tp),data:%20(x)}'

        param_list['filter'] = '(IsLatest=%27T%27)(enddate=^2018-06-30^)'
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
        for unit in page_data:
            assert isinstance(unit, dict)

            item = FinancialNoticeItem()
            item['symbol'] = unit['scode']
            item['name'] = unit['sname']
            item['sclx'] = unit['sclx']
            item['forecast_content'] = unit['forecastcontent']

            item['forecast_left'] = unit['forecastl']
            item['forecast_right'] = unit['forecastt']

            item['increase_left'] = unit['increasel']
            item['increase_right'] = unit['increaset']

            item['change_reason'] = unit['changereasondscrpt']
            item['preview_type'] = unit['forecasttype']
            item['previous_year_profit'] = unit['yearearlier']
            item['hymc'] = unit['hymc']
            item['announcement_date'] = unit['ndate']

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
