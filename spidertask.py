                                                                                                                                     
import logging
import requests
import time
import json
import queue
from threading import Thread
from threading import Lock
from ayspider.spider import SpiderManage
from ayspider import model
from ayspider import utils

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="[%(asctime)s][%(thread)d][%(levelname)s]\t%(message)s",datefmt='%m-%d %H:%M')
    fh = logging.FileHandler(filename ="log/"+str(int(time.time()))+".log",mode ="a",encoding = "utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('[%(asctime)s][%(thread)d][%(levelname)s]\t%(message)s'))
    logging.getLogger('').addHandler(fh)

ips = ['119.23.234.19']
accarr = [model.Account('119.23.234.19','','')]
mq = utils.MQueue()
mq.init_redis(host='47.89.243.179', password ='')
#mq.init_redis(host='47.88.220.242')
wkey = "task:oppluck:queue"
save = utils.Save('http://47.88.86.26:14/coll')
sm = SpiderManage(ips, mq, wkey, save, False, False, None,10, 20, 0)
sm.start()
logging.info('main thread start')

