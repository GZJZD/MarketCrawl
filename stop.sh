#!/bin/sh

#chkconfig: 123456 90 10
# openerp server for user authentication
workdir=/home/MarketCrawl

spider_stop() {
  cd $workdir
  local name=$1
  if [ "$name" != "" ] ; then
      pids=($(ps -ef | grep "scrapy crawl ${name}"|grep -v grep | awk '{ print $2 }'))
      echo ${pids[@]}
	  for pid in ${pids[@]}; do kill $pid; done
	  sleep 2
	  echo "spider ${name} is killed."
  else
      echo "spider name is empty."
  fi
}

case "$1" in
G)
  spider_stop GridListSpider
;;

M)
  spider_stop MainInfluxSpider
;;

F)
  spider_stop FinancialNoticeSpider
;;

H)
  spider_stop ShareHolderSpider
;;

B)
  spider_stop ShareBuybackSpider
;;

P)
  spider_stop SharePledgeSpider
;;

R)
  spider_stop RestrictedSpider
;;

A)
  spider_stop CompanyAnnouncementSpider
;;

N)
  spider_stop CompanyNewSpider
;;

*)
  echo "Usage: ./stop.sh {G |M |F |H |B |P |R |A |C }"
 exit 1
;;
esac
exit 0

