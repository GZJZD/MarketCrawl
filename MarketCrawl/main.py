# -*- coding: utf-8 -*-
from scrapy import cmdline
import sys

#name = 'GridListSpider'
#name = 'MainInfluxSpider'
#name = 'FinancialNoticeSpider'
#name = 'ShareHolderSpider'
#name = 'ShareBuybackSpider'
#name = 'SharePledgeSpider'
name = 'RestrictedSpider'
#name = 'AnnouncementSpider'
cmd = "scrapy crawl {0}".format(name)
cmdline.execute(cmd.split())

