## https://github.com/dsmorgan/yacgb

import datetime
from datetime import timezone
import os
import logging
import sys
import random

from yacgb.awshelper import yacgb_aws_ps
from yacgb.lookup import ohlcvLookup
from yacgb.bdt import BacktestDateTime
#from yacgb.util import base_symbol, quote_symbol, event2config, configsetup


logger = logging.getLogger()
logger.setLevel(logging.INFO)

#AWS parameter store usage is optional, and can be overridden with environment variables
psconf=yacgb_aws_ps()
#OHLCV table lookup cache
olcache = ohlcvLookup()

def lambda_handler(event, context):
    run_start = datetime.datetime.now(timezone.utc)
    #### tickerstats run START
    random.shuffle(psconf.market_list)
    logger.info("exchange:market %s" % str(psconf.market_list))
    for x in psconf.market_list:
        exchange = x.split(':', 1)[0]
        market_symbol = x.split(':', 1)[1]
        timeframe = '1m'
        nowbdt = BacktestDateTime()
        lookup = olcache.get_candles(exchange, market_symbol, timeframe, nowbdt.dtstf(timeframe), -300)
        logger.info("%s %s %s" %(exchange, market_symbol, lookup))
        
    
    
    
    logger.info(olcache)
    #### tickerstats run END
    run_end = datetime.datetime.now(timezone.utc)
    logger.info('RUN TIME: %s', str(run_end-run_start))
    
    return ("OK")
    
if __name__ == "__main__":
    import time
    logfile = 'tickerstats.log'
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


  