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
RETRY_TIMES = 3
DOWNLOAD_TIMEOUT = 60
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

# 加载pipelines项
ITEM_PIPELINES = {
    'MarketCrawl.pipelines.MarketCrawlJsonPipeline': 300, #保存到文件
    'MarketCrawl.pipelines.MarketCrawlSQLPipeline': 300,  #保存到mysql数据库
}

# 取消默认的useragent,使用新的useragent
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'MarketCrawl.middlewares.MarketcrawlUserAgentMiddleware': 300,
}

# 数据库配置
DATABASE_CONNECTION = {
    "MYSQL_HOST": "47.52.77.50",
    "MYSQL_PORT": 3306,
    "MYSQL_USER": "root",
    "MYSQL_PASSWORD": "1",
    "MYSQL_DATABASE": "options",
}

