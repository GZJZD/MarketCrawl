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
 {
   if [ "$2" == "newest" ] ; then
     spider_start 'CompanyAnnouncementSpider -a mode=newest'
   elif [ "$2" == "period" ] ; then
      spider_start 'CompanyAnnouncementSpider -a mode=period'
   else
      spider_start 'CompanyAnnouncementSpider'
   fi
 }
;;

N)
 {
   if [ "$2" == "newest" ] ; then
     spider_start 'CompanyNewSpider -a mode=newest'
   elif [ "$2" == "period" ] ; then
      spider_start 'CompanyNewSpider -a mode=period'
   else
      spider_start 'CompanyNewSpider'
   fi
 }
  spider_start CompanyNewSpider
;;

*)
  echo "Usage: ./start.sh {G |M |F |H |B |P |R |A |C } {all| period| newest}"
 exit 1
;;
esac
exit 0

