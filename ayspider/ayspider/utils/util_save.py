from urllib import request
import sys

class Save:
    def __init__(self, address = 'http://127.0.0.1:14534/coll'):
        self.address = address
        return

    def submit(self, result):
        if result == "":
            return
        req = request.Request(self.address, result.encode('utf-8'))
        #print(sys.getsizeof(req))
        return request.urlopen(req).read()
