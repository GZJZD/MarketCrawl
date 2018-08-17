# -*- coding: utf-8 -*-
from twisted.enterprise import adbapi
from MarketCrawl.logger import logger
from MarketCrawl.items import *
from scrapy.spiders import Spider
import codecs
import json
import decimal

class DecimalEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        super(DecimalEncoder, self).default(o)

class MarketCrawlJsonPipeline(object):
    file_handler = {}

    def process_item(self, item, spider):
        assert isinstance(spider, Spider)
        handler = self.file_handler[spider.name]
        line = json.dumps(dict(item), ensure_ascii=False, cls=DecimalEncoder) + "\n"
        handler.write(line)
        return item

    def open_spider(self, spider):
        assert isinstance(spider, Spider)
        self.file_handler[spider.name] = codecs.open('{}.json'.format(spider.name), 'w', encoding='utf-8')

    def close_spider(self, spider):
        assert isinstance(spider, Spider)
        self.file_handler[spider.name].close()


class MarketCrawlSQLPipeline(object):
    db_pool = None

    def __init__(self, pool):
        self.db_pool = pool

    @classmethod
    # This method is used by Scrapy to create your spiders.
    def from_settings(cls, settings):
        db_parms = dict(
            host=settings["DATABASE_CONNECTION"]['MYSQL_HOST'],
            port=settings["DATABASE_CONNECTION"]['MYSQL_PORT'],
            user=settings["DATABASE_CONNECTION"]['MYSQL_USER'],
            passwd=settings["DATABASE_CONNECTION"]['MYSQL_PASSWORD'],
            db=settings["DATABASE_CONNECTION"]['MYSQL_DATABASE'],
            use_unicode=True,
            charset="utf8",
        )

        pool = adbapi.ConnectionPool("pymysql", **db_parms)
        return cls(pool)

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        self.db_pool.close()

    def process_item(self, item, spider):
        assert isinstance(spider, Spider)
        if spider.name is 'GridListSpider':
            query = self.db_pool.runInteraction(self.handle_insert_grid_list, item)
            query.addErrback(self.handle_error)
        elif spider.name is 'MainInfluxSpider':
            query = self.db_pool.runInteraction(self.handle_insert_main_influx, item)
            query.addErrback(self.handle_error)
        elif spider.name is 'FinancialNoticeSpider':
            query = self.db_pool.runInteraction(self.handle_insert_financial_notice, item)
            query.addErrback(self.handle_error)
        elif spider.name is 'ShareHolderSpider':
            query = self.db_pool.runInteraction(self.handle_insert_share_holder, item)
            query.addErrback(self.handle_error)
        elif spider.name is 'ShareBuybackSpider':
            query = self.db_pool.runInteraction(self.handle_insert_share_buyback, item)
            query.addErrback(self.handle_error)
        elif spider.name is 'SharePledgeSpider':
            query = self.db_pool.runInteraction(self.handle_insert_share_pledge, item)
            query.addErrback(self.handle_error)
        elif spider.name is 'RestrictedSpider':
            query = self.db_pool.runInteraction(self.handle_insert_restricted, item)
            query.addErrback(self.handle_error)
        elif spider.name is 'CompanyAnnouncementSpider':
            query = self.db_pool.runInteraction(self.handle_insert_announcement, item)
            query.addErrback(self.handle_error)
        else:
            pass

    def handle_insert_grid_list(self, cursor, item):
        # 待执行的SQL语句
        sql = """INSERT INTO crawler_basic_index (
        shares_code, shares_name, shares_type, latest_price, rise_fall_ratio, rise_fall_price, 
        volumn, price, max_price, min_pirce, open_price, close_price, change_volumn, quantity_ratio, 
        pe_ratio, pb_ratio, date) 
	    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
	    ON DUPLICATE KEY UPDATE shares_code=%s, date=%s"""

        #从ITEM中获取SQL的数据项并定义为tupe类型
        assert isinstance(item, BasicIndicatorItem)

        params = []
        params.append(item['symbol'])
        params.append(item['name'])
        params.append(item['type'])
        params.append(item['last_price'])
        params.append(item['change_rate'])
        params.append(item['change_amount'])
        params.append(item['turnover_volume'])
        params.append(item['turnover_amount'])
        params.append(item['highest'])
        params.append(item['lowest'])
        params.append(item['price_open'])
        params.append(item['prev_close'])
        params.append(item['turnover_hand'])
        params.append(item['quantity_ratio'])
        params.append(item['pe_ratio'])
        params.append(item['pb_ratio'])

        data_and_hours = item['last_update_time'][0].split(u' ')
        params.append(data_and_hours[0])

        params.append(item['symbol'])
        params.append(data_and_hours[0])

        cursor.execute(sql, params)

    def handle_insert_main_influx(self, cursor, item):
        # 待执行的SQL语句
        sql = """INSERT INTO crawler_main_influx (
                shares_code, shares_name, main_influx_price, main_influx_ratio, huge_influx_price, huge_influx_ratio, 
                large_influx_price, large_influx_ratio, middle_influx_price, middle_influx_ratio, 
                small_influx_price, small_influx_ratio, date) 
        	    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        	    ON DUPLICATE KEY UPDATE shares_code=%s, date=%s"""

        #从ITEM中获取SQL的数据项并定义为tupe类型
        assert isinstance(item, MainInfluxItem)

        params = []
        params.append(item['symbol'])
        params.append(item['name'])
        params.append(item['main_influx_price'])
        params.append(item['main_influx_ratio'])
        params.append(item['huge_influx_price'])
        params.append(item['huge_influx_ratio'])
        params.append(item['large_influx_price'])
        params.append(item['large_influx_ratio'])
        params.append(item['middle_influx_price'])
        params.append(item['middle_influx_ratio'])
        params.append(item['small_influx_price'])
        params.append(item['small_influx_ratio'])

        data_and_hours = item['last_update_time'].split(u' ')
        params.append(data_and_hours[0])

        params.append(item['symbol'])
        params.append(data_and_hours[0])

        cursor.execute(sql, params)

    def handle_insert_financial_notice(self, cursor, item):
        # 待执行的SQL语句
        sql = """INSERT INTO crawler_financial_disclosure (
                shares_code, shares_name, performance_change, expected_net_profit_left, expected_net_profit_right, 
                performance_change_ratio_left, performance_change_ratio_right, performance_change_reason, preview_type, 
                previous_year_profit, announcement_date) 
        	    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        	    ON DUPLICATE KEY UPDATE shares_code=%s, announcement_date=%s"""

        #从ITEM中获取SQL的数据项并定义为tupe类型
        assert isinstance(item, FinancialNoticeItem)

        params = []
        params.append(item['symbol'])
        params.append(item['name'])
        params.append(item['forecast_content'])
        params.append(item['forecast_left'])
        params.append(item['forecast_right'])
        params.append(item['increase_left'])
        params.append(item['increase_right'])
        params.append(item['change_reason'])
        params.append(item['preview_type'])
        params.append(item['previous_year_profit'])
        params.append(item['announcement_date'])

        params.append(item['symbol'])
        params.append(item['announcement_date'])

        cursor.execute(sql, params)

    def handle_insert_share_holder(self, cursor, item):
        # 待执行的SQL语句
        sql = """INSERT INTO crawler_shareholders (
                shares_code, shares_name, shareholders_name, change_type, change_share, change_equity_ratio, 
                change_share_ratio, total_hold, total_equity_ratio, total_share, total_share_ratio, 
                begin_date, end_date, announcement_date) 
        	    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
        	    ON DUPLICATE KEY UPDATE shares_code=%s, announcement_date=%s"""

        #从ITEM中获取SQL的数据项并定义为tupe类型
        assert isinstance(item, ShareHolderItem)

        params = []
        params.append(item['symbol'])
        params.append(item['name'])
        params.append(item['shareholders_name'])
        params.append(item['change_type'])
        params.append(item['change_share'])
        params.append(item['change_equity_ratio'])
        params.append(item['change_share_ratio'])
        params.append(item['total_hold'])
        params.append(item['total_equity_ratio'])
        params.append(item['total_share'])
        params.append(item['total_share_ratio'])
        params.append(item['begin_date'])
        params.append(item['end_date'])
        params.append(item['announcement_date'])

        params.append(item['symbol'])
        params.append(item['announcement_date'])

        cursor.execute(sql, params)

    def handle_insert_share_buyback(self, cursor, item):
        # 待执行的SQL语句
        sql = """INSERT INTO crawler_share_buyback (
                shares_code, shares_name, buyback_price_range_left, buyback_price_range_right, close_price, buyback_volumn_range_left, 
                buyback_volumn_range_right, share_ratio_left, share_ratio_right, equity_ratio_left, equity_ratio_right, 
                buyback_amount_range_left, buyback_amount_range_right, begin_date, impl_progress, announcement_date) 
        	    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
        	    ON DUPLICATE KEY UPDATE shares_code=%s, announcement_date=%s"""

        #从ITEM中获取SQL的数据项并定义为tupe类型
        assert isinstance(item, ShareBuybackItem)

        params = []
        params.append(item['symbol'])
        params.append(item['name'])
        params.append(item['buyback_price_range_left'])
        params.append(item['buyback_price_range_right'])
        params.append(item['close_price'])
        params.append(item['buyback_volumn_range_left'])
        params.append(item['buyback_volumn_range_right'])
        params.append(item['share_ratio_left'])
        params.append(item['share_ratio_right'])
        params.append(item['equity_ratio_left'])
        params.append(item['equity_ratio_right'])
        params.append(item['buyback_amount_range_left'])
        params.append(item['buyback_amount_range_right'])

        # 处理begin_date
        begin_date_hours = item['begin_date'].split(u' ')
        params.append(begin_date_hours[0])

        # 处理impl_progress
        impl_progress= item['impl_progress']
        impl_progress_text = u'未定义'

        if impl_progress == '001':
            impl_progress_text = u'董事会预案'
        elif impl_progress == '002':
            impl_progress_text = u'股东大会通过'
        elif impl_progress == '003':
            impl_progress_text = u'股东大会否决'
        elif impl_progress == '004':
            impl_progress_text = u'实施中'
        elif impl_progress == '005':
            impl_progress_text = u'停止实施'
        elif impl_progress == '006':
            impl_progress_text = u'完成实施'

        params.append(impl_progress_text)

        # 处理announcement_date
        date_and_hours = item['announcement_date'].split(u' ')
        params.append(date_and_hours[0])

        params.append(item['symbol'])
        params.append(date_and_hours[0])

        cursor.execute(sql, params)

    def handle_insert_share_pledge(self, cursor, item):
        # 待执行的SQL语句
        sql = """INSERT INTO crawler_share_pledge (
                shares_code, shares_name, shareholders_name, pledge_number, pledge_volumn, pledge_price, share_ratio, 
                equity_datio, close_position_range_left, close_position_range_right, warning_position_range_left, 
                warning_position_range_right, update_date) 
        	    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
        	    ON DUPLICATE KEY UPDATE shares_code=%s, update_date=%s"""

        #从ITEM中获取SQL的数据项并定义为tupe类型
        assert isinstance(item, SharePledgeItem)

        params = []
        params.append(item['symbol'])
        params.append(item['name'])
        params.append(item['shareholders_name'])
        params.append(item['pledge_number'])
        params.append(item['pledge_volumn'])
        params.append(item['pledge_price'])
        params.append(item['share_ratio'])
        params.append(item['equity_datio'])
        params.append(item['close_position_range_left'])
        params.append(item['close_position_range_right'])
        params.append(item['warning_position_range_left'])
        params.append(item['warning_position_range_right'])

        # 处理update_date
        date_and_hours = item['update_date'].split(u' ')
        params.append(date_and_hours[0])

        params.append(item['symbol'])
        params.append(date_and_hours[0])

        cursor.execute(sql, params)

    def handle_insert_restricted(self, cursor, item):
        # 待执行的SQL语句
        sql = """INSERT INTO crawler_restricted_circulation (
                shares_code, shares_name, shareholders_num, share_num, real_share_num, non_share_num, real_share_price, 
                equity_ratio, share_ratio, close_price, share_type, before_range, after_range, circulation_date) 
        	    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
        	    ON DUPLICATE KEY UPDATE shares_code=%s, circulation_date=%s"""

        #从ITEM中获取SQL的数据项并定义为tupe类型
        assert isinstance(item, RestrictedItem)

        params = []
        params.append(item['symbol'])
        params.append(item['name'])
        params.append(item['shareholders_num'])
        params.append(item['share_num'])
        params.append(item['real_share_num'])
        params.append(item['non_share_num'])
        params.append(item['real_share_price'])
        params.append(item['equity_ratio'])
        params.append(item['share_ratio'])
        params.append(item['close_price'])
        params.append(item['share_type'])
        params.append(item['before_range'])
        params.append(item['after_range'])

        # 处理circulation_date，时间和日期以‘T’来分割
        date_and_hours = item['circulation_date'].split(u'T')
        params.append(date_and_hours[0])

        params.append(item['symbol'])
        params.append(date_and_hours[0])

        cursor.execute(sql, params)

    def handle_insert_announcement(self, cursor, item):
        # 待执行的SQL语句
        sql = """INSERT INTO crawler_company_announcement (
                shares_code, shares_name, announce_title, announce_url, announce_type, announce_date, announce_id) 
        	    VALUES (%s,%s,%s,%s,%s,%s,%s) 
        	    ON DUPLICATE KEY UPDATE shares_code=%s, announce_id=%s"""

        #从ITEM中获取SQL的数据项并定义为tupe类型
        assert isinstance(item, CompanyAnnouncementItem)

        params = []
        params.append(item['symbol'])
        params.append(item['name'])
        params.append(item['announce_title'])
        params.append(item['announce_url'])
        params.append(item['announce_type'])

        params.append(item['announce_date'])
        params.append(item['announce_id'])

        params.append(item['symbol'])
        params.append(item['announce_id'])

        cursor.execute(sql, params)

    def handle_error(self, failure):
        # 输出错误日志
        logger.error('database operation exception, failure=%s', failure)


