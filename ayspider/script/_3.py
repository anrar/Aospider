import re
import json
import requests
from requests.sessions import Session


# using opskinsAPI method : GetAllLowestListPrices v1
def search_op_gallp(session:Session, gameid:int ):
    if gameid is None:
        return
    url = init_url(gameid)
    if url is None:
        return
    bcontent = session.get(url).content
    result = json.loads(bcontent.decode('utf-8'))
    if result["status"] != 1:
        return False

    res = []
    response = result["response"]
    for key in response:
        osp = OpStockPrice()
        osp.init_spi(key, response[key]["price"]/100, response[key]["quantity"])
        res.append(osp)
    return res


def init_url(gameid:int):
    url = 'https://api.opskins.com/IPricing/GetAllLowestListPrices/v1/'
    if gameid == 1: #csgo
        url += '?appid=730'
    elif gameid == 2: #dota2
        url += '?appid=570'
    elif gameid == 3: #tf 2
        url += '?appid=440'
    elif gameid == 4: #h1z1 js
        url += '?appid=295110'
    elif gameid == 5: #h1z1 kotk
        url += '?appid=433850'
    elif gameid == 6: #psb
        url += '?appid=578080'
    elif gameid == 7: #rust
        url += '?appid=252490'
    elif gameid == 9: #unturned
        url += '?appid=304930'
    else:
        return
    return url

class OpStockPrice(object):
    def __init__(self):
        self.SName = ''
        self.Quantity = ''
        self.Price = ''

    def init_spi(self, key, price, stock):
        # cheak verity
        self.SName = key
        self.Quantity = stock
        self.Price = price