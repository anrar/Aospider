                                                                                                                                     
import logging
import requests
import time
import json
import queue
from threading import Thread
from threading import Lock
from ayspider.spider import SpiderManage2
from ayspider import model
from ayspider import utils

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s\t%(message)s")

ips = ['119.23.234.19']
accarr = [model.Account('119.23.34.19','','')]
mq = utils.MQueue()
mq.init_redis(host='47.88.20.242')
wkey = "task:oppluck:queue"
save = utils.Save('http://127.0.0.1:134/coll')
sm = SpiderManage2(ips, mq, wkey, save, False, False, accarr,10)
sm.start()
print('main thread start')
