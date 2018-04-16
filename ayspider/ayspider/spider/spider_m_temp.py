# _*_ coding: utf-8 _*_

import logging
import requests
import time
import json
import queue
import random
import re
from copy import deepcopy
from threading import Thread
from threading import Lock
from .. import utils
from ..script import _1, _2, _3, _4, _5
from .. import model

rdata = ''
rdatal = Lock()
mqueue = queue.Queue()
mqueuel = Lock()
mqueuemin = 0

def rdataadd(data):
    global rdata
    if data == '' or data is None:
        return None
    if not rdatal.acquire(1):
        return None
    try:
        rdata = rdata + data + '\n\n'
    finally:
        rdatal.release()
    return True

def rdatasubmit(save:utils.Save):
    global rdata
    if rdata == '':
        return None
    if not rdatal.acquire(1):
        return None
    try:
        result = save.submit(rdata)
        rdata = ''
    finally:
        rdatal.release()
    logging.debug("rdata submit:%s"%(result))
    return True

def mqueueget():
    global mqueue
    if mqueue.qsize() <= 0:
        return None
    if not mqueuel.acquire(1):
        return None
    try:
        task = mqueue.get(False)
    finally:
        mqueuel.release()
    return task

def mqueuefill(mq:utils.MQueue,wkey:str):
    global mqueue
    if mqueue.qsize() >= mqueuemin:
        time.sleep(1)
        return None

    if not mqueuel.acquire(1):
        return None
    try:
        task = None
        taskb = mq.get_task_one(wkey)
        if taskb != None:
            task = str(taskb, encoding='utf-8')
        if task != "" and task != None:
            mqueue.put(task)
        else:
            time.sleep(5)#task null wait
    finally:
        mqueuel.release()
    return mqueue.qsize()

class tSpiderManage(Thread):
    def __init__(self, ips, mq:utils.MQueue=None, wkey='', save:utils.Save=None, bindip=False, blogin=False, accarr=None,savesleep = 10):
        Thread.__init__(self)
        global mqueuemin
        self._ips = ips
        mqueuemin = len(self._ips)
        self._mq = mq
        self._wkey = wkey
        self._save = save
        self._bindip = bindip
        if self._bindip:
            utils.bindipbythread()
        self._blogin = blogin
        self._accarr = accarr
        self._runflag = False
        self._savesleep = savesleep
        self._starttime = 0.0
        return

    def run(self):
        self._runflag = True
        session = None
        if not self._blogin and self._accarr != None:
            session = requests.Session()
            headers = { 'User-Agent' : random.choice(utils.util_config.CONFIG_USERAGENT_PC)}
            session.headers = headers
            steamhelper = utils.util_steam.SteamHelper(session)
            resp = utils.util_cfpass.request(session,"get","https://opskins.com/?loc=login")
            islogin = steamhelper.loginopenid(self._accarr[0].name, self._accarr[0].password)
            if islogin:
                logging.info("main steam login success")
            else:
                logging.info("main steam login error")

        #start sub thread
        for ip in self._ips:
            account = None
            if self._blogin and self._accarr != None:
                for i in self._accarr:
                    if i.ip != ip:
                        continue
                    else:
                        account = i
                        break
            nsession = None
            if session != None:
                nsession = deepcopy(session)
            subth = SpiderTask(ip, session = nsession, blogin = self._blogin,account = account)
            subth.start()
            logging.info("thread:% start"%(ip))

        #manage mq and th
        old = int(time.time()) + self._savesleep
        while self._runflag:
            try:
                #self._starttime = time.time()
                mqueuefill(self._mq,self._wkey)
                if int(time.time()) > old:
                    old = int(time.time()) + self._savesleep
                    rdatasubmit(self._save)
                #logging.info("main speed:[%s] [%s]"%(time.time() - self._starttime, self._starttime))
            except Exception as ex:
                logging.error("error%s"%(ex))
        return

    def stop(self):
        self._runflag = False

class SpiderTask(Thread):
    def __init__(self, ip="", session:requests.Session=None, blogin = False, account:model.Account = None):
        Thread.__init__(self)
        self._name = ip
        self._ip = ip
        self._blogin = blogin
        self._account = account
        self._bpass = False
        self._runflag = False
        self._performance = None
        if not session:
            self._session = requests.Session()
            headers = { 'User-Agent' : random.choice(utils.util_config.CONFIG_USERAGENT_PC)}
            self._session.headers = headers
        else:
            self._session = session

    def parsetask(self, task):
        if task is "":
            return None
        pattern = re.compile('_(?P<gid>\d+)_(?P<sid>\d+)_(?P<pid>\d+)_(?P<name>[^^]+)')
        return pattern.search(task)

    def worker(self):
        success = False
        result = None
        try:
            task = mqueueget() #str(self._mq.get_task_one(self._wkey), encoding='utf-8')
            self._performance.gettask = time.time()
            if task == None:
                logging.info("%s task is null."%(self._ip))
                return success,result
            m = self.parsetask(task)
            if not m:
                logging.info("%s error task."%(self._ip))
                return success,result

            itemlist = None 
            success = True;
            if m.group('sid') == '1':
                itemlist = _1.search_item(self._session,int(m.group('gid')),m.group('name'))
            elif m.group('sid') == '2':
                try:
                    # task2 use <name> as pageindex
                    pageindex = int(m.group('pid'))
                except Exception as ex:
                    logging.error("Task2 pageindex Error%s"%(ex))
                itemlist = _2.search_stockandprice(self._session,int(m.group('gid')), pageindex)
            elif m.group('sid') == '3':
                itemlist = _3.search_op_gallp(self._session,int(m.group('gid')))
            elif m.group('sid') == '4':
                itemlist = _4.search_pricehistory(self._session,int(m.group('gid')),m.group('name'))
            elif m.group('sid') == '5':
                itemlist = _5.search_opsales(self._session, int(m.group('gid')),m.group('name'))

            self._performance.gethtml = time.time()
            logging.info("%s %s count:%s" %(self._ip, m.group('name'), "None" if itemlist == None else len(itemlist)))
            itemdata = "" if itemlist == None else json.dumps(itemlist, default=lambda o: o.__dict__)
            savedata = model.SaveData(task, itemdata, self._name)#"_%s_%s_%s"%(m.group('gid'),m.group('sid'),m.group('pid'))
            result = json.dumps(savedata.__dict__)
            self._performance.savedata = time.time()
        except Exception as ex:
            logging.error("%s error%s"%(self._ip,ex))
        finally:
            return success,result
        return success,result

    def run(self):
        self._bpass = True
        self._runflag = True
        islogin = False
        if self._blogin and self._account != None:
            #do login op
            steamhelper = utils.util_steam.SteamHelper(self._session)
            resp = utils.util_cfpass.request(self._session,"get","https://opskins.com/?loc=login")
            islogin = steamhelper.loginopenid(self._account.name, self._account.password)
        if islogin is None or islogin == False:
            logging.info("%s steam login error"%(self._ip))     
            headers = {
                'Content-Type':	'application/x-www-form-urlencoded; charset=UTF-8',
                'Cookie': 'opskins_csrf_token=28N3PzVJAZDLdjwgudmPcY3tofaUWhWPb;',
                'X-CSRF': '28N3PzVJAZDLdjwgudmPcY3tofaUWhWPb',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
                'X-Requested-With':'XMLHttpRequest'
                }
            self._session.headers.update(headers)
        else:
            logging.info("%s steam login success"%(self._ip))
        while self._runflag:
            self._performance = model.Performance(time.time())
            success,result = self.worker()
            if not success:
                time.sleep(0.5)
                continue
            rdataadd(result)
            self._performance.endtime = time.time()
            logging.info("%s performance[%d]:task[%.2f] html[%.2f] save[%.2f] all[%.2f]"%(self._ip\
                ,self._performance.starttime\
                ,self._performance.TaskTime()\
                ,self._performance.HtmlTime()\
                ,self._performance.SaveTime()\
                ,self._performance.CountTime()))
        return