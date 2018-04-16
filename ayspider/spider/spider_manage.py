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
from .. import script
from .. import model

rdata = ''
rdatal = Lock()
mqueue = queue.Queue()
mqueuel = Lock()
mqueuemin = 0

def rdataadd(data):
    global rdata
    if data == None or data == '':
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
    if rdata == None or rdata == '':
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

class SpiderManage(Thread):
    def __init__(self, ips, mq:utils.MQueue=None, wkey='', save:utils.Save=None, bindip=False, blogin=False, accarr=None,savesleep = 10,waittime = 5, optype = 0):
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
        self._waittime = waittime
        self._optype = optype
        return

    def run(self):
        self._runflag = True
        session = None
        if not self._blogin and self._accarr != None:
            session = requests.Session()
            session.headers['User-Agent'] = random.choice(utils.util_config.CONFIG_USERAGENT_PC)
            steamhelper = utils.util_steam.SteamHelper(session)
            resp = utils.util_cfpass.request(session,"get","https://opskins.com/?loc=login")
            logging.info("pass cf success")
            islogin = steamhelper.loginopenid(self._accarr[0].name, self._accarr[0].password)
            logging.info("oplogin start")
            if islogin:
                bhtml = utils.util_cfpass.request(session,"get","https://opskins.com/").content
                html = bhtml.decode('utf-8')
                muid = re.search(r'g_UID\s*=\s*(\d+)',html)
                opskins_csrf_token = session.cookies.get('opskins_csrf_token')
                if muid != None and opskins_csrf_token != None:
                    session.headers['X-OP-UserID'] = muid.group(1)
                    session.headers['X-Requested-With'] = 'XMLHttpRequest'
                    session.headers['X-CSRF'] = opskins_csrf_token
                    session.headers['Cookie'] = '__cfduid=%s;opskins_csrf_token=%s;PHPSESSID=%s;opskins_login_token=%s;opskins_hasLoggedIn=true;'\
                    %(session.cookies.get('__cfduid'),session.cookies.get('opskins_csrf_token'),session.cookies.get('PHPSESSID'),session.cookies.get('opskins_login_token'))
                    islogin = True
                else:
                    islogin = False
            if islogin:
                logging.info("main steam login success")
            else:
                logging.info("main steam login error")

        #start sub thread
        for ip in self._ips:
            account = None
            if self._accarr != None: #islogin and
                for i in self._accarr:
                    if i.ip != ip:
                        continue
                    else:
                        account = i
                        break
            nsession = None
            if session != None:
                nsession = deepcopy(session)
            subth = SpiderTask(ip, session = nsession, blogin = self._blogin,account = account,waittime= self._waittime,optype = self._optype)
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
    def __init__(self, ip="", session:requests.Session=None, blogin = False, account:model.Account = None,waittime = 5,optype =1):
        Thread.__init__(self)
        self._name = ip
        self._ip = ip
        self._blogin = blogin
        self._account = account
        self._bpass = False
        self._runflag = False
        self._performance = None
        self._nonecount = 0
        self._waittime = waittime
        self._optype = optype
        if not session:
            self._session = requests.Session()
            self._session.headers['User-Agent'] = random.choice(utils.util_config.CONFIG_USERAGENT_PC)
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
        needstop = False
        try:
            task = mqueueget() #str(self._mq.get_task_one(self._wkey), encoding='utf-8')
            self._performance.gettask = time.time()
            if task == None:
                logging.info("%s task is null."%(self._ip))
                return success,result,needstop
            m = self.parsetask(task)
            if not m:
                logging.info("%s error task."%(self._ip))
                return success,result,needstop

            itemlist = None 
            success = True;
            if m.group('sid') == '1':
                if self._blogin == False and self._account == None:
                    if self._optype == 1:
                        itemlist, needstop = script._1.search_item(self._session,int(m.group('gid')),m.group('name'))
                    else:
                        itemlist, needstop = script._1_bak.search_item(self._session,int(m.group('gid')),m.group('name'))
                else:
                    needlogin, itemlist, needstop = script._1_2.search_item(self._session,int(m.group('gid')),m.group('name'),ip=self._ip)
                    if needlogin:
                        opskinslogin()

            elif m.group('sid') == '2':
                try:
                    # task2 use <name> as pageindex
                    pageindex = int(m.group('pid'))
                except Exception as ex:
                    logging.error("Task2 pageindex Error%s"%(ex))
                itemlist = script._2.search_stockandprice(self._session,int(m.group('gid')), pageindex)
            elif m.group('sid') == '3':
                itemlist = script._3.search_op_gallp(self._session,int(m.group('gid')))
            elif m.group('sid') == '4':
                itemlist = script._4.search_pricehistory(self._session,int(m.group('gid')),m.group('name'))
            elif m.group('sid') == '5':
                itemlist = script._5.search_opsales(self._session, int(m.group('gid')),m.group('name'))

            self._performance.gethtml = time.time()
            logging.info("%s %s count:%s time:[%.2f]" %(self._ip,task\
                , "None" if itemlist == None else len(itemlist), self._performance.HtmlTime()))
            itemdata = "" if itemlist == None else json.dumps(itemlist, default=lambda o: o.__dict__)
            savedata = model.SaveData(task, itemdata, self._name)#"_%s_%s_%s"%(m.group('gid'),m.group('sid'),m.group('pid'))
            result = json.dumps(savedata.__dict__)
            self._performance.savedata = time.time()
        except Exception as ex:
            logging.error("%s error%s"%(self._ip,ex))
        finally:
            return success,result,needstop
        return success,result,needstop

    def run(self):
        self._bpass = True
        self._runflag = True
        if self._blogin and self._account != None:
            islogin = self.opskinslogin()
            if islogin:
                logging.info("%s steam login success"%(self._ip))
            else:
                logging.error("%s steam login error"%(self._ip))
        elif self._optype == 1:
            if self.opskinspreheaders():
                logging.info("%s op headers set success"%(self._ip))
            else:
                logging.error("%s op headers set faild"%(self._ip))
                
        while self._runflag:
            self._performance = model.Performance(time.time())
            success,result,needstop = self.worker()
            if not success:
                time.sleep(0.5)
                continue
            if result is None:
                self._nonecount += 1
                if self._nonecount >= 10:
                    logging.error("%s nonecount than 10 stop."%(self._ip))
                    break;
            else:
                self._nonecount = 0
            if needstop: #been blocked.
                #logging.error("%s been blocked stop."%(self._ip))
                logging.error("%s been blocked stop,sleep 20 minute."%(self._ip))
                time.sleep(1200)
                continue;
            rdataadd(result)
            sleeptime = self._waittime - self._performance.HtmlTime()
            if sleeptime > 0 and sleeptime <= self._waittime:
                time.sleep(sleeptime)
        return

    def opskinslogin(self):
        if self._blogin == False and self._account == None:
            return False

        steamhelper = utils.util_steam.SteamHelper(self._session)
        resp = utils.util_cfpass.request(self._session,"get","https://opskins.com/?loc=login")
        bakip = self._ip
        try:
            self._ip = None
            islogin = steamhelper.loginopenid(self._account.name, self._account.password)
        finally:
            self._ip = bakip
        if islogin:
            bhtml = utils.util_cfpass.request(self._session,"get","https://opskins.com/").content
            html = bhtml.decode('utf-8')
            muid = re.search('g_UID\s*=\s*(\d+)',html)
            opskins_csrf_token = self._session.cookies.get('opskins_csrf_token')
            if muid != None and opskins_csrf_token != None:
                self._session.headers['X-OP-UserID'] = muid.group(1)
                self._session.headers['X-Requested-With'] = 'XMLHttpRequest'
                self._session.headers['X-CSRF'] = opskins_csrf_token
                self._session.headers['Cookie'] = '__cfduid=%s;opskins_csrf_token=%s;PHPSESSID=%s;opskins_login_token=%s;opskins_hasLoggedIn=true;'\
                %(self._session.cookies.get('__cfduid'),self._session.cookies.get('opskins_csrf_token'),self._session.cookies.get('PHPSESSID'),self._session.cookies.get('opskins_login_token'))
                islogin = True
            else:
                islogin = False
        return islogin

    def opskinspreheaders(self):
        steamhelper = utils.util_steam.SteamHelper(self._session)
        resp = utils.util_cfpass.request(self._session,"get","https://opskins.com/?loc=login")
        bhtml = utils.util_cfpass.request(self._session,"get","https://opskins.com/").content
        html = bhtml.decode('utf-8')
        muid = re.search('g_UID\s*=\s*(\d+)',html)
        opskins_csrf_token = self._session.cookies.get('opskins_csrf_token')
        if muid != None and opskins_csrf_token != None:
            self._session.headers['X-OP-UserID'] = muid.group(1)
            self._session.headers['X-Requested-With'] = 'XMLHttpRequest'
            self._session.headers['X-CSRF'] = opskins_csrf_token
            self._session.headers['Cookie'] = '__cfduid=%s;opskins_csrf_token=%s;PHPSESSID=%s;'\
            %(self._session.cookies.get('__cfduid'),self._session.cookies.get('opskins_csrf_token'),self._session.cookies.get('PHPSESSID'))
            islogin = True
        else:
            islogin = False
        return islogin
        