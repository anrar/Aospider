
import time
import logging
from ..utils import *

class Producer:
    def __init__(self, mq:MQueue, sqlconn:Mysql, gameids = '1,3,4,5,6,7,9', bat = 1000):
        self._mq = mq
        self._sqlconn = sqlconn
        self._runflag = False
        self._wkey = "task:pricehistory:queue"
        self._mincount = 1
        self._batcount = bat
        self._gameids = gameids#2dota 4h1z1js 8steam  1csgo 3,5,6,7,9
        return

    def start(self):
        self._runflag = True
        self.worker()

    def stop(self):
        self._runflag = False

    def worker(self):
        prevcount = 0
        index = 0
        while self._runflag:
            #get now count
            count = self._mq.view_count(self._wkey)
            if count > self._mincount:
                logging.info("count:%s prevcount:%s cost:%s", count, prevcount,prevcount - count)
                prevcount = count
                time.sleep(10)
                continue
            #get new task
            newtasks = self.getnewtasks(index,self._batcount)
            index = index + self._batcount
            if newtasks.count == 0: 
                logging.info("job has been Done")
                return 
            logging.info("newtasks:%s", len(newtasks))
            #add new task
            temptask = []
            for i in newtasks:
                temptask.append(i)
                if len(temptask) >= 100:
                    self._mq.add_tasks(self._wkey, *temptask)
                    temptask = []
            if len(temptask) > 0:
                self._mq.add_tasks(self._wkey, *temptask)
            logging.info("addnewtasks:%s", len(newtasks))
            time.sleep(10)
        return

    def getnewtasks(self, start:int, count:int):
#        sql = """select pro.id,pro.gameid,pro.name
#from product as pro join productprice as pri on pro.id = pri.id
#where pro.gameid in (%s) and flag <> 1 order by pri.updatetime limit %s"""
        sql = """select id,gameid,name from product where gameid in (%s) and flag <> 1 limit %d,%d"""
        sql = sql%(self._gameids,start,count)
        logging.info(sql)
        result = self._sqlconn.fetchall(sql,None)
        tasks = []
        for i in result:
            tasks.append("_%s_%s_%s_%s"%(i['gameid'], 4, i['id'], i['name']))
        return tasks