# MarketCrawl
股票信息爬虫

# 爬虫列表
## 基本指标
### url分解
http://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx

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

### url测试
http://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx?cb=jQuery&type=CT&token=4f1862fc3b5e77c150a2b985b12db0fd&sty=FCOIATC&js=(%7Bdata%3A%5B(x)%5D%2CrecordsFiltered%3A(tot)%7D)&cmd=C._A&st=(ChangePercent)&sr=-1&p=1&ps=50&_=1534163735696


## 主力流入
### url分解
http://ff.eastmoney.com//EM_CapitalFlowInterface/api/js

?type=hff
&rtntype=2
&js={data:[(x)]}
&cb=var%20aff_data=
&check=TMLBMSPROCR
&acces_token=1942f5da9b46b069953c873404aad4b5
&id=0000632
&_=1534217118028

### url测试
http://ff.eastmoney.com//EM_CapitalFlowInterface/api/js?type=hff&rtntype=2&js={data:[(x)]}&cb=var%20aff_data=&check=TMLBMSPROCR&acces_token=1942f5da9b46b069953c873404aad4b5&id=0000632&_=1534296977822


## 财报披露
### url分解
http://data.eastmoney.com/bbsj/600096.html


## 股东增减持
### url分解
http://data.eastmoney.com/DataCenter_V3/gdzjc.ashx
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


### 查询单股票
http://data.eastmoney.com/DataCenter_V3/gdzjc.ashx?pagesize=50&page=1&js=var%20gHhJMGOC&param=&sortRule=-1&sortType=BDJZ&tabid=all&code=600519&name=&rt=51146585

### 批量查询所有股票
http://data.eastmoney.com/DataCenter_V3/gdzjc.ashx?pagesize=50&page=1&js=var%20upbBBTdP&param=&sortRule=-1&sortType=BDJZ&tabid=all&code=&name=&rt=51130247

## 股票回购
### url分解
http://api.dataide.eastmoney.com/data/gethglist
?pageindex=2
&pagesize=50
&orderby=dim_date
&order=desc
&jsonp_callback=var%20klzuugWP=(x)
&market=(0,1,2,3)
&rt=51135425

### url测试
http://api.dataide.eastmoney.com/data/gethglist?pageindex=2&pagesize=50&orderby=dim_date&order=desc&jsonp_callback=var%20klzuugWP=(x)&market=(0,1,2,3)&rt=51135425


## 股权质押
### url分解
http://api.dataide.eastmoney.com/data/GDZY_GD_SUM?pageindex=1&pagesize=50&orderby=updatedate&order=desc&jsonp_callback=var%20GRjicuBd=(x)&scode=002123&rt=51135446

直接查询所有的
http://api.dataide.eastmoney.com/data/GDZY_GD_SUM
?pageindex=1
&pagesize=500
&orderby=updatedate
&order=desc
&jsonp_callback=var%20GRjicuBd=(x)
&rt=51135446

### url测试
http://api.dataide.eastmoney.com/data/GDZY_GD_SUM?pageindex=1&pagesize=100&orderby=updatedate&order=desc&jsonp_callback=var%20GRjicuBd=(x)&rt=51135446


## 限售解禁
### url分解
http://dcfm.eastmoney.com/em_mutisvcexpandinterface/api/js/get?token=70f12f2f4f091e459a279469fe49eca5&st=ltsj&sr=-1&p=1&ps=50&type=XSJJ_NJ_PC&js=var%20NQkceaOS={pages:(tp),data:(x)}&filter=(gpdm=%27300323%27)&rt=51135483

直接查询所有的
http://dcfm.eastmoney.com/em_mutisvcexpandinterface/api/js/get
?token=70f12f2f4f091e459a279469fe49eca5
&st=ltsj
&sr=-1
&p=1
&ps=500
&type=XSJJ_NJ_PC
&js=var%20NQkceaOS={pages:(tp),data:(x)}
&filter=(gpdm=)
&rt=51135483

### url测试
http://api.dataide.eastmoney.com/data/GDZY_GD_SUM?token=70f12f2f4f091e459a279469fe49eca5&st=ltsj&sr=-1&p=1&ps=300&type=XSJJ_NJ_PC&js=var%20ETGaGXFB={pages:(tp),data:(x)}&filter=(gpdm=)&rt=1534160756415


## 公司公告
### url分解
https://xueqiu.com/statuses/stock_timeline.json
?symbol_id=SH600519  #股票类型+股票代码构成KEY，1代表SH，表示上交所，2代表SZ，表示深交所
&count=10
&source=%E5%85%AC%E5%91%8A #‘公告’的UTF-8编码，表示查询的是公告
&page=1


## 公司新闻
### url分解
https://xueqiu.com/statuses/stock_timeline.json?symbol_id=SH600519&count=10&source=%E8%87%AA%E9%80%89%E8%82%A1%E6%96%B0%E9%97%BB&page=1
