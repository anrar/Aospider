import re
import json
import requests
from requests.sessions import Session



#def search_stockandprice(session:requests.Session(), gameid:int, pagesize:int=100):
#    url = init_url(gameid)
#    if url == None:
#        return
#    pager, total_count = each_page(session, url, 0, pagesize)
#    return [each_page(session, url, p, pagesize) for p in range(total_count//pagesize)]

def search_stockandprice(session:requests.Session(), gameid:int, pageindex:int, pagesize:int=100):
    if gameid is None:
        return
    url = init_url(gameid)
    if url is None:
        return
    bcontent = session.get(url%((pageindex-1)*pagesize, pagesize)).content
    result = json.loads(bcontent.decode('utf-8'))
    pattern = re.compile(r'market_listing_table_header')
    m = pattern.search(result["results_html"])
    if m is None:
        return 
    pattern = re.compile(r'class="market_listing_num_listings_qty"[^>]*>(\d{1,3}(?:,\d{3})*)[^^]*?class="normal_price"\s?>\$(\d{1,3}(?:,\d{3})*(?:.\d{2}))\s?[USD]?[^^]*?class="market_listing_item_name" [^>]*?>([^<]*)<')
    ms = pattern.findall(result["results_html"])

    res = []
    for item in ms:
        spi = StaemStockPrice()
        spi.init_spi(item)
        res.append(spi)
    return res

def init_url(gameid:int):
    url = 'http://steamcommunity.com/market/search/render/?query=&search_descriptions=0&sort_column=popular&sort_dir=desc&start=%d&count=%d'
    if gameid == 1: #csgo
        url += '&appid=730&category_730_ItemSet[]=any&category_730_ProPlayer[]=any&category_730_StickerCapsule[]=any&category_730_TournamentTeam[]=any&category_730_Weapon[]=any'
    elif gameid == 2: #dota2
        url += '&appid=570&category_570_Hero[]=any&category_570_Slot[]=any&category_570_Type[]=any'
    elif gameid == 3: #tf 2
        url += '&appid=440&category_440_Type[]=any'
    elif gameid == 4: #h1z1 js
        url += '&appid=295110'
    elif gameid == 5: #h1z1 kotk
        url += '&appid=433850'
    elif gameid == 6: #psb
        url += '&appid=578080'
    elif gameid == 7: #rust
        url += '&appid=252490&category_252490_itemclass[]=any'
    elif gameid == 9: #unturned
        url += '&appid=304930&category_304930_effect[]=any&category_304930_skin_slot[]=any'
    else:
        return
    return url

class StaemStockPrice(object):
    def __init__(self):
        self.SName = ''
        self.Quantity = ''
        self.Price = ''

    def init_spi(self, m):
        if not m:
            return
        self.SName = m[2]
        self.Quantity = str(m[0]).replace(',','')
        self.Price = str(m[1]).replace(',','')
