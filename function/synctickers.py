## https://github.com/dsmorgan/yacgb

import ccxt
import datetime
from datetime import timezone
from calendar import monthrange
import os
import logging
from time import time, sleep

from yacgb.util import get_os_env
from yacgb.ohlcv_sync import save_candles
from model.market import Market
from model.ohlcv import OHLCV

## CONFIGURATION
exchange = get_os_env('EXCHANGE', required=True)
market_symbol = get_os_env('MARKET_SYMBOL', required=True)

## END

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# load the configured exchange from ccxt, load_markets is needed to initialize
myexch = eval ('ccxt.%s ()' % exchange)
myexch.enableRateLimit = False
myexch.load_markets()


def lambda_handler(event, context):

    #TODO refactor these out
    # Create tables in dynamodb if they don't exist already
    if not Market.exists():
        Market.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
        logger.info('Created Dynamodb table Market')
    if not OHLCV.exists():
        OHLCV.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)   
        logger.info('Created Dynamodb table OHLCV')
  
    nowdt = datetime.datetime.now(timezone.utc)  
    thisminute = nowdt.replace(second=0, microsecond=0)
  
    # If this is the 1st time we've attempted to get this exchange + market_symbol, then save a table entry w/ some details
    
    #TODO refactor these out
    try:
        exchange_item = Market.get(exchange, market_symbol)
    except Market.DoesNotExist:
        #fetch new market info
        market = myexch.market(market_symbol)
        exchange_item = Market(exchange, market_symbol,
                    precision_base=market['precision']['amount'], 
                    precision_quote=market['precision']['price'],
                    maker=market['maker'],
                    taker=market['taker'],
                    limits_amount_max=market['limits']['amount']['max'],
                    limits_amount_min=market['limits']['amount']['min'],
                    limits_cost_max=market['limits']['cost']['max'],
                    limits_cost_min=market['limits']['cost']['min'],
                    limits_price_max=market['limits']['price']['max'],
                    limits_price_min=market['limits']['price']['min'])
        exchange_item.save()
        logger.info('Created new Market entry [' + exchange + '] [' + market_symbol + ']')
    
    ltsminute=None
    ltshour=None
    ltsday=None
    ltsmonth=None
    
    
    #TODO refactor these out
    if exchange_item.last_timestamp == None:
        # New entry, set defaults
        limit_1m = 660
        limit_1h = 360
        limit_1d = 62
        #set start_timestamp
        exchange_item.start_timestamp = int(nowdt.timestamp())
        exchange_item.start = str(nowdt)
    else:
        #calculate from last_timestamp how far back we need to go
        #since we shouldn't assume that the run interval is deterministic
        #last_timestamp is the last minute that isn't the current minute
        ltsminute = datetime.datetime.fromtimestamp(exchange_item.last_timestamp - 60, tz=timezone.utc)
        ltshour = ltsminute.replace(minute=0, second=0)
        ltsday = ltshour.replace(hour=0)
        ltsmonth = ltsday.replace(day=1)
        #diff of last update to this minute
        limit_1m = int(((thisminute - ltshour).total_seconds()) // 60 ) + 2
        if limit_1m > 660:
            limit_1m = 660
        limit_1h = int(((thisminute - ltsday).total_seconds()) // 3600 ) + 1
        if limit_1h > 360:
            limit_1h = 360
        limit_1d = (thisminute.date() - ltsmonth.date()).days + 1
        if limit_1d > 62:
            limit_1d = 62
    logger.info('limit_1m:' + str(limit_1m) + ' limit_1h:' + str(limit_1h) + ' limit_1d:' + str(limit_1d))
        
    #store the current timestamp(s)
    exchange_item.last_timestamp = int(thisminute.timestamp())
    exchange_item.last = str(nowdt)
 
    # Get minute timeframe OHLCV candles data, grouped per hour in a table entry
    timeframe='1m'
    key = exchange+'_'+market_symbol+'_'+timeframe
    candles = myexch.fetchOHLCV(market_symbol, timeframe, limit=limit_1m)
    save_candles(exchange, market_symbol, timeframe, nowdt, candles)

    # Get hour timeframe OHLCV candles data, grouped per day in a table entry
    timeframe='1h'
    key = exchange+'_'+market_symbol+'_'+timeframe
    candles = myexch.fetchOHLCV(market_symbol, timeframe, limit=limit_1h)
    save_candles(exchange, market_symbol, timeframe, nowdt, candles)

    # Get day timeframe OHLCV candles data, grouped per month on a table entry
    timeframe='1d'
    key = exchange+'_'+market_symbol+'_'+timeframe
    candles = myexch.fetchOHLCV(market_symbol, timeframe, limit=limit_1d)
    save_candles(exchange, market_symbol, timeframe, nowdt, candles)
    
    # This needs to happen after the OHLCV entries have all been collected, to save the last_timestamp
    exchange_item.save()
    return (0)
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s', 
                            datefmt='%Y%m%d %H:%M:%S', filename='synctickers.log')
    if (os.environ.get('DYNAMODB_HOST') == None):
        print ('DYNAMODB_HOST not set')
        exit()
    print ('DYNAMODB_HOST=' + os.environ.get('DYNAMODB_HOST'))
    
    while True:
        print (lambda_handler(None, None))
        sleep_time = 60 - (time()-11) % 60
        print ("sleeping", sleep_time)
        sleep(sleep_time)