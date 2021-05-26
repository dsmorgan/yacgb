## https://github.com/dsmorgan/yacgb

import datetime
from datetime import timezone
from calendar import monthrange
import logging

from model.ohlcv import OHLCV

logger = logging.getLogger(__name__)


def max_array_size(timeframe, year, month):
    if timeframe == '1m':
        return(60)
    elif timeframe == '1h':
        return(24)
    elif timeframe == '1d':
        return (monthrange(year, month)[1])
    #Unexpected result, return zero
    return (0)
    
def rounded_down_time(timeframe, ct):
    if timeframe == '1m':
        return (ct.replace(minute=0, second=0, microsecond=0))
    elif timeframe == '1h':
        return (ct.replace(hour=0, minute=0, second=0, microsecond=0))
    elif timeframe == '1d':
        return (ct.replace(day=1, hour=0, minute=0, second=0, microsecond=0))
    #Unexpected result, return None
    return (None)
    

def save_candles(exch, ms, tf, ndt, candles):
    # Get minute/hour/day timeframe OHLCV candles data, grouped per hour/day/month in a table entry
    key = exch+'_'+ms+'_'+tf
    logger.debug("start of save_candles " + key)
    # For each 1st field of the ohlcv candle, compare to the rounded hour value. If a 0 minute, 0 hour, or day 1
    #  match, then take up to the next 60/24/x days of a month entries and place into a single time_item.
    x = 0
    max = 0 
    while x < len(candles):
        candle_time = datetime.datetime.fromtimestamp(candles[x][0]/1000, tz=timezone.utc)
        logger.debug("candle_time %s" % candle_time.strftime('%Y-%m-%d %H:%M:%S'))
        
        if (candle_time == rounded_down_time(tf, candle_time)):
            #create new entry
            ts = candle_time.strftime('%Y-%m-%d %H:%M:%S')
            max = max_array_size(tf,candle_time.year, candle_time.month)
            try:
                time_item = OHLCV.get(key, candles[x][0])
                time_item.update(actions=[OHLCV.array.set(candles[x:x+max]), OHLCV.last.set(str(ndt))])
                #Log an updated table entry
                logger.info('U:' + key + ' ' + str(candles[x][0]) + ' ' + ts + ' '+ str(x) + ' ' + str(x+max) + ' actual:' + str(len(candles[x:x+max])))
            except OHLCV.DoesNotExist:
                time_item = OHLCV(key, candles[x][0], timestamp_st=ts, array=candles[x:x+max], last=str(ndt))
                #Log a new table entry
                logger.info('N:' + key + ' ' + str(candles[x][0]) + ' ' + ts + ' ' + str(x) + ' ' + str(x+max) + ' actual:' + str(len(candles[x:x+max])))
            time_item.save()
            #increment to next block of candles
            x += max-1
        # increment to next candle
        x+=1
    logger.debug("end of save_candles " + key)
    return

    
class candle_limits:
    def __init__(self, last_ts, this_minute):
        self.limit_1m = 660
        self.limit_1h = 360
        self.limit_1d = 62
        
        logger.debug("last_ts %s this_minute %s" %(str(last_ts), str(this_minute)))
        if last_ts == None:
            # New entry, set defaults
            logger.debug("last_ts == None, using default values for limits")
        else:
            #calculate from last_timestamp how far back we need to go
            #since we shouldn't assume that the run interval is deterministic
            #last_timestamp is the last minute that isn't the current minute
            ltsminute = datetime.datetime.fromtimestamp(last_ts - 60, tz=timezone.utc)
            ltshour = ltsminute.replace(minute=0, second=0)
            ltsday = ltshour.replace(hour=0)
            ltsmonth = ltsday.replace(day=1)
            logger.debug("lts: minute %s hour %s day %s month %s" % (ltsminute, ltshour, ltsday, ltsmonth))
            #diff of last update to this minute
            self.limit_1m = int(((this_minute - ltshour).total_seconds()) // 60 ) + 2
            if self.limit_1m > 660:
                logger.debug('limit_1m too big: '+ str(self.limit_1m) + ' using default')
                self.limit_1m = 660
            self.limit_1h = int(((this_minute - ltsday).total_seconds()) // 3600 ) + 1
            if self.limit_1h > 360:
                logger.debug('limit_1h too big: '+ str(self.limit_1h) + ' using default')
                self.limit_1h = 360
            self.limit_1d = (this_minute.date() - ltsmonth.date()).days + 1
            if self.limit_1d > 62:
                logger.debug('limit_1d too big: '+ str(self.limit_1d) + ' using default')
                self.limit_1d = 62
        logger.info('limit_1m:' + str(self.limit_1m) + ' limit_1h:' + str(self.limit_1h) + ' limit_1d:' + str(self.limit_1d))

