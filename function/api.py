## https://github.com/dsmorgan/yacgb

import ccxt
import time
import datetime
from datetime import timezone
import logging
import os
import json
import re

#from model.orders import Orders, orders_init
#from yacgb.lookup import OrderBookLookup
#from yacgb.bdt import BacktestDateTime
from yacgb.awshelper import yacgb_aws_ps
from yacgb.gbotrunner import GbotRunner
from yacgb.util import base_symbol, quote_symbol, orderid
#from yacgb.ccxthelper import CandleTest
from yacgb.lookup import ohlcvLookup
from yacgb.bdt import BacktestDateTime
from yacgb.indicators import Indicators
from yacgb.orderslookup import OrdersGet

logger=logging.getLogger()
logger.setLevel(logging.INFO)

logger.info("CCXT version: %s" % ccxt.__version__)
#AWS parameter store usage is optional, and can be overridden with environment variables
psconf=yacgb_aws_ps(with_decryption=False)
#OHLCV table lookup cache
olcache=ohlcvLookup()

myexch={}
for e in psconf.exch:
    myexch[e] = eval ('ccxt.%s ()' % e)
    myexch[e].setSandboxMode(psconf.exch_sandbox[e])
    myexch[e].enableRateLimit = False
    myexch[e].load_markets()
    #load_markets is required before each exchange can be used, but an expensive (time consuming) operation that can also
    # interfere with server side rate limiting. Moving this to global reduces the frequency it needs to be called.

#orders_init()

list_gbotids = re.compile('/gbotids$')
get_gbotid = re.compile('/gbotid/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$')

def lambda_handler(event, context):
    run_start = datetime.datetime.now(timezone.utc)
    global myexch
    global psconf
    
    psconf.collect()
    for d in psconf.del_exch:
        logger.info("config change, deleting exchange config: %s" % d)
        del(myexch[d])
    for a in psconf.new_exch:
        logger.info("config change, new exchange config: %s" % a)
        myexch[a] = eval ('ccxt.%s ()' % a)
        myexch[a].setSandboxMode(psconf.exch_sandbox[a])
        myexch[a].enableRateLimit = False
        myexch[a].load_markets()
    
    
    response = {}
    gbotid_match = get_gbotid.search(event["path"])
    if gbotid_match:
        #get details of a specific gbotid
        response['status'] == 'ok'
        gbotid = gbotid_match.group(1)
        gr = GbotRunner(gbotid)
        response.update(gr.gbot_dict)
        #get ohlcv
        lookup = olcache.get_candles(exchange, market_symbol, timeframe, nowbdt.dtstf(timeframe), -1440)
        i = Indicators(lookup.aggregate('5m'))
        response.update(i.ca_dict)
        #get orders
        o = OrdersGet(gbotid)
        response.update(o.orders_dict)
        
    elif list_gbotids.search(event["path"]):
        #list all gbotids (in parameter store)
        response['status'] == 'ok'
        response['gbotids'] = psconf.shuffled_gbotids
    else:
        response['status'] == 'error'
    
    #response['gbotids'] = gbotids
    logger.info(response)

    for gbotid in gbotids:
        #load Gbot, TODO: need to handle if it can't be found
        x = GbotRunner(gbotid=gbotid)
        response[gbotid]=x.gbot.to_dict()

    run_end = datetime.datetime.now(timezone.utc)
    logger.info('RUN TIME: %s', str(run_end-run_start))
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Credentials': 'true',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(response)
    }
 

if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s', 
                            datefmt='%Y%m%d %H:%M:%S', filename='api.log')
    if (os.environ.get('DYNAMODB_HOST') == None):
        print ('DYNAMODB_HOST not set')
        exit()
      
    print ('DYNAMODB_HOST=' + os.environ.get('DYNAMODB_HOST'))
    
    if (len(sys.argv) != 2):
        print ("error: missing event json file")
        exit(1)
    with open(sys.argv[1]) as json_file:
        event = json.load(json_file)
    
    print (lambda_handler(event, None))