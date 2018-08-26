#!/bin/sh

#chkconfig: 123456 90 10
# openerp server for user authentication
workdir=/home/MarketCrawl

spider_start() {
  cd $workdir
  local name=$1
  if [ "$name" != "" ] ; then
      nohup scrapy crawl ${name} >> /dev/null 2>&1 &
      echo "spider ${name} is started."
  else
      echo "spider name is empty."
  fi
}


case "$1" in
G)
  spider_start GridListSpider
;;

M)
  spider_start MainInfluxSpider
;;

F)
  spider_start FinancialNoticeSpider
;;

H)
  spider_start ShareHolderSpider
;;

B)
  spider_start ShareBuybackSpider
;;

P)
  spider_start SharePledgeSpider
;;

R)
  spider_start RestrictedSpider
;;

A)
  spider_start CompanyAnnouncementSpider
;;

N)
  spider_start CompanyNewSpider
;;

*)
  echo "Usage: ./start.sh {G |M |F |H |B |P |R |A |C } {all|newest}"
 exit 1
;;
esac
exit 0

