# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.spiders import Spider
from fake_useragent import UserAgent
from datetime import datetime, timedelta
from twisted.web._newclient import ResponseNeverReceived
from twisted.internet.error import TimeoutError, ConnectionRefusedError, ConnectError
import requests
import json

# 随机更换User-Agent
class MarketcrawlUserAgentMiddleware(object):

    def __init__(self):
        super(MarketcrawlUserAgentMiddleware, self).__init__()
        self.ua = UserAgent()

    def process_request(self, request, spider):
        assert isinstance(spider, Spider)
        ua = getattr(self.ua, spider.settings['USER_AGETN_TYPE'])
        if ua:
            request.headers.setdefault('User-Agent', ua)
        else:
            spider.logger.info("unkown user agent type by spider: %s" % spider)


class MarketcrawlSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class MarketcrawlHttpProxyMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    # 遇到这些类型的错误直接当做代理不可用处理掉, 不再传给retrymiddleware
    DONT_RETRY_ERRORS = (TimeoutError, ConnectionRefusedError, ResponseNeverReceived, ConnectError, ValueError)

    def __init__(self, use_https):
        # 保存上次不用代理直接连接的时间点
        self.last_no_proxy_time = datetime.now()
        # 一定分钟数后切换回不用代理, 因为用代理影响到速度
        self.recover_interval = 20
        # 初始时不使用代理,采用直接连接
        self.is_using_direct = True
        # 使用http代理还是https代理
        self.using_https = use_https

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        use_https = crawler.settings.getbool('HTTPS_PROXY')
        s = cls(use_https)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called

        # 使用代理超过一定时间后，主动切回直接连接，但此时不将IP从代理IP地址池中删除
        if self.is_using_direct is False and datetime.now() > (self.last_no_proxy_time + timedelta(minutes=self.recover_interval)):
            spider.logger.info("After %d minutes later, recover from using proxy" % self.recover_interval)
            self.last_no_proxy_time = datetime.now()
            self.is_using_direct = True

        # 有些代理会把请求重定向到一个莫名其妙的地址
        request.meta["dont_redirect"] = True

        # spider发现parse error, 要求使用代理或更换代理
        if "change_proxy" in request.meta.keys() and request.meta["change_proxy"]:
            spider.logger.info("change proxy request get by spider: %s" % request)
            self.invalid_proxy(request.meta["proxy_ip"], spider)
            request.meta["change_proxy"] = False
            self.is_using_direct = False



    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)