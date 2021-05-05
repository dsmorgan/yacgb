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

    



