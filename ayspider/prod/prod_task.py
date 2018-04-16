import time
import datetime
import logging
from .. import utils
from .. import model

class ProducerTask:
    def __init__(self, mq:utils.MQueue, sqlconn:utils.Mysql, gameids = '1,3,4,5,6,7,9',type = None, bat = 1000):
        self._mq = mq
        self._sqlconn = sqlconn
        self._runflag = False
        self._wkey = "task:oppluck:queue"
        self._mincount = 100
        self._batcount = bat
        self._gameids = gameids#2dota 4h1z1js 8steam  1csgo 3,5,6,7,9
        self._type = type
        return

    def start(self):
        self._runflag = True
        self.worker()

    def stop(self):
        self._runflag = False

    def worker(self):
        prevcount = 0
        while self._runflag:
            #get now count
            count = self._mq.view_count(self._wkey)
            if count >= self._mincount:
                logging.info("count:%s prevcount:%s cost:%s", count, prevcount,prevcount - count)
                prevcount = count
                time.sleep(5)
                continue
            #get new task
            newtasks = self.getnewtasks(self._batcount)
            logging.info("newtasks:%s", len(newtasks))
            #add new task
            temptask = []
            namelist = []
            for i in newtasks:
                namelist.append(i.name)
                temptask.append(i)
                if len(temptask) >= 100:
                    self._mq.add_tasks(self._wkey, *namelist)
                    self.settaskstart(temptask)
                    namelist = []
                    temptask = []
            if len(temptask) > 0:
                self._mq.add_tasks(self._wkey, *namelist)
                self.settaskstart(temptask)
            logging.info("addnewtasks:%s", len(newtasks))
            time.sleep(1)
        return

    def getnewtasks(self, count):
        sql = "select id,name from pytask where gameid in (%s) and flag <> 1 and updatetime + intervaltime < %s and starttime + waittime < %s"
        if self._type != None and self._type !=  '':
            sql +=" and type in (%s)"%(self._type) 
        sql += " order by updatetime limit %d"
        nowtime = int(time.mktime(datetime.datetime.utcnow().timetuple()))
        sql = sql%(self._gameids, nowtime, nowtime, self._batcount)
        result = self._sqlconn.fetchall(sql,None)
        tasks = []
        for i in result:
            tasks.append(model.PYTask(id=i['id'],name=i['name']))
        return tasks

    def settaskstart(self, taskList):
        if taskList == None or len(taskList) <=0:
            return
        nowtime = int(time.mktime(datetime.datetime.utcnow().timetuple()))
        ids=''
        for i in taskList:
            if i is None or i.id <=0:
                continue
            ids += str(i.id) + ","
        ids = ids[0:len(ids)-1]
        sql = """UPDATE `pytask` SET `starttime`=%d,`readcount`=`readcount`+1 WHERE id in (%s)"""
        sql = sql%(nowtime,ids)
        result = self._sqlconn.excute(sql,None)