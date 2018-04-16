import enum
import time
import json
import logging

from robot import model
from robot import utils
from robot.steampy.client import SteamClient, GameOptions, Asset, TradeOfferState

default_info = {'api_key':'EED222BD0D467C878FA94BFE3A2F1702',
                'steamid':'76561198414064980',
                'shared_secret':'OqFInWnV0xe0blB1G5ywg0x2EiE=',
                'identity_secret':'A0UQuxgCC9AQhbZuXOQKcb+KCiU=',
                'username':'niubility360',
                'password':'qwe789456qwe',
                'trade_url':'https://steamcommunity.com/tradeoffer/new/?partner=453799252&token=kbSUsH5N',
                'is_buyer': False}


def generate_optask(order_id:str, item_lack:list, top_price:str):
    #url 是库存号自己的trade_url
    #steam_id = account_id_to_steam_id(get_key_value_from_url(url, 'partner'))
    app = {}
    for item in item_lack:
        itemkey = '_'.join([item['appid'], item['contextid']])
        if itemkey in app.keys():
            app[itemkey].append({"name":item['item_name'],"amount":item['amount']})
        else:
            app[itemkey] = [{"name":item['item_name'],"amount":item['amount']}]
    return json.dumps([app, {"amounts":len(item_lack),"top_price":top_price,"order_id":order_id}])

class 报价状态(enum.IntEnum):
    无效的 = 1
    交易中 = 2
    已完成 = 3
    讲价 = 4
    已过期 = 5
    已取消 = 6
    被拒绝 = 7
    无效产品 = 8
    需要确认 = 9
    其他因素取消 = 10
    托管中 = 11

class ClientBot():
    def __init__(self, bot_info:dict=default_info, mq:utils.MQueue=None):
        self._api_key = bot_info['api_key']
        self._steamguard_path = '{"steamid": "'+bot_info['steamid']+'","shared_secret": "'+bot_info['shared_secret']+'=","identity_secret": "'+bot_info['identity_secret']+'"}'
        self._username = bot_info['username']
        self._password = bot_info['password']
        self._trade_url = bot_info['trade_url']
        self._is_buyer = bot_info['is_buyer']
        self._mq = mq
        self._wkey = { "order_id":"bot:%s:order_id"%(bot_info['username']), 
               "inventory":"bot:%s:inventory"%(bot_info['username']),
               "opservice":"bot:%s:opservice"%(bot_info['username']),
               "opreceive":"bot:%s:opreceive"%(bot_info['username']),
               "orderhistory":"bot:%s:orderhistory"%(bot_info['username'])}


    def are_credentials_filled(self) -> bool:
        return self._api_key != '' and self._steamguard_path != '' and self._username != '' and self._password != ''


    def login(self):
        try:
            if not self.are_credentials_filled():
                logging.info("bot:%s message hasn't been filled yet"%(self._username))
                return
            self._client = SteamClient(self._api_key)
            self._client.login(self._username, self._password, self._steamguard_path)
            logging.info('bot:%s logged in successfully'%(self._username))
        except Exception as ex:
            logging.error("bot:%s login failed-->%s"%(self._username, ex.args))


    def report_msg(self, order_id:str, msg:str):
        try:
            self._mq.mq_with_locked(self._mq.add_task_one, 'order:callback', (order_id + '_' + msg,))
        except Exception as ex:
            logging.error('report_msg error : %s'%(ex.args))
            return

    def init_inventory(self):
        self._mq.mq_with_locked(self._mq.del_key, self._wkey['inventory'])

        _offer = self._client.get_trade_offers()
        offers_sent = _offer['response']['trade_offers_sent']
        item_active = []
        for offer in offers_sent:
            if len(offer['items_to_give']) > 0 and offer['is_our_offer'] == True:
                for item in offer['items_to_give']:
                    if offer['items_to_give'][item]['tradable'] == True:
                        #把发送中的 产品id 加入 item_active
                        item_active.append(item)
        
        for go in [GameOptions.CS, GameOptions.H1Z1KOTK, GameOptions.PUBG]:
            try:
                my_items = self._client.get_my_inventory(go)
                temp_item = {}
                for my_item in my_items.values():
                    if my_item['id'] not in item_active and my_item['tradable'] == 1:
                        temp_item[my_item['market_name']] = my_item['id'] if my_item['market_name'] not in temp_item.keys() else '_'.join([temp_item[my_item['market_name']], my_item['id']])
                self._mq.add_hashs(self._wkey['inventory'], temp_item)
            except Exception:
                continue

    
    #判断库存是否充足,返回bool以及相应列表
    def is_inventory_enough(self, order_id:str, items:dict):
        item_tradable, items_modify = [], {}
        for item in items:
            item_id, err = self._mq.mq_with_locked(self._mq.get_hash_one, self._wkey['inventory'], (str(item['item_name']).replace('&*&', '\''),))
            if len(err) != 0 or item_id is None or len(str(item_id, encoding='utf-8').split('_')) < int(item['amount']):
                #logging.info('订单:%s 库存号:%s 库存不足'%(order_id, self._username))
                return False, None, None
            item_ids = str(item_id, encoding='utf-8').split('_')
            items_modify[item['item_name']] = '_'.join(item_ids[int(item['amount']):])
            for i in range(int(item['amount'])):
                item_tradable.append(Asset(item_ids[i], GameOptions(item['appid'], item['contextid']), 1))
        #logging.info('订单:%s 库存号:%s 库存满足'%(order_id, self._username))
        return True, item_tradable, items_modify


    #程序主动取消，或接收报价时才能用到；其他情况获取不到market_name
    def update_inventory(self, items):
        if items is None:
            return 
        update = True
        locked, timeout = self._mq.redis_lock(self._wkey['inventory']+'lock')
        if locked:
            try:
                if isinstance(items, dict):
                    for item in items:
                        if items[item]['tradable'] == True:
                            original = self._mq.get_hash_one(self._wkey['inventory'], items[item]['market_name'])
                            if original is None:
                                #某产品本无库存
                                self._mq.add_hash_one(self._wkey['inventory'], items[item]['market_name'], items[item]['id'])
                            else:
                                #修改未报价队列
                                self._mq.add_hash_one(self._wkey['inventory'], items[item]['market_name'], '_'.join([str(original, encoding='utf-8'), items[item]['id']]))
                elif isinstance(items, list) and len(items) != 0 and 'tradable' in items[0].keys():
                    for item in items:
                        if items[item]['tradable'] == 1:
                            original = self._mq.get_hash_one(self._wkey['inventory'], item['market_name'])
                            if original is None:
                                self._mq.add_hash_one(self._wkey['inventory'], item['market_name'], item['id'])
                            else:
                                self._mq.add_hash_one(self._wkey['inventory'], item['market_name'], '_'.join([str(original, encoding='utf-8'), item['id']]))
                else:
                    update = False
            finally:
                self._mq.redis_unlock(self._wkey['inventory']+'lock', timeout)
        if not update:
            logging.error('入库的产品数据无法识别, 重新初始化库存%s'%(self._username))
            self.init_inventory()


    def make_offer(self, order_id:str, url:str, item_tradable:list, items_modify:dict=None, total:str=''):
        res = False
        try:
            offer_result = self._client.make_offer_with_url(item_tradable, [], url, 'thanks')
            if 'strError' in offer_result.keys():
                self.report_msg(order_id, '1_发货出错, '%(self._username))
                logging.error('订单%s发货出错: 库存%s 原因: %s'%(order_id, self._username, offer_result))
                return res
            res = True
            self.report_msg(order_id, '0_已发货: 库存%s, 交易ID:%s, [total:%s]'%(self._username, str(offer_result['tradeofferid']), total))
            #维护一个校验报价接收状态的队列
            self._mq.mq_with_locked(self._mq.add_hash_one, self._wkey['order_id'], (order_id, str(offer_result['tradeofferid']),))
            if items_modify is not None:
                #发送报价成功，修改库存队列
                locked, timeout = self._mq.redis_lock(self._wkey['inventory']+'lock')
                if locked:
                    try:
                        for item_name in items_modify:
                            if items_modify[item_name] == '':
                                self._mq.del_hash_one(self._wkey['inventory'], str(item_name).replace('&*&', '\''))
                            else:
                                self._mq.add_hash_one(self._wkey['inventory'], str(item_name).replace('&*&', '\''), items_modify[item_name])
                    finally:
                        self._mq.redis_unlock(self._wkey['inventory']+'lock', timeout)
                else:
                    logging.error(order_id, '4_已发货但未减少程序库存，可能导致后来订单发送重复产品；需重启程序')
            return res
        except Exception as ex:
            self.report_msg(order_id, '1_发货异常: 库存%s 原因:%s'%(self._username, ex.args))
            logging.error('订单%s发货异常: 库存%s 原因:%s'%(order_id, self._username, ex.args))
            return res


    def cheak_offer(self):
        order_dict, err = self._mq.mq_with_locked(self._mq.get_hash_all,self._wkey['order_id'])
        if len(err) != 0:
            logging.error('获取订单报价异常: %s'%(err))
            return
        for order_id in order_dict:
            tradeofferid = str(order_dict[order_id], encoding='utf-8')
            trade_offer = self._client.get_trade_offer(tradeofferid)
            if len(trade_offer['response']) == 0:
                self.report_msg(str(order_id, encoding='utf-8'), '1_发货出错:丢失,无法查询报价状态')
                self._mq.mq_with_locked(self._mq.del_hash_one, self._wkey['inventory'], (str(order_id, encoding='utf-8'),))
                continue
            trade_offer_state = trade_offer['response']['offer']['trade_offer_state']
            if trade_offer_state == TradeOfferState.Active:
                #客户还未接收报价
                continue
            elif trade_offer_state == TradeOfferState.ConfirmationNeed:
                try:#该报价在发送时 意外没有进行确认报价，在此重新确认发送报价
                    self._client._session.update(self._client._confirm_transaction(tradeofferid))
                except Exception as ex:
                    self.report_msg(str(order_id, encoding='utf-8'), '1_发货出错:报价%s未确认 原因:%s'%(tradeofferid, ex.args))
                    logging.error('订单%s发货出错, 报价%s未确认 原因:%s'%(str(order_id, encoding='utf-8'), tradeofferid, ex.args))
                    continue
            #报价状态不是交易中，都要删除校验队列的order_id
            self._mq.mq_with_locked(self._mq.del_hash_one, self._wkey['order_id'], (str(order_id, encoding='utf-8'),))
            if trade_offer_state in [TradeOfferState.Accepted, TradeOfferState.StateInEscrow]:
                self.report_msg(str(order_id, encoding='utf-8'), '0_对方接受报价, 订单完成')
            else:#剩下情况都是取消报价，产品加回库存(重新初始化库存)
                self.init_inventory()
                self.report_msg(str(order_id, encoding='utf-8'), '1_订单无法完成, %s'%(报价状态(trade_offer_state)))
                #
                #steam报价状态说明 https://developer.valvesoftware.com/wiki/Steam_Web_API/IEconService
                #
                logging.info('订单%s无法完成, %s'%(str(order_id, encoding='utf-8'), 报价状态(trade_offer_state)))


    def is_our_order(self, order_id:str):
        tradeofferid, err = self._mq.mq_with_locked(self._mq.get_hash_one, self._wkey['order_id'], (order_id,))
        if tradeofferid is None:
            return False
        return str(tradeofferid, encoding='utf-8')

    def cancel_offer(self, order_id:str, tradeofferid:str):
        trade_offer = self._client.get_trade_offer(tradeofferid)
        trade_offer_state = trade_offer['response']['offer']['trade_offer_state']
        if trade_offer_state == TradeOfferState.Active:
            self._client.cancel_trade_offer(tradeofferid)
            self._mq.mq_with_locked(self._mq.del_hash_one, self._wkey['orderhistory'], (order_id,))
            self._mq.mq_with_locked(self._mq.del_hash_one, self._wkey['order_id'], (order_id,))
            self.update_inventory(trade_offer['response']['offer']['items_to_give'])
            self.report_msg(order_id, '1_主动取消发货')
            logging.info('订单%s 主动取消发货'%(order_id))


    def accept_offer(self):
        _offer = self._client.get_trade_offers()
        offers_received = _offer['response']['trade_offers_received']
        for offer in offers_received:
            if offer['items_to_give'] == {} and offer['items_to_receive']:
                result = self._client.accept_trade_offer(offer['tradeofferid'])
                if result:
                    logging.info('接收报价%s'%(offer['tradeofferid']))
                    tradeid = json.loads(result.text)
                    item_list = self._client.get_trade_receipt(tradeid['tradeid'])
                    #把收到的产品加入 未报价队列
                    self.update_inventory(item_list)
            else:
                self._client.decline_trade_offer(offer['tradeofferid'])


    def accept_offer_by_id(self, tradeofferid:str):
        trade_offer = self._client.get_trade_offer(tradeofferid)
        trade_offer_state = trade_offer['response']['offer']['trade_offer_state']
        if len(trade_offer['response']) != 0:
            if trade_offer_state == TradeOfferState.Active:
                try:
                    result = self._client.accept_trade_offer(tradeofferid)
                    if result:
                        logging.info('接收报价%s'%(tradeofferid))
                        tradeid = json.loads(result.text)
                        item_list = self._client.get_trade_receipt(tradeid['tradeid'])
                        self.update_inventory(item_list)
                        return True, True
                except Exception as ex:
                    logging.error('接收报价异常: 库存%s 原因:%s'%(self._username, ex.args))
                    return False, False
            elif trade_offer_state == TradeOfferState.Accepted:
                return True, True
        return False, True


    def buy_from_op(self, data:dict):
        try:
            err = ''
            if self._is_buyer and str(data['top_price']).isdigit():
                res, err = self._mq.mq_with_locked(self._mq.add_task_one, self._wkey['opservice'], (generate_optask(data['order_id'], data['items_from_me'], data['top_price']), ))
                if res is not None and res > 0 and err == '':
                    self.report_msg(data['order_id'], '2_购买进行:库存%s'%(self._username))
                    res, err = self._mq.mq_with_locked(self._mq.add_hash_one, self._wkey['orderhistory'], (data['order_id'], json.dumps(data), ))
                    if res is None and len(err) != 0:
                        self.report_msg(data['order_id'], '1_订单缓存失败, 将无法发货 原因:%s'%(err))
                        logging.error('订单%s 缓存失败, 将无法发货 原因:%s'%(data['order_id'], err))
                    return True
                raise Exception(err)
        except Exception as ex:
            self.report_msg(data['order_id'], '1_购买失败:%s'%(ex.args))
            logging.error('订单%s 库存%s 购买失败 原因:%s'%(data['order_id'], self._username, ex.args))
            return False


    