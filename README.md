# 爬虫开发指南
## 数据来源
* 基本指标
```sh
# url
http://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx

# 参数
?cb=jQuery112402081770324259753_1534163735689
&type=CT
&token=4f1862fc3b5e77c150a2b985b12db0fd
&sty=FCOIATC
&js=(%7Bdata%3A%5B(x)%5D%2CrecordsFiltered%3A(tot)%7D)
&cmd=C._A
&st=(ChangePercent)
&sr=-1
&p=2
&ps=20
&_=1534163735696
```

* 主力流入
```sh
# url
http://ff.eastmoney.com//EM_CapitalFlowInterface/api/js

# 参数
?type=hff
&rtntype=2
&js={data:[(x)]}
&cb=var%20aff_data=
&check=TMLBMSPROCR
&acces_token=1942f5da9b46b069953c873404aad4b5
&id=0000632
&_=1534217118028
```

* 财报披露
```sh
# url
http://data.eastmoney.com/bbsj/600096.html
```

* 股东增减持
```sh
# url
http://data.eastmoney.com/DataCenter_V3/gdzjc.ashx

# 参数
?pagesize=50
&page=2
&js=var%20upbBBTdP
&param=
&sortRule=-1
&sortType=BDJZ
&tabid=all
&code=
&name=
&rt=51130247
```

* 股票回购
```sh
# url
http://api.dataide.eastmoney.com/data/gethglist

# 参数
?pageindex=2
&pagesize=50
&orderby=dim_date
&order=desc
&jsonp_callback=var%20klzuugWP=(x)
&market=(0,1,2,3)
&rt=51135425
```


* 股权质押
```sh
# url
http://api.dataide.eastmoney.com/data/GDZY_GD_SUM

# 参数
?pageindex=1
&pagesize=500
&orderby=updatedate
&order=desc
&jsonp_callback=var%20GRjicuBd=(x)
&rt=51135446
```

* 限售解禁
```sh
# url
http://dcfm.eastmoney.com/em_mutisvcexpandinterface/api/js/get

# 参数
?token=70f12f2f4f091e459a279469fe49eca5
&st=ltsj
&sr=-1
&p=1
&ps=500
&type=XSJJ_NJ_PC
&js=var%20NQkceaOS={pages:(tp),data:(x)}
&filter=(gpdm=)
&rt=51135483
```

* 公司公告
```sh
# url
https://xueqiu.com/statuses/stock_timeline.json

# 参数
?symbol_id=SH600519  #股票类型+股票代码构成KEY，1代表SH，表示上交所，2代表SZ，表示深交所
&count=10
&source=%E5%85%AC%E5%91%8A #‘公告’的UTF-8编码，表示查询的是公告
&page=1
```

* 公司新闻
```sh
# url
https://xueqiu.com/statuses/stock_timeline.json

# 参数
?symbol_id=SH600519
&count=10
&source=%E8%87%AA%E9%80%89%E8%82%A1%E6%96%B0%E9%97%BB
&page=1
```

## 框架简介
基于`python`的`scrapy`框架来开发爬虫，爬取的数据持久化至`mysql`数据库，再由`web`应用完成查询和展示。

### 运行依赖
```sh
[root@master ~]# python -V
Python 2.7.5

[root@master ~]# pip list
Package                      Version
---------------------------- -----------
chardet                      3.0.4
demjson                      2.2.4
fake-useragent               0.1.10
gevent                       1.3.6
lxml                         3.2.1
psutil                       5.4.7
PyMySQL                      0.9.2
pyOpenSSL                    18.0.0
pysqlite                     2.8.3
pytz                         2018.5
requests                     2.10.0
Scrapy                       1.5.1
SQLAlchemy                   1.2.11
Twisted                      18.7.0
web.py                       0.39
```

### 技术问题
#### 动态页面
* 抓包工具分析`js,ajax`的请求，模拟该请求获取js加载后的数据
* Spynner + PyQt4.QtWebKit内核
* Selenium + phantomjs模拟操作

**我们采用的是第一种方式，构造js请求获取数据后进行解析**

#### IP限制
网站的防火墙会对某个固定ip在某段时间内请求的次数做限制，超过了则拒绝请求或是弹出一些类似于**验证码、滑动块**的交互页面，后台爬取时机器和ip有限，很容易达到上线而导致请求被拒绝。目前主要的应对方案是使用代理，这样一来ip的数量就会多一些，但代理ip依然有限，对于这个问题，根本不可能彻底解决。

* Go-Agent：较成熟，但提供的IP均是透明的，雪球网反爬会屏蔽。
* IPProxyPool：爬取免费代理的开源实现，不稳定，但提供的IP有匿名和高匿的，可绕过雪球网反爬，其具体实现参见项目文档`https://github.com/GZJZD/IPProxyPool`

**我们采用的是基于IPProxyPool进行若干修改的方案**

#### User-Agent
网站后台通常会通过此字段判断用户设备类型、系统以及浏览器的型号版本。我们可以设置为浏览器的`User-Agent`来避免被拒绝链接。

**我们采用的是三方包fake-useragent来随机生成ua**

#### Cookie
一般在用户登录或者某些操作后，服务端会在返回包中包含`Cookie`信息要求浏览器设置`Cookie`，没有`Cookie`会很容易被辨别出来是伪造请求。

**我们需要爬取的数据源中，雪球网有Cookie检查，不过比较简单，只需要登录一次主页获取Cookie即可**

#### 数据维护
随着爬虫运行时间的推移，爬取到的数据会越来越多，云端ECS主机的存储空间有限，需要定期清理历史数据

**TODO**

## 代码目录
```sh
panhongfa@DESKTOP-TH8I1NC /cygdrive/e/works/gerapy/projects/MarketCrawl
$ tree ./
./
|-- crontab.conf    # crond.service配置
|-- MarketCrawl
|   |-- __init__.py
|   |-- __pycache__
|   |   |-- __init__.cpython-37.pyc
|   |   `-- settings.cpython-37.pyc
|   |-- items.py         # 采集数据项定义
|   |-- logger.py
|   |-- main.py          # 调试启动入口
|   |-- middlewares.py   # UA与proxy中间件实现
|   |-- pipelines.py     # 数据持久化实现
|   |-- settings.py      # 全局配置
|   `-- spiders          # 爬虫实现
|       |-- __init__.py
|       |-- __pycache__
|       |   |-- __init__.cpython-37.pyc
|       |   `-- GridListSpider.cpython-37.pyc
|       |-- CompanyAnnouncementSpider.py
|       |-- CompanyNewSpider.py
|       |-- FinancialNoticeSpider.py
|       |-- GridListSpider.py
|       |-- MainInfluxSpider.py
|       |-- RestrictedSpider.py
|       |-- ShareBuybackSpider.py
|       |-- ShareHolderSpider.py
|       `-- SharePledgeSpider.py
|-- README.md
|-- scrapy.cfg          # scrapy配置
|-- start.sh            # 后台服务启动脚本
`-- stop.sh             # 停止后台服务脚本
5 directories, 27 files
```

## 部署与调度
### 云端部署
```sh
云端ECS主机
ip: 47.52.77.50
用户: root
密码: jzt@2018

Mysql数据库
ip: localhost
用户: root
密码: 1
```

```sh
cd /home

git clone git@github.com:GZJZD/IPProxyPool.git
git clone git@github.com:GZJZD/MarketCrawl.git
```

### 定时调度
定时调度采用`crond.service`服务来实现，其配置文件内容如下
```sh
SHELL=/bin/bash
PATH=/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=root

# For details see man 4 crontabs

# Example of job definition:
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  * user-name  command to be executed

*/5  7-22 * * * root /home/MarketCrawl/start.sh G
*/30 7-22 * * * root /home/MarketCrawl/start.sh M

00 7-22/1 * * * root /home/MarketCrawl/start.sh F
10 7-22/1 * * * root /home/MarketCrawl/start.sh H
20 7-22/1 * * * root /home/MarketCrawl/start.sh B
30 7-22/1 * * * root /home/MarketCrawl/start.sh P
40 7-22/1 * * * root /home/MarketCrawl/start.sh R

00 */4 * * * root /home/MarketCrawl/start.sh A newest
50 */4 * * * root /home/MarketCrawl/start.sh C newest

00 8 * * 6-7 root /home/MarketCrawl/start.sh A period
00 14 * * 6-7 root /home/MarketCrawl/start.sh C period

00 00 1 * * root /home/MarketCrawl/start.sh A all
00 00 1 * * root /home/MarketCrawl/start.sh C all

#Usage: ./start.sh {G |M |F |H |B |P |R |A |C } {all| period| newest}
```
