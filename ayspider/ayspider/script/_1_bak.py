import re
import time
import logging
from requests.sessions import Session
from ayspider.utils import util_cfpass

def search_item(session:Session, gameid:int, itemname\
    , bcfpass = True, blogin = False):
    url = ''
    if gameid == 1: #csgo
        url = 'https://opskins.com/?loc=shop_search&app=730_2&sort=lh&search_item="%s"'
    else:
        return search_itemother(session, gameid, itemname, bcfpass, blogin)
    html = util_cfpass.gethtml(session, url%(itemname))
    banned = re.search(r"The owner of this website[^<]+has banned you temporarily from accessing this website",html)
    downfromm =re.search(r"OPSkins is down for maintenance",html)
    ipbanned  = re.search(r'Your IP<[^>]+></span> has been blocked.',html)
    iscfpass = re.search(r'To ensure you are not a bot, please wait while we check your browser',html)
    if(banned or downfromm or ipbanned):
        logging.error("Stop:[%s] html:[%s]"%(itemname,html))
        return None,True
    toofaslt = re.search(r"Slow down! You're requesting pages too fast",html)
    if toofaslt:
        return None,False

    oilist = []
    if(re.search(r"We couldn't find any items",html)):
        return oilist,False
    pattern = re.compile(r'(class=.featured-item[^^]+?)</div></div></div></div></div>')
    ms = pattern.findall(html)
    if(len(ms) == 0):
        pattern = re.compile(r'(class=.featured-item[^^]+?Add to Cart</button>)')
        ms = pattern.findall(html)
        if(len(ms) == 0):
            return None,False
    pattern = re.compile('item=(\d+).>\s?([^^]+?)\s?</a>[^^]+?text-muted.>([^<]*)[^^]+?#[\d\w]+[^>]+>([^<]*)(?:[^^]+?item-img.\s+src=.([^''"]+))?[^^]+?item-amount.[^>]+?>\$([\d\.\,]+)[^^]+?suggested-price[^>]+>\$?([\d\.\,]+)?(?:[^^]+?csgo_econ_action_preview%20(\w+)[^^]+?Wear:\s*([\d\.]+))?')
    for i in ms:
        m = pattern.search(i)
        if m is None:
            continue
        oi = item()
        mark_name = oi.init_csgo(m)
        if not mark_name == itemname:
            continue
        oilist.append(oi)
    return oilist,False

def search_itemother(session:Session, gameid:int, itemname\
    , bcfpass, blogin):
    url = ''
    if gameid == 2: #dota2
        url = 'https://opskins.com/?loc=shop_search&app=570_2&sort=lh&search_item="%s"'
    elif gameid == 3: #tf 2
        url = 'https://opskins.com/?loc=shop_search&app=440_2&sort=lh&search_item="%s"'
    elif gameid == 4: #h1z1 js
        url = 'https://opskins.com/?loc=shop_search&app=295110_1&sort=lh&search_item="%s"'
    elif gameid == 5: #h1z1 kotk
        url = 'https://opskins.com/?loc=shop_search&app=433850_1&sort=lh&search_item="%s"'
    elif gameid == 6: #psb
        url = 'https://opskins.com/?loc=shop_search&app=578080_2&sort=lh&search_item="%s"'
    elif gameid == 7: #rust
        url = 'https://opskins.com/?loc=shop_search&app=252490_2&sort=lh&search_item="%s"'
    elif gameid == 8: #steam
        url = 'https://opskins.com/?loc=shop_search&app=753_6&sort=lh&search_item="%s"'
    elif gameid == 9: #Unturned
        url = 'https://opskins.com/?loc=shop_search&app=304930_2&sort=lh&search_item="%s"'
    else:
        return
    html = util_cfpass.gethtml(session,url%(itemname))
    banned = re.search(r"The owner of this website[^<]+has banned you temporarily from accessing this website",html)
    downfromm =re.search(r"OPSkins is down for maintenance",html)
    ipbanned  = re.search(r'Your IP<[^>]+></span> has been blocked.',html)
    iscfpass = re.search(r'To ensure you are not a bot, please wait while we check your browser',html)
    if(banned or downfromm or ipbanned):
        logging.error("Stop:[%s] html:[%s]"%(itemname,html))
        return None,True
    toofaslt = re.search(r"Slow down! You're requesting pages too fast",html)
    if(toofaslt):
        return None,False

    oilist = []
    if(re.search(r"We couldn't find any items",html)):
        return oilist,False
    pattern = re.compile(r'(class=.featured-item[^^]+?Add to Cart</button>)')
    ms = pattern.findall(html)
    if(len(ms) == 0):
        return None,False
    pattern = re.compile('item=(\d+).>\s?([^^]+?)\s?</a>[^^]+?text-muted.>([^<]*)[^^]+?#[\d\w]+[^>]+>([^<]*)(?:[^^]+?item-img.\s+src=.([^''"]+))?[^^]+?item-amount.[^>]+?>\$([\d\.\,]+)[^^]+?suggested-price[^>]+>\$?([\d\.\,]+)?')
    for i in range(len(ms)):
        m = pattern.search(ms[i])
        if m is None:
            continue
        oi = item()
        mark_name = oi.init_item(m)
        if not mark_name == itemname:
            continue
        oilist.append(oi)
    return oilist,False

class item(object):
    def __init__(self):
        self.id = ''
        self.price = 0
        self.wear = ''
        self.inspect = ''
        self.stickerlist = None

    def init_csgo(self, m):
        if not m:
            return
        self.id = m.group(1)
        self.price = m.group(6)
        self.inspect = m.group(8)
        self.wear = m.group(9)

        market_name = m.group(2)
        wearname = m.group(3)
        if wearname:
            market_name = "%s (%s)" %(market_name, wearname)
        return market_name

    def init_item(self, m):
        if not m:
            return
        self.id = m.group(1)
        market_name = str(m.group(2))
        self.price = m.group(6)
        return market_name