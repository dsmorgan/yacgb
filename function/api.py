## https://github.com/dsmorgan/yacgb

import ccxt
import time
import datetime
from datetime import timezone
import logging
import os
import sys
import json
import re

#from model.orders import Orders, orders_init
#from yacgb.lookup import OrderBookLookup
#from yacgb.bdt import BacktestDateTime
from yacgb.awshelper import yacgb_aws_ps
from yacgb.gbotrunner import GbotRunner
#from yacgb.util import base_symbol, quote_symbol, orderid
#from yacgb.ccxthelper import CandleTest
from yacgb.lookup import ohlcvLookup
from yacgb.bdt import BacktestDateTime
from yacgb.indicators import Indicators
from yacgb.orderslookup import OrdersGet
from model.gbot import Gbot

logger=logging.getLogger()
logger.setLevel(logging.INFO)

logger.info("CCXT version: %s" % ccxt.__version__)
#AWS parameter store usage is optional, and can be overridden with environment variables
psconf=yacgb_aws_ps(with_decryption=False)
#OHLCV table lookup cache
olcache=ohlcvLookup()

list_gbotids = re.compile('/gbotids$')
all_gbotids = re.compile('/allgbotids$')
get_gbotid = re.compile('/gbotid/([-\w]{1,36})$')

def lambda_handler(event, context):
    run_start = datetime.datetime.now(timezone.utc)
    global psconf

    psconf.collect()
    
    response = {}
    gbotid_match = get_gbotid.search(event["path"])
    if gbotid_match:
        #get details of a specific gbotid
        response['status'] = 'ok'
        gbotid = gbotid_match.group(1)
        gr = GbotRunner(gbotid)
        response.update(gr.gbot_dict)
        #get ohlcv
        nowbdt = BacktestDateTime()
        lookup = olcache.get_candles(gr.gbot.exchange, gr.gbot.market_symbol, '1h', nowbdt.dtstf('1h'), -1800)
        i = Indicators(lookup.aggregate('6h'))
        response.update(i.ca_dict)
        #get orders
        o = OrdersGet(gbotid)
        response.update(o.orders_dict)

    elif all_gbotids.search(event["path"]):
        #list all gbotids (in parameter store)
        response['status'] = 'ok'
        response['gbotids'] = []
        for g in Gbot.scan():
            response['gbotids'].append(g.gbotid)
            
    elif list_gbotids.search(event["path"]):
        #list all SSM gbotids (in parameter store)
        response['status'] = 'ok'
        response['gbotids'] = psconf.shuffled_gbotids
        
    else:
        response['status'] = 'error'
    
    #response['gbotids'] = gbotids
    logger.info(response)

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