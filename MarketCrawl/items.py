# -*- coding: utf-8 -*-

from scrapy import Item, Field
from scrapy.loader.processors import *


class BasicIndicatorItem(Item):
    # 股票代码
    symbol = Field()
    # 股票名称
    name = Field()
    # 股票所在交易所类型
    type = Field()
    # 最新价
    last_price = Field()
    # 涨跌额
    change_amount = Field()
    # 涨跌幅
    change_rate = Field()
    # 昨收
    prev_close = Field()
    # 今开
    price_open = Field()
    # 最低价
    lowest = Field()
    # 最高价
    highest = Field()
    # 换手
    turnover_hand = Field()
    # 量比
    quantity_ratio = Field()
    # 成交量
    turnover_volume = Field()
    # 成交额
    turnover_amount = Field()
    # 市盈
    pe_ratio = Field()
    # 市净
    pb_ratio = Field()
    # 上市时间
    market_begin_time = Field()
    # 数据更新时间
    last_update_time = Field()


class MainInfluxItem(Item):
    # 股票代码
    symbol = Field()
    # 股票名称
    name = Field()
    # 主力净流入净额
    main_influx_price = Field()
    # 主力净流入净占比
    main_influx_ratio = Field()
    # 超大单净流入净额
    huge_influx_price = Field()
    # 超大单净流入净占比
    huge_influx_ratio = Field()
    # 大单净流入净额
    large_influx_price = Field()
    # 大单净流入净占比
    large_influx_ratio = Field()
    # 中单净流入净额
    middle_influx_price = Field()
    # 中单净流入净占比
    middle_influx_ratio = Field()
    # 小单净流入净额
    small_influx_price = Field()
    # 小单净流入净占比
    small_influx_ratio = Field()
    # 数据更新时间
    last_update_time = Field()


class FinancialNoticeItem(Item):
    # 股票代码
    symbol = Field()
    # 股票名称
    name = Field()
    # 股票板块
    sclx = Field()
    # 业绩变动内容
    forecast_content = Field()
    # 预计净利润左部分
    forecast_left = Field()
    # 预计净利润右部分
    forecast_right = Field()
    # 业绩变动幅度左部分
    increase_left = Field()
    # 业绩变动幅度右部分
    increase_right = Field()
    # 业绩变动原因
    change_reason = Field()
    # 预告类型
    preview_type = Field()
    # 上年同期净利润
    previous_year_profit = Field()
    # 所属品种
    hymc = Field()
    # 公告日期
    announcement_date = Field()

class ShareHolderItem(Item):
    # 股票代码
    symbol = Field()
    # 股票名称
    name = Field()
    # 股东名称
    shareholders_name = Field()
    # 增减持
    change_type = Field()
    # 变动数量
    change_share = Field()
    # 变动占总股本比例
    change_equity_ratio = Field()
    # 变动占流通股比例
    change_share_ratio = Field()
    # 持股总数
    total_hold = Field()
    # 占总股本比例
    total_equity_ratio = Field()
    # 持流通股数
    total_share = Field()
    # 占流通股比例
    total_share_ratio = Field()
    # 变动开始日
    begin_date = Field()
    # 变动截止日
    end_date = Field()
    # 公告日期
    announcement_date = Field()

class ShareBuybackItem(Item):
    # 股票代码
    symbol = Field()
    # 股票名称
    name = Field()
    # 最新价
    new_price = Field()
    # 回购价格区间1
    buyback_price_range_left = Field()
    # 回购价格区间2
    buyback_price_range_right = Field()
    # 公告日前一日收盘价
    close_price = Field()
    # 回购数量区间(股)1
    buyback_volumn_range_left = Field()
    # 回购数量区间(股)2
    buyback_volumn_range_right = Field()
    # 占公告前一日流通股份比例(%)1
    share_ratio_left = Field()
    # 占公告前一日流通股份比例(%)2
    share_ratio_right = Field()
    # 占公告前一日总股本比例(%)1
    equity_ratio_left = Field()
    # 占公告前一日总股本比例(%)2
    equity_ratio_right = Field()
    # 回购金额区间(元)1
    buyback_amount_range_left = Field()
    # 回购金额区间(元)2
    buyback_amount_range_right = Field()
    # 回购起始时间
    begin_date = Field()
    # 实施进度
    impl_progress = Field()
    # 公告日期
    announcement_date = Field()

class SharePledgeItem(Item):
    # 股票代码
    symbol = Field()
    # 股票名称
    name = Field()
    # 股东名称
    shareholders_name = Field()
    # 最新质押笔数
    pledge_number = Field()
    # 剩余质押股数(股)
    pledge_volumn = Field()
    # 剩余质押股份市值(元)
    pledge_price = Field()
    # 占所持股份比例(%)
    share_ratio = Field()
    # 占总股本比例(%)
    equity_datio = Field()
    # 平仓线区间(预估）1
    close_position_range_left = Field()
    # 平仓线区间(预估）2
    close_position_range_right = Field()
    # 预警线区间(预估)1
    warning_position_range_left = Field()
    # 预警线区间(预估)2
    warning_position_range_right = Field()
    # 更新日期
    update_date = Field()

class RestrictedItem(Item):
    # 股票代码
    symbol = Field()
    # 股票名称
    name = Field()
    # 解禁时间
    circulation_date = Field()
    # 解禁股东数
    shareholders_num = Field()
    # 解禁数量(股)
    share_num = Field()
    # 实际解禁数量(股)
    real_share_num = Field()
    # 未解禁数量(股)
    non_share_num = Field()
    # 实际解禁市值(元)
    real_share_price = Field()
    # 占总市值比例(%)
    equity_ratio = Field()
    # 占流通市值比例(%)
    share_ratio = Field()
    # 解禁前一日收盘价(元)
    close_price = Field()
    # 限售股类型
    share_type = Field()
    # 解禁前20日涨跌幅(%)
    before_range = Field()
    # 解禁后20日涨跌幅(%)
    after_range = Field()

class AnnouncementItem(Item):
    # 股票代码
    symbol = Field()
    # 股票名称
    name = Field()
    # 公告标题
    announce_title = Field()
    # 公告地址
    announce_url = Field()
    # 公告类型
    announce_type = Field()
    # 公告日期
    announce_date = Field()
    # url的MD5值
    announce_url_md5 = Field()

class CompanyNewItem(Item):
    # 股票代码
    symbol = Field()
    # 股票名称
    name = Field()
    # 新闻标题
    news_title = Field()
    # 新闻地址
    news_url = Field()
    # 发布日期
    date = Field()