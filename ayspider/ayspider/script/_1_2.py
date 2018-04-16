import re
import time
import logging
from requests.sessions import Session
from ayspider.utils import util_cfpass
from ayspider import utils

def search_item(session:Session, gameid:int, itemname\
    , bcfpass = True, blogin = False, ip = ""):
    url = ''
    needlogin = False
    needstop = False
    if gameid == 1: #csgo
        url = 'https://opskins.com/ajax/search_scroll.php?app=730_2&search_item="%s"&sort=lh&page=1&appId=730&contextId=2'
    else:
        return search_itemother(session, gameid, itemname, bcfpass, blogin,ip)
    html = util_cfpass.gethtml(session, url%(itemname))
    banned = re.search(r"The owner of this website[^<]+has banned you temporarily from accessing this website",html)
    downfromm =re.search(r"OPSkins is down for maintenance",html)
    ipbanned  = re.search(r'Your IP<[^>]+></span> has been blocked.',html)
    if(banned or downfromm or ipbanned):
        logging.error("%s Stop:[%s] html:[%s]"%(ip,itemname,html))
        return needlogin,None,True
    if html == None or html == ""\
        or re.search('sendAlert[^<]+<div\s+class=[^"]+"alert\s+alert-warning[^"]+">',html)\
        or re.search("We ran into a problem when performing your search",html)\
        or re.search("<input type='hidden' class='isload' value='true'>",html) == None:
        logging.warning("%s None:[%s] html:[%s]"%(ip, itemname,html))
        return needlogin,None,needstop
    oilist = []

    ms = re.findall("(class='featured-item[^^]+?)</div></div></div></div></div>",html)
    if(len(ms) == 0):
        ms = re.findall("(class='featured-item[^^]+?Add to Cart</button>)",html)
        if(len(ms) == 0):
            logging.info("%s Zero:[%s] html:[%s]"%(ip, itemname, html))
            return needlogin,oilist,needstop

    pattern = re.compile("item=(?P<id>\d+)'>\s?(?P<name>[^^]+?)\s?</a>[^^]+?text-muted'>(?P<wname>[^<]*)[^^]+?item-amount'[^>]+?>\$(?P<price>[\d\.\,]+)(?:[^^]+?csgo_econ_action_preview%20(?P<inspect>\w+)[^^]+?Wear:\s*(?P<wear>[\d\.]+))?")
    for i in ms:
        m = pattern.search(i)
        if m is None:
            continue
        oi = item()
        mark_name = oi.init_csgo(m)
        if not mark_name == itemname:
            continue
        oilist.append(oi)
    return needlogin,oilist,needstop

def search_itemother(session:Session, gameid:int, itemname\
    , bcfpass = True, blogin = False, ip = ""):
    url = ''
    needlogin = False
    needstop = False
    if gameid == 2: #dota2
        url = 'https://opskins.com/ajax/search_scroll.php?app=570_2&search_item="%s"&sort=lh&page=1&appId=570&contextId=2'
    elif gameid == 3: #tf 2
        url = 'https://opskins.com/ajax/search_scroll.php?app=440_2&search_item="%s"&sort=lh&page=1&appId=440&contextId=2'
    elif gameid == 4: #h1z1 js
        url = 'https://opskins.com/ajax/search_scroll.php?app=295110_1&search_item="%s"&sort=lh&page=1&appId=295110&contextId=1'
    elif gameid == 5: #h1z1 kotk
        url = 'https://opskins.com/ajax/search_scroll.php?app=433850_1&search_item="%s"&sort=lh&page=1&appId=433850&contextId=1'
    elif gameid == 6: #psb
        url = 'https://opskins.com/ajax/search_scroll.php?app=578080_2&search_item="%s"&sort=lh&page=1&appId=578080&contextId=2'
    elif gameid == 7: #rust
        url = 'https://opskins.com/ajax/search_scroll.php?app=252490_2&search_item="%s"&sort=lh&page=1&appId=252490&contextId=2'
    elif gameid == 8: #steam
        url = 'https://opskins.com/ajax/search_scroll.php?app=753_6&search_item="%s"&sort=lh&page=1&appId=753&contextId=2'
    elif gameid == 9: #Unturned
        url = 'https://opskins.com/ajax/search_scroll.php?app=304930_2&search_item="%s"&sort=lh&page=1&appId=304930&contextId=2'
    else:
        return
    html = util_cfpass.gethtml(session,url%(itemname))
    banned = re.search(r"The owner of this website[^<]+has banned you temporarily from accessing this website",html)
    downfromm =re.search(r"OPSkins is down for maintenance",html)
    ipbanned  = re.search(r'Your IP<[^>]+></span> has been blocked.',html)
    if(banned or downfromm or ipbanned):
        logging.error("%s Stop:[%s] html:[%s]"%(ip,itemname,html))
        return needlogin,None,True
    if html == None or html == ""\
        or re.search('sendAlert[^<]+<div\s+class=[^"]+"alert\s+alert-warning[^"]+">',html)\
        or re.search("We ran into a problem when performing your search",html)\
        or re.search("<input type='hidden' class='isload' value='true'>",html) == None:
        logging.warning("%s None:[%s] html:[%s]"%(ip,itemname,html))
        return needlogin,None,needstop
    oilist = []

    ms = re.findall("(class='featured-item[^^]+?Add to Cart</button>)",html)
    if(len(ms) == 0):
        logging.info("%s Zero:[%s] html:[%s]"%(ip, itemname,html))
        return needlogin,oilist,needstop
    pattern = re.compile("item=(?P<id>\d+)'>\s?(?P<name>[^^]+?)\s?</a>[^^]+?item-amount'[^>]+?>\$(?P<price>[\d\.\,]+)")
    for i in range(len(ms)):
        m = pattern.search(ms[i])
        if m is None:
            continue
        oi = item()
        mark_name = oi.init_item(m)
        if not mark_name == itemname:
            continue
        oilist.append(oi)
    return needlogin,oilist,needstop

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
        self.id = m.group('id')
        self.price = m.group('price')
        self.inspect = m.group('inspect')
        self.wear = m.group('wear')

        market_name = m.group('name')
        wearname = m.group('wname')
        if wearname:
            market_name = "%s (%s)" %(market_name, wearname)
        return market_name

    def init_item(self, m):
        if not m:
            return
        self.id = m.group('id')
        market_name = str(m.group('name'))
        self.price = m.group('price')
        return market_name