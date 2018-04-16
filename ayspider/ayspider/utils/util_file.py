import os,sys
import logging


def file_write(filname,txt):
    try:
        fsock = open(filname, "a", encoding="utf-8")
        fsock.write(txt)
        fsock.close()
    except Exception as ex:
        logging.error("error%s"%(ex))