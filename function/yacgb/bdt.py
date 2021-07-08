## https://github.com/dsmorgan/yacgb

import sys
import datetime
import calendar
from datetime import timezone
import logging

logger = logging.getLogger(__name__)

class BacktestDateTime:
    
    def __init__(self,timestring=None):
        if timestring == None:
            # we'll use now in the absence of a timestring
            self.t = datetime.datetime.now(timezone.utc)
        else:
            # parse the format assuming like this '20210317 21:00'
            self.t = datetime.datetime.strptime(timestring+'+0000', "%Y%m%d %H:%M%z")
        logger.debug("%s %s" %(str(self.t), str(self.t.tzinfo)))
    
    def __str__(self):
        return (self.t.strftime("%Y%m%d %H:%M"))

    def dtsmin(self):
        return (self.t.strftime("%Y%m%d %H:%M"))
        
    def dtshour(self):
        return (self.t.strftime("%Y%m%d %H:00"))
        
    def addmin(self, min=1):
        self.t = self.t + datetime.timedelta(minutes=min)
        
    def addhour(self, hr=1):
        self.t = self.t + datetime.timedelta(hours=hr)
        
    def laterthan(self, anotherbdt=None):
        return(self.t > anotherbdt.t)
        
    def dtstf(self, tf='1h'):
        if tf == '1m':
            return (self.t.strftime("%Y%m%d %H:%M"))
        elif tf == '1h':
            return (self.t.strftime("%Y%m%d %H:00"))
        #elif tf == '1d'
        return (self.t.strftime("%Y%m%d 00:00"))
        
    def dtskey(self, tf='1h'):
        if tf == '1m':
            return (self.t.strftime("%Y%m%d %H:00"))
        elif tf == '1h':
            return (self.t.strftime("%Y%m%d 00:00"))
        #elif tf == '1d'
        return (self.t.strftime("%Y%m01 00:00"))
            
    def addtf(self, tf='1h', offset=1):
        if tf == '1m':
            self.t = self.t + datetime.timedelta(minutes=offset)
        elif tf == '1h':
            self.t = self.t + datetime.timedelta(hours=offset)
        else: #tf == '1d', increment a day if not 1m or 1h
            self.t = self.t + datetime.timedelta(days=offset)
            
    def addkey(self, tf='1h', offset=1):
        if tf == '1m':
            self.t = self.t + datetime.timedelta(hours=offset)
        elif tf == '1h':
            self.t = self.t + datetime.timedelta(days=offset)
        else: #tf == '1d', increment a day if not 1m or 1h
            month = self.t.month - 1 + offset
            year = self.t.year + month // 12
            month = month % 12 + 1
            day = min(self.t.day, calendar.monthrange(year,month)[1])
            hour = self.t.hour
            minute = self.t.minute
            self.t =  datetime.datetime(year, month, day, hour=hour, minute=minute, tzinfo=timezone.utc)
            
    def ccxt_timestamp(self, tf='1h'):
        if tf == '1m':
            return (int(self.t.replace(second=0, microsecond=0).timestamp()*1000))
        elif tf == '1h':
            return (int(self.t.replace(minute=0, second=0, microsecond=0).timestamp()*1000))
        #elif timeframe == '1d':
        return (int(self.t.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()*1000))
         
    def ccxt_timestamp_key(self, tf='1h'):
        if tf == '1m':
            return (int(self.t.replace(minute=0, second=0, microsecond=0).timestamp()*1000))
        elif tf == '1h':
            return (int(self.t.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()*1000))
        #elif timeframe == '1d':
        return (int(self.t.replace(day=1, hour=0, minute=0, second=0, microsecond=0).timestamp()*1000))
    
  
        
    
        