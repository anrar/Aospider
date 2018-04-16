
import re
import time
import json
import logging
from threading import Thread
from robot import utils
from robot.robot.client_bot import ClientBot

def get_appid_contextid(game:str):
    ids = []
    if game in ["All Server", "CSGO"]:
        ids = ["730","2"]
    elif game == "PRK BG":
        ids = ["578080","2"]
    elif game == "H1Z1 KotK":
        ids = ["433850","1"]
    elif game == "H1Z1 JS":
        ids = ["295110","1"]
    #elif game == "Rust":
    #    ids = ["252490","2"]
    elif game == "TF2":
        ids = ["440","2"]
    elif game == "Dota 2":
        ids = ["570","2"]
    return ids


def parse_taskstr(task:str):
    data = json.loads(task)
    ndata = {}
    ndata['order_id'] = data['OrderID']
    ndata['trade_offer_url'] = data['TraderUrl']
    ndata['top_price'] = data['Total']
    ndata['items_from_me'] = []
    a_c_id = get_appid_contextid(data['Game'])
    if len(a_c_id) == 0:
        logging.error('订单%s Game【%s】 not exist'%(data['OrderID'], data['Game']))
        return None
    for item in data['ItemList']:
        ndata['items_from_me'].append({"item_name":item['name'],"appid":a_c_id[0],"contextid":a_c_id[1],"amount":item['amount']})
    return json.dumps(ndata)


class ManagerBot(Thread):
    def __init__(self, bot_infos:list, mq:utils.MQueue=None, wkey:str="order:sent"):
        Thread.__init__(self)
        self._bot_infos = bot_infos
        self._mq = mq
        self._wkey = wkey
        self._bots = []
        self._runflag = False

    def init_bot(self, bot_infos:list):
        for bot_info in bot_infos:
            cb = ClientBot(bot_info, self._mq)
            cb.login()
            if cb._client.was_login_executed:
                cb.init_inventory()
                self._bots.append(cb)


    def run(self):
        self._runflag = True
        self.init_bot(self._bot_infos)
        for cb in self._bots:
            checkoffer = CheckOffer(cb)
            checkoffer.start()

        while self._runflag:
            try:
                task = self._mq.get_task_one(self._wkey)
                if task is None:
                    time.sleep(4.5)
                    continue

                pattern = re.compile('(?P<tid>\d+)_(?P<content>.*)')
                m = pattern.search(str(task, encoding='utf-8'))
                if not m:
                    raise Exception("该任务无法解析成功 %s"%(str(task, encoding='utf-8')))
                    continue

                if m.group('tid') == '01':
                    data = json.loads(parse_taskstr(m.group('content')))
                    if data is None:
                        continue
                    done = False
                    for cb in self._bots:
                        flag, item_tradable, items_modify = cb.is_inventory_enough(data['order_id'], data['items_from_me'])
                        if flag:
                            if not cb._client.is_session_alive():
                                cb.login()
                            done = cb.make_offer(data['order_id'], data['trade_offer_url'], item_tradable, items_modify)
                            break
                    if not done:
                        for cb in self._bots:
                            if cb._is_buyer and cb.buy_from_op(data):
                                break

                elif m.group('tid') == '02':
                    order_id = m.group('content')
                    if order_id is None:
                        continue
                    done = False
                    for cb in self._bots:
                        tradeofferid = cb.is_our_order(order_id)
                        if tradeofferid is not False:
                            if not cb._client.is_session_alive():
                                cb.login()
                            cb.cancel_offer(order_id, tradeofferid)
                            done = True
                            break
                    if not done:
                        self._mq.mq_with_locked(self._mq.add_task_one, 'order:callback', (order_id + '_3_订单不在处理程序中',))
            except Exception as ex:
                logging.error('manager error: %s'%(ex.args))
                continue
            finally:
                time.sleep(0.5)
              

    def stop(self):
        self._runflag = False


class CheckOffer(Thread):
    def __init__(self, client:ClientBot):
        Thread.__init__(self)
        self._cbot = client

    def run(self):
        n = 0
        while True:
            try:
                #每99*3s校验一次; 每3秒查看购买号有没有反馈消息，有则处理
                if n > 99:
                    n = 0
                    if not self._cbot._client.is_session_alive():
                        self._cbot.login()
                    self._cbot.cheak_offer()
                    self._cbot.accept_offer()
                n += 1
                time.sleep(3)

                if self._cbot._is_buyer:
                    tasks = self._cbot._mq.get_hash_all(self._cbot._wkey['opreceive'])
                    if len(tasks) == 0:
                        continue
                    if not self._cbot._client.is_session_alive():
                        self._cbot.login()

                    for task in tasks:
                        order_id = str(task, encoding='utf-8')
                        tradeofferid_total = str(tasks[task], encoding='utf-8').split('_')
                        tradeofferid = tradeofferid_total[0]
                        #购买失败则tradeofferid == 'false'
                        if tradeofferid == 'false':
                            logging.info('订单%s %s'%(order_id, tradeofferid_total[1]))
                            self._cbot._mq.del_hash_one(self._cbot._wkey['opreceive'], order_id)
                            self._cbot._mq.del_hash_one(self._cbot._wkey['orderhistory'], order_id)
                        else:
                            #购买成功 则可获取 购买成本total
                            total = tradeofferid_total[1]
                            
                            time.sleep(2) #给时间op withdraw
                            is_accept, is_del_task = self._cbot.accept_offer_by_id(tradeofferid)
                            if is_del_task:
                                self._cbot._mq.del_hash_one(self._cbot._wkey['opreceive'], order_id)
                            if is_accept:
                                task, err = self._cbot._mq.mq_with_locked(self._cbot._mq.get_hash_one, self._cbot._wkey['orderhistory'], (order_id,))
                                if task is None:
                                    continue
                                data = json.loads(str(task, encoding='utf-8'))
                                flag, item_tradable, items_modify = self._cbot.is_inventory_enough(data['order_id'], data['items_from_me'])
                                if flag and self._cbot.make_offer(data['order_id'], data['trade_offer_url'], item_tradable, items_modify, total):
                                    self._cbot._mq.del_hash_one(self._cbot._wkey['orderhistory'], order_id)
                                else:
                                    self._cbot._mq.mq_with_locked(self._cbot._mq.add_task_one, 'order:callback', (order_id + '_1_订单处理失败',))
                            elif is_del_task:
                                self._cbot._mq.mq_with_locked(self._cbot._mq.add_task_one, 'order:callback', (order_id + '_1_订单处理失败',))
                                self._cbot._mq.del_hash_one(self._cbot._wkey['orderhistory'], order_id)
            except Exception as ex:
                logging.error('client:%s 报出异常: %s'%(self._cbot._username, ex.args))
                time.sleep(3)
                continue
