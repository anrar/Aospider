
import re
import json
import time
import requests
from requests.sessions import Session


def search_pricehistory(session:requests.Session(), gameid:int, itemname):
    url = init_url(gameid)
    if url is None:
        return None 
    resp = session.get(url + str(itemname))
    html = str(resp.content, encoding='utf-8')
    mname = re.search("Listings for\s+([^<]+)",html)
    if mname == None: #or mname.group(1) != itemname
        return None

    res = []
    if re.search(r'market_listing_table_message">\s+There are no listings for this item',html):
        return res

    pattern = re.compile(r'var line1=\[([^^]*?)\];')
    m = pattern.search(html)
    if m is None:
        return res
    line1 = m.group(1)
    phi = PriceHistoryItem()
    phi.init_phi(line1)
    res.append(phi)
    return res

def init_url(gameid:int):
    url = 'http://steamcommunity.com/market/listings/'
    if gameid == 1: #csgo
        url += '730/'
    elif gameid == 2: #dota2
        url += '570/'
    elif gameid == 3: #tf 2
        url += '440/'
    elif gameid == 4: #h1z1 js
        url += '295110/'
    elif gameid == 5: #h1z1 kotk
        url += '433850/'
    elif gameid == 6: #psb
        url += '578080/'
    elif gameid == 7: #rust
        url += '252490/'
    elif gameid == 9: #unturned
        url += '304930/'
    else:
        return
    return url

class PriceHistoryItem(object):
    def __init__(self):
        self.historydata = ''
        self.begindate = ''
        self.enddate = ''

    def init_phi(self, line1:str):
        if not line1:
            return
        pattern = re.compile(r',\[\"'+ time.strftime("%b %d %Y", time.localtime()) +'')
        m = pattern.search(line1)
        if m is None:
            line = line1
        else:
            line = str(line1[:m.start()])
        pattern = re.compile(r'\[\"\w{3}\s\d{2}\s\d{4}\s\d{2}\:\s\+0\",\d+?.\d{1,3},\"\d*\"\]')
        phitems = pattern.findall(line)
        self.historydata, self.begindate, self.enddate = self.formatphitem(phitems)

    def formatphitem(self, phitems:list):
        philist = []
        lastitem = []
        for eachdayitem in phitems:
            item = eachdayitem[1:len(eachdayitem)-1].split(',')
            item[0] = time.strftime("%Y-%m-%d", time.strptime(eval(item[0])[:11], "%b %d %Y"))
            item[1] = float(item[1])
            item[2] = int(eval(item[2]))

            try:
                if lastitem != [] and lastitem[0] == item[0]:
                    totalsellnum = item[2] + lastitem[2]
                    averageprice = round((item[1]*item[2] + lastitem[1]*lastitem[2])/totalsellnum, 3)
                    item[1], item[2] = averageprice, totalsellnum
                    philist.pop()
                philist.append(item)
                lastitem = item
            except Exception as rx: 
                print(rx)
        return str(philist), philist[0][0], philist[-1][0]
