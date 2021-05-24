import sys
import datetime
from datetime import timezone
import logging

logger = logging.getLogger(__name__)

class BacktestDateTime:
    
    def __init__(self,timestamp=None):
        if timestamp == None:
            # we'll use the now timestamp
            self.t = datetime.datetime.now(timezone.utc)
        else:
            # parse the format assuming like this '20210317 21:00'
            self.t = datetime.datetime.strptime(timestamp+'+0000', "%Y%m%d %H:%M%z")
        logger.debug("%s %s" %(str(self.t), str(self.t.tzinfo)))

    def tsmin(self):
        return (self.t.strftime("%Y%m%d %H:%M:%"))

    def dtsmin(self):
        return (self.t.strftime("%Y%m%d %H:%M:00"))
        
    def tstenmin(self):
        temp = self.tsmin()
        return (temp[:-3] + '%')
        
    def tshour(self):
        return (self.t.strftime("%Y%m%d %H:%"))
    
    def dtshour(self):
        return (self.t.strftime("%Y%m%d %H:00"))
        
    def addmin(self, min=1):
        self.t = self.t + datetime.timedelta(minutes=min)
        
    def addhour(self, hr=1):
        self.t = self.t + datetime.timedelta(hours=hr)
        
    def laterthan(self, anotherbdt=None):
        return(self.t > anotherbdt.t)
        