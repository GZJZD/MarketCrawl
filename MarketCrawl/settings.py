# -*- coding: utf-8 -*-

# Scrapy settings for $project_name project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

import os
import scrapy.downloadermiddlewares.httpproxy

BOT_NAME = 'MarketCrawl'

SPIDER_MODULES = ['MarketCrawl.spiders']
NEWSPIDER_MODULE = 'MarketCrawl.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'MarketCrawl (+http://www.yourdomain.com)'

# 调用相应的浏览器类型属性就可以生成相应的User-Agent<br>ua.chrome<br>ua.firefox<br>ua.ie<br>ua.random
USER_AGETN_TYPE = 'random'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# 日志设定
LOG_LEVEL = 'INFO'
LOG_ENCODING = 'utf-8'
LOG_FORMAT = '%(asctime)s\tFile \"%(filename)s\",line %(lineno)s\t%(levelname)s: %(message)s'

# 全局的下载延时相关参数配置
DOWNLOAD_DELAY = 1
DOWNLOAD_TIMEOUT = 60

# 重试相关参数配置
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 400, 403, 404, 408]

# 数据和日志目录设定
JSON_DATA_DIR = './data'
if not os.path.exists(JSON_DATA_DIR):
    os.mkdir(JSON_DATA_DIR)

LOG_FILES_DIR = './log'
if not os.path.exists(LOG_FILES_DIR):
    os.mkdir(LOG_FILES_DIR)

# 代理服务器地址
HTTPS_PROXY = 'http://127.0.0.1:8000'

# 一定分钟数后切换回不用代理, 因为用代理影响到速度
RECOVER_INTERVAL = 20
# 每次从本地代理服务获取的新代理数量
FETCH_PROXY_FIXED_SIZE = 6
# 当有效代理小于这个数时(包括直连), 从网上抓取新的代理, 可以将这个数设为为了满足每个ip被要求输入验证码后得到足够休息时间所需要的代理数
# 例如爬虫在十个可用代理之间切换时, 每个ip经过数分钟才再一次轮到自己, 这样就能get一些请求而不用输入验证码.
# 如果这个数过小, 例如两个, 爬虫用A ip爬了没几个就被ban, 换了一个又爬了没几次就被ban, 这样整个爬虫就会处于一种忙等待的状态, 影响效率
EXTEND_PROXY_THRESHOLD = 10

# 加载pipelines项
ITEM_PIPELINES = {
    'MarketCrawl.pipelines.MarketCrawlJsonPipeline': 300, #保存到文件
    'MarketCrawl.pipelines.MarketCrawlSQLPipeline': 301,  #保存到mysql数据库
}

# 取消默认的useragent,使用新的useragent
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'MarketCrawl.middlewares.MarketcrawlUserAgentMiddleware': 403,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
    'MarketCrawl.middlewares.MarketcrawlHttpProxyMiddleware': 543
}

# 数据库配置
DATABASE_CONNECTION = {
    "MYSQL_HOST": "47.52.77.50",
    "MYSQL_PORT": 3306,
    "MYSQL_USER": "root",
    "MYSQL_PASSWORD": "1",
    "MYSQL_DATABASE": "options",
}

