#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from twisted.web._newclient import ResponseNeverReceived
from twisted.internet.error import TimeoutError, ConnectionRefusedError, ConnectError
from scrapy.spiders import Spider
import requests
import json

class HttpProxyMiddleware(object):
    # 遇到这些类型的错误直接当做代理不可用处理掉, 不再传给retrymiddleware
    DONT_RETRY_ERRORS = (TimeoutError, ConnectionRefusedError, ResponseNeverReceived, ConnectError, ValueError)

    def __init__(self, interval):
        # 保存上次不用代理直接连接的时间点
        self.last_no_proxy_time = datetime.now()
        # 初始化代理列表, 第一元素表示直连
        self.proxyes = [{"proxy": None, "ip": None, "count": 0}]
        # 初始时使用0号代理(即无代理,直接连接)
        self.proxy_index = 0
        # 上一次获取新代理的时间
        self.last_fetch_proxy_time = datetime.now()

        self.recover_interval = interval

    @classmethod
    def from_crawler(cls, crawler):
        interval = crawler.settings.getint('RECOVER_INTERVAL')
        return cls(interval)

    # 尝试从本地代理服务中获取一个新的代理IP
    def fetch_new_proxy(self, spider):
        assert isinstance(spider, Spider)

        for i in range(1, 2):
            r = requests.get('{}/?types=0&count=1&protocol={}'.format(spider.settings['HTTPS_PROXY'], i))
            ip_ports = json.loads(r.text)

            if len(ip_ports) > 0:
                for item in ip_ports:
                    ip = item[0]
                    port = item[1]

                    proxy = {
                        "proxy": 'https://%s:%s' % (ip, port),
                        "ip": ip,
                        "count": 0
                    }
                    self.proxyes.append(proxy)

                spider.logger.info("fetch new proxy, ip_ports: %s" % ip_ports)
                return True
            else:
                continue

        return False

    # 代理IP标记不为空时，调用proxy接口删除该代理IP
    def remove_invalid_proxy(self, index, spider):
        assert isinstance(spider, Spider)

        if index == 0:
            return False
        elif index < len(self.proxyes):
            proxy_ip = self.proxyes[index]['ip']
            if proxy_ip is not None:
                r = requests.get('{}/delete?ip={}'.format(spider.settings['HTTPS_PROXY'], proxy_ip))
                spider.logger.info("remove invalid proxy, ip: %s, result: %s" % (proxy_ip, r.text))
            else:
                pass

            self.proxyes.pop(index)
            return True
        else:
            return False

    def set_proxy(self, request, spider):
        # 代理ip数量不够时，从本地代理服务获取一个
        if len(self.proxyes) == 1:
            self.fetch_new_proxy(spider)

        # index标记非法时，强制使用直接连接
        if self.proxy_index > 1:
            self.proxy_index = 0

        # 每次不用代理直接下载时更新self.last_no_proxy_time
        if self.proxy_index == 0:
            self.last_no_proxy_time = datetime.now()

        proxy = self.proxyes[self.proxy_index]

        if proxy["proxy"]:
            request.meta["proxy"] = proxy["proxy"]
        elif "proxy" in request.meta.keys():
            del request.meta["proxy"]

        request.meta["proxy_index"] = self.proxy_index

    def invalid_proxy(self, request, spider):
        assert isinstance(spider, Spider)

        # 代理IP标记不为空时，调用proxy接口删除该代理IP
        if "proxy_ip" in request.meta.keys() and request.meta["proxy_ip"] is not None:
            proxy_ip = request.meta["proxy_ip"]
            r = requests.get('{}/delete?ip={}'.format(spider.settings['HTTPS_PROXY'], proxy_ip))
            spider.logger.info("invalidate %s, result: %s" % (proxy_ip, r.text))
        else:
            pass
        request.meta["proxy_ip"] = None

    def process_request(self, request, spider):
        # 使用代理超过一定时间后，主动切回直接连接,也就是把下标proxy_index重置为0
        if self.proxy_index > 0 and datetime.now() > (self.last_no_proxy_time + timedelta(minutes=self.recover_interval)):
            spider.logger.info("After %d minutes later, recover from using proxy" % self.recover_interval)
            self.last_no_proxy_time = datetime.now()
            self.proxy_index = 0

        request.meta["dont_redirect"] = True  # 有些代理会把请求重定向到一个莫名其妙的地址

        # spider发现parse error, 强制更换代理
        if "change_proxy" in request.meta.keys() and request.meta["change_proxy"]:
            spider.logger.info("change proxy request get by spider: %s" % request)
            if not self.remove_invalid_proxy(request.meta["proxy_index"], spider):
                self.proxy_index = 1

            request.meta["change_proxy"] = False

        self.set_proxy(request, spider)

        #Scrapy将继续处理该request，执行其他的中间件的相应方法，直到合适的下载器处理函数(downloadhandler)被调用
        return None

    def process_response(self, request, response, spider):
        """
        检查response.status, 根据status是否在允许的状态码中决定是否切换到下一个proxy, 或者禁用proxy
        """
        if "proxy" in request.meta.keys():
            spider.logger.info("%s %s %s" % (request.meta["proxy"], response.status, request.url))
        else:
            spider.logger.info("None %s %s" % (response.status, request.url))

        # status不是正常的200而且不在spider声明的正常爬取过程中可能出现的status列表中, 则认为代理无效, 则强制切换代理
        if response.status != 200:
            if not hasattr(spider, "website_possible_httpstatus_list") \
                    or response.status not in spider.website_possible_httpstatus_list:
                new_request = request.copy()
                new_request.dont_filter = True
                new_request.meta["change_proxy"] = True
                return new_request

            # 其他错误时直接进行重试
            else:
                return request
        else:
            return response

    def process_exception(self, request, exception, spider):
        spider.logger.info("%s exception: %s" % (request.url, exception))

        # 遇到这些类型的错误直接当做代理不可用处理掉, 不再传给retrymiddleware
        if isinstance(exception, self.DONT_RETRY_ERRORS):
                new_request = request.copy()
                new_request.dont_filter = True
                new_request.meta["change_proxy"] = True
                return new_request

        # 其他异常时不进行处理，直接给retrymiddleware处理
        else:
            return None
