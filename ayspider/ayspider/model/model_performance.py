class Performance(object):
    def __init__(self, starttime = 0):
        self.starttime = starttime
        self.gettask = 0
        self.gethtml = 0
        self.savedata = 0
        self.endtime = 0

    def TaskTime(self):
        return self.gettask - self.starttime

    def HtmlTime(self):
        return self.gethtml - self.gettask

    def SaveTime(self):
        return self.savedata - self.gethtml

    def CountTime(self):
        return self.endtime - self.starttime