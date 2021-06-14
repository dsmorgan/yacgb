## https://github.com/dsmorgan/yacgb

import ccxt
import datetime
from datetime import timezone
import os
import logging
import time
import random

from yacgb.awshelper import yacgb_aws_ps
from yacgb.ohlcv_sync import save_candles, candle_limits
from model.market import Market, market_init
from model.ohlcv import OHLCV, ohlcv_init

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info("CCXT version: %s" % ccxt.__version__)
#AWS parameter store usage is optional, and can be overridden with environment variables
psconf=yacgb_aws_ps()

# Create tables in dynamodb if they don't exist already
market_init()
ohlcv_init()

# load the sconfigured exchange from ccxt, load_markets is needed to initialize
myexch = {}
for e in psconf.exch:
    myexch[e] = eval ('ccxt.%s ()' % e)
    myexch[e].enableRateLimit = False
    myexch[e].load_markets()


def lambda_handler(event, context):
    nowdt = datetime.datetime.now(timezone.utc)  
    thisminute = nowdt.replace(second=0, microsecond=0)
    
    random.shuffle(psconf.market_list)
    logger.info("exchange:market %s" % str(psconf.market_list))
    for x in psconf.market_list:
        exchange = x.split(':', 1)[0]
        market_symbol = x.split(':', 1)[1]
        logger.debug("syncing %s %s" %(exchange, market_symbol))
 
        ####
        # If this is the 1st time we've attempted to get this exchange + market_symbol, then save a table entry w/ some details
        #TODO refactor these out
        try:
            exchange_item = Market.get(exchange, market_symbol)
        except Market.DoesNotExist:
            #fetch new market info
            market = myexch[exchange].market(market_symbol)
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
        
        #Determine the number of candles to request and save, for each duration
        cl = candle_limits(exchange_item.last_timestamp, thisminute)
        if exchange_item.last_timestamp == None:
            #store the current timestamp(s) in START
            exchange_item.start_timestamp = int(nowdt.timestamp())
            exchange_item.start = str(nowdt)
        #store the current minute timestamp(s) in LAST
        exchange_item.last_timestamp = int(thisminute.timestamp())
        exchange_item.last = str(nowdt)
     
        #TODO: refactor this as a loop     
        # Get minute timeframe OHLCV candles data, grouped per hour in a table entry
        timeframe='1m'
        key = exchange+'_'+market_symbol+'_'+timeframe
        candles = myexch[exchange].fetchOHLCV(market_symbol, timeframe, limit=cl.limit_1m)
        save_candles(exchange, market_symbol, timeframe, nowdt, candles)
    
        # Get hour timeframe OHLCV candles data, grouped per day in a table entry
        timeframe='1h'
        key = exchange+'_'+market_symbol+'_'+timeframe
        candles = myexch[exchange].fetchOHLCV(market_symbol, timeframe, limit=cl.limit_1h)
        save_candles(exchange, market_symbol, timeframe, nowdt, candles)
    
        # Get day timeframe OHLCV candles data, grouped per month on a table entry
        timeframe='1d'
        key = exchange+'_'+market_symbol+'_'+timeframe
        candles = myexch[exchange].fetchOHLCV(market_symbol, timeframe, limit=cl.limit_1d)
        save_candles(exchange, market_symbol, timeframe, nowdt, candles)
        
        # This needs to happen after the OHLCV entries have all been collected, to save the last_timestamp
        exchange_item.save()
        ####
    return ("OK")
    

if __name__ == "__main__":
    logfile = 'synctickers.log'
    logging.basicConfig(level=logging.INFO, format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s', 
                            datefmt='%Y%m%d %H:%M:%S', filename=logfile)
    if (os.environ.get('DYNAMODB_HOST') == None):
        print ('DYNAMODB_HOST not set')
        exit()
    print ('DYNAMODB_HOST=' + os.environ.get('DYNAMODB_HOST'))
    print ('logging output to ' + logfile)
    error_count=0
    while True:
        try:
            logging.info(lambda_handler(None, None))
        except Exception:
            logging.exception("Fatal error in main loop")
            error_count+=1
        sleep_time = 60 - (time.time()-11) % 60
        logging.info("sleeping %f error count %d" %(sleep_time, error_count))
        time.sleep(sleep_time)