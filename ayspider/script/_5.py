import re
import logging
from requests.sessions import Session
import json
import requests
import copy


def search_opsales(session:requests.Session(), gameid:int, itemname:str):
    if gameid is None or gameid == 0:
        return None 
    url = 'https://opskins.com/ajax/sale_graph.php'
    data = { 'type':2, 'days':360, 'appid': appidmap(gameid), 'market_name': itemname}
    session_5 = copy.deepcopy(session)

    if 'X-CSRF' not in session_5.headers:
        session_5.headers['X-CSRF'] = '2ASVYy84BUevVi79vpXAZeROLPNQj84Cm'
        session_5.headers['Cookie'] = 'opskins_csrf_token=2ASVYy84BUevVi79vpXAZeROLPNQj84Cm;'
        session_5.headers['X-Requested-With'] = 'XMLHttpRequest'
    html = session_5.post(url, data).content.decode('utf-8')
    if re.search(r'{"status":1,"time":\d+',html) == None:
        return None

    res = []
    jsonres = json.loads(html)
    if ('response' in jsonres) == False:
        return res
    pattern = re.compile(r"\[('x'[^\]]*)\][^^]*?\[('Min Price \(Normalized\)'[^\]]*)\][^^]*?\[('Average Price'[^\]]*)\][^^]*?\[('Max Price \(Normalized\)'[^\]]*)\][^^]*?\[('Sales'[^\]]*)\]")
    m = pattern.findall(str(jsonres['response']))
    if m is None:
        return res

    osi = OpSalesItem()
    osi.init_osi(m[0])
    res.append(osi)
    return res


def appidmap(gameid:int):
    if gameid == 1:
        return 730
    elif gameid == 2:
        return 570
    elif gameid == 3:
        return 440
    elif gameid == 4:
        return 295110
    elif gameid == 5:
        return 433850
    elif gameid == 6:
        return 578080
    elif gameid == 7:
        return 252490
    elif gameid == 9:
        return 304930


class OpSalesItem(object):
    def __init__(self):
        self.x = ''
        self.minprice = ''
        self.aveprice = ''
        self.maxprice = ''
        self.sales = ''

    def init_osi(self, m):
        self.x = m[0]
        self.minprice = m[1]
        self.aveprice = m[2]
        self.maxprice = m[3]
        self.sales = m[4]