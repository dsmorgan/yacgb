## https://github.com/dsmorgan/yacgb

import datetime
from datetime import timezone
import logging

from model.ohlcv import OHLCV
from yacgb.ohlcv_sync import key_time

logger = logging.getLogger(__name__)

class OrderBookLookup:
    def __init__(self, exchange, market_symbol):
        self.exchange=exchange
        self.market_symbol=market_symbol
        self.ddb = OHLCV()
        self.last_keyptimestamp = None
        self.last_time_item = None
        self.key = None
    
    def getcandle(self, timeframe='1h', stime='20210317 21:10'):
        key = self.exchange+'_'+self.market_symbol+'_'+timeframe
        if key != self.key:
            self.key = key
            self.last_keyptimestamp = None
            
        ptime = datetime.datetime.strptime(stime, "%Y%m%d %H:%M").replace(tzinfo=timezone.utc)
        ptimestamp = int(ptime.timestamp()*1000)
        #if timeframe == '1h':
        #keyptime = ptime.replace(hour=0, minute=0, second=0, microsecond=0)
        keyptime = key_time(timeframe, ptime)
        keyptimestamp = int(keyptime.timestamp()*1000)
        self.open = 0
        self.close = 0
        self.high = 0
        self.low = 999999
        self.volume = 0
        self.cnt = 0

        if (keyptimestamp == self.last_keyptimestamp):
            #Prevent another query to the database, the record we were looking for is already in this object (last_time_item)
            time_item = self.last_time_item
        else:
            try:
                time_item = OHLCV.get(self.key, keyptimestamp)
                self.last_time_item = time_item
                self.last_keyptimestamp = keyptimestamp
                
            except OHLCV.DoesNotExist:
                logger.warn("Not found in table key: %s (%s %s %s %s)" %(str(self.key), str(keyptime), str(keyptimestamp), str(ptime), str(ptimestamp)))
                self.low=0
                return

        for x in time_item.array:
           if x[0] == ptimestamp:
                self.open = x[1]
                self.high = x[2]
                self.low = x[3]
                self.close = x[4]
                self.volume = x[5]
                self.cnt = 1
                return
        logger.warn("Not found in array: %s (%s %s %s %s)" %(str(self.key), str(keyptime), str(keyptimestamp), str(ptime), str(ptimestamp)))
        self.low=0
        