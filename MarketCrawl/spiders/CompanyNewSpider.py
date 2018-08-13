# -*- coding: utf-8 -*-
from scrapy.spiders import Spider
from scrapy.http import Request
from scrapy.http import Response
from scrapy import signals
from collections import OrderedDict
from MarketCrawl.logger import logger
from MarketCrawl.items import *
import time
import pytz
import datetime
import demjson
import re
import random
import string
import hashlib

class CompanyNewSpider(Spider):
    name = 'CompanyNewSpider'
    allowed_domains = ['data.eastmoney.com',]
    start_urls = ['http://data.eastmoney.com/notices/getdata.ashx']

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
        param_list['StockCode'] = ''
        param_list['FirstNodeType'] = 0
        param_list['CodeType'] = 1
        param_list['PageIndex'] = 46
        param_list['PageSize'] = 500
        param_list['jsObj'] = '{}'.format(self.generate_random_prefix())
        param_list['SecNodeType'] = 0
        param_list['Time'] = ''
        param_list['rt'] = self.current_milli_time()

        # 组织查询参数
        query_param = ''
        for kv in param_list.items():
            if kv[0] is 'StockCode':
                query_param += '?{0}={1}'.format(*kv)
            else:
                query_param += '&{0}={1}'.format(*kv)

        begin_url = self.start_urls[0] + query_param
        logger.info('begin_url=%s', begin_url)

        yield Request(
            url=begin_url,
            meta={'page_no': param_list['PageIndex'], 'page_size': param_list['PageSize']}
        )

    def parse(self, response):
        assert isinstance(response, Response)
        # 去除头部的'='和尾部的';' 得到json格式的文本
        body_list = re.split('^[^=]*(=+)|;$', str(response.body).decode('gbk'))
        json_text = body_list[2]

        json_obj = demjson.decode(json_text)
        assert isinstance(json_obj, dict)

        page_data = json_obj['data']
        assert isinstance(page_data, list)
        for unit in page_data:
            assert isinstance(unit, dict)

            item = CompanyNewItem()
            for cdsy in unit['CDSY_SECUCODES']:
                if 'A' in cdsy['SECURITYTYPE']:
                    item['symbol'] = cdsy['SECURITYCODE']
                    item['name'] = cdsy['SECURITYFULLNAME']
                    break
                else:
                    item['symbol'] = None
                    item['name'] = None

            item['announce_title'] = unit['NOTICETITLE']
            item['announce_url'] = unit['Url']

            # 计算url的MD5值
            url_md5 = hashlib.md5(item['announce_url']).hexdigest()
            item['announce_url_md5'] = url_md5

            if "ANN_RELCOLUMNS" in unit:
                item['announce_type'] = unit['ANN_RELCOLUMNS'][0]['COLUMNNAME']
            else:
                item['announce_type'] = None

            # 注意日期和时间字符串以'T'来分割
            item['announce_date'] = unit['NOTICEDATE']

            yield item

        page_total = json_obj['pages']
        page_size = response.meta['page_size']
        page_no = response.meta['page_no']
        logger.info('page_total=%s, page_no=%s, page_size=%s', page_total, page_no, page_size)

        if page_no < page_total:
            page_no += 1
            next_url = re.sub('PageIndex=\d+', 'PageIndex={}'.format(page_no), response.url)
            logger.info('next_url=%s', next_url)
            yield Request(
                url=next_url,
                meta={'page_no': page_no, 'page_size': page_size}
            )
