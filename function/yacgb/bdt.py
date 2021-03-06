## https://github.com/dsmorgan/yacgb

import sys
import datetime
import calendar
from datetime import timezone
import logging

logger = logging.getLogger(__name__)

class BacktestDateTime:
    
    def __init__(self,timestring=None,timestamp=None):
        if timestring == None and timestamp == None:
            # we'll use now in the absence of a timestring
            self.t = datetime.datetime.now(timezone.utc)
        elif timestring != None:
            try:
                # parse the format assuming like this '20210317 21:00'
                self.t = datetime.datetime.strptime(timestring+'+0000', "%Y%m%d %H:%M%z")
            except ValueError:
                # try parse an alternate format assuming like this '2021-03-17 21:00:00.000000+00:00'
                self.t = datetime.datetime.strptime(timestring, "%Y-%m-%d %H:%M:%S.%f%z")
        else: #timestamp != None
            self.t = datetime.datetime.fromtimestamp(timestamp/1000, tz=timezone.utc)
        
        logger.debug("%s %s -> %s %s" %(timestring, timestamp, str(self.t), str(self.t.tzinfo)))
    
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
        
    def diffsec(self, anotherbdt=None):
        return ((self.t-anotherbdt.t).total_seconds())
        
    def difftf(self, tf='1m', anotherbdt=None):
        if tf.endswith('m'):
            return ((self.t-anotherbdt.t).total_seconds())
        if tf.endswith('h'):
            return ((self.t-anotherbdt.t).total_seconds()/60)
        #elif tf.endswith('d'):
        return ((self.t-anotherbdt.t).total_seconds()/(3600))
        
    def dtstf(self, tf='1m'):
        if tf.endswith('m'):
            return (self.t.strftime("%Y%m%d %H:%M"))
        elif tf.endswith('h'):
            return (self.t.strftime("%Y%m%d %H:00"))
        #elif tf.endswith('d'):
        return (self.t.strftime("%Y%m%d 00:00"))
        
    def dtskey(self, tf='1m'):
        if tf.endswith('m'):
            return (self.t.strftime("%Y%m%d %H:00"))
        elif  tf.endswith('h'):
            return (self.t.strftime("%Y%m%d 00:00"))
        #elif tf.endswith('d'):
        return (self.t.strftime("%Y%m01 00:00"))
            
    def addtf(self, tf='1m', offset=1):
        if tf.endswith('m'):
            self.t = self.t + datetime.timedelta(minutes=offset)
        elif tf.endswith('h'):
            self.t = self.t + datetime.timedelta(hours=offset)
        else: #tf.endswith('d'), increment a day if not 1m or 1h
            self.t = self.t + datetime.timedelta(days=offset)
            
    def addkey(self, tf='1m', offset=1):
        if tf.endswith('m'):
            self.t = self.t + datetime.timedelta(hours=offset)
        elif tf.endswith('h'):
            self.t = self.t + datetime.timedelta(days=offset)
        else: #tf.endswith('d'), increment a day if not 1m or 1h
            month = self.t.month - 1 + offset
            year = self.t.year + month // 12
            month = month % 12 + 1
            day = min(self.t.day, calendar.monthrange(year,month)[1])
            hour = self.t.hour
            minute = self.t.minute
            self.t =  datetime.datetime(year, month, day, hour=hour, minute=minute, tzinfo=timezone.utc)
            
    def ccxt_timestamp(self, tf='1m'):
        if tf.endswith('m'):
            return (int(self.t.replace(second=0, microsecond=0).timestamp()*1000))
        elif tf.endswith('h'):
            return (int(self.t.replace(minute=0, second=0, microsecond=0).timestamp()*1000))
        #elif tf.endswith('d'):
        return (int(self.t.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()*1000))
         
    def ccxt_timestamp_key(self, tf='1m'):
        if tf.endswith('m'):
            return (int(self.t.replace(minute=0, second=0, microsecond=0).timestamp()*1000))
        elif tf.endswith('h'):
            return (int(self.t.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()*1000))
        #elif tf.endswith('d'):
        return (int(self.t.replace(day=1, hour=0, minute=0, second=0, microsecond=0).timestamp()*1000))