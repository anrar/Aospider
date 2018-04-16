import json
import time
import rsa
import re
import base64
import requests
from .util_parse import *

class SteamHelper:
    def __init__(self, session: requests.Session = requests.session()):
        self._session = session
        return 

    def login(self, username, password):
        url = 'https://steamcommunity.com/login/getrsakey/'
        data = {'username' : username, 'donotcache' : str(int(time.time()))}
        bcontent = self._session.post(url,data).content
        result = json.loads(bcontent.decode('utf-8'))
        pub_key = rsa.PublicKey(int(str(result["publickey_mod"]), 16),    \
            int(str(result["publickey_exp"]), 16))
        password_rsa = base64.b64encode(rsa.encrypt(bytes(password,'utf-8'), pub_key))

        url = 'https://steamcommunity.com/login/dologin/'
        data = {
            'username' : username,
            "password": password_rsa,
            "emailauth": "",
            "loginfriendlyname": "",
            "captchagid": "-1",
            "captcha_text": "",
            "emailsteamid": "",
            "rsatimestamp": result["timestamp"],
            "remember_login": False,
            "donotcache": str(int(time.time())),
            }
        bcontent = self._session.post(url,data).content
        result = json.loads(bcontent.decode('utf-8'))
        if result["success"]:
            return True
        else:
            return False

    def loginopenid(self, username='', password='', siteurl='https://opskins.com/?loc=login_migrate&content_only=1'):
        domain,param = get_url_params(siteurl)
        url = 'https://steamcommunity.com/openid/login?openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&openid.mode=checkid_setup&openid.return_to='
        url = url + siteurl + '&openid.realm=' + domain
        url = url + '&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select'
        if not self.login(username, password):
            return False
        html = str(self._session.get(url).content)
        pattern = re.compile(r'<input.+?name=\W?([^\x22\x2c]+).+?value=\W?([^\x22\x2c]+)')
        ms = pattern.findall(html)
        if(len(ms) == 0):
            return
        data = {}
        for i in ms :
            data[i[0]] = i[1]
        result = self._session.post('https://steamcommunity.com/openid/login',data).content
        pattern = re.compile(r'opener.postMessage\({"msg": "logged_in')
        m = pattern.search(str(result))
        if m is None:
            return False
        else:
            return True

    def get_session(self):
        return self._session