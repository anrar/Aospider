                                                                                                                                     
import logging
import requests
import time
import json
import queue
from threading import Thread
from threading import Lock
from ayspider.spider.spider_m_temp import SpiderManage
from ayspider import model
from ayspider import utils

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s\t%(message)s")

ips = ['192.168.31.151']
accarr = [model.Account('119.3.4.19','','')]
mq = utils.MQueue()
mq.init_redis(host='47.89.243.179', password ='B7ETm4Heldak')
#wkey = "task:opsales:queue"
wkey = "task:pricehistory:queue"
save = utils.Save('http://127.0.0.1:/coll')
sm = SpiderManage(ips, mq, wkey, save, False, False, None,10)
sm.start()
print('main thread start')

