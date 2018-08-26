# -*- coding: utf-8 -*-
from scrapy import cmdline
import sys

#name = 'GridListSpider'
#name = 'MainInfluxSpider'
#name = 'FinancialNoticeSpider'
#name = 'ShareHolderSpider'
#name = 'ShareBuybackSpider'
#name = 'SharePledgeSpider'
#name = 'RestrictedSpider'
#name = 'CompanyAnnouncementSpider'
#name = 'CompanyAnnouncementSpider -a mode=period'
name = 'CompanyAnnouncementSpider -a mode=newest'
#name = 'CompanyNewSpider'
#name = 'CompanyNewSpider -a mode=period'
#name = 'CompanyNewSpider -a mode=newest'
cmd = "scrapy crawl {0}".format(name)
cmdline.execute(cmd.split())

