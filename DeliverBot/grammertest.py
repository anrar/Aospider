import re
import time

def rut():
    return True, ""


try:
    di = {"asd":"sad","cea":"sss"}
    liss = []
    liss.append(di)

    if liss and len(liss) != 0 and "asd" in liss[0].keys():
        print("ceecee")
    if "asd" in liss:
        print("ceeeee")
except Exception as ex:
    print(ex.args)

finally:
    print('sd')