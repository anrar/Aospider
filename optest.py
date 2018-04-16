import socket
import re
import time
import socket
from threading import Thread
from threading import current_thread
from urllib import request
import requests


true_socket = socket.socket
def bound_socket(*a, **k):
    sock = true_socket(*a, **k)
    thread = current_thread()
    sock.bind((thread.ip, 0))
    return sock
socket.socket = bound_socket

class GetHtml(Thread):
    def __init__(self, ip=""):
        Thread.__init__(self)
        self.ip = ip

    def worker(self):
        try:
            session = requests.Session()
            session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0'
            html = session.get('https://opskins.com/').content
            html = html.decode('unicode-escape')
            result = re.search(r'has been blocked\r\n',html)
            if result:
                print("%s :%s"%(self.ip,result.group(0)))
            else:
                print("%s zhengchang\r\n"%(self.ip))
        except Exception as excep:
            print("%s errror %s" %(self.ip,excep))

    def run(self):
        self.worker()
        time.sleep(0.1)


iplist = ['174.139.162.182']#
for i in iplist:
    gh = GetHtml(i)
    gh.start()
