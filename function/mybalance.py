## https://github.com/dsmorgan/yacgb

import ccxt
import time
import datetime
from datetime import timezone
import logging
import os
import sys
from collections import OrderedDict

from yacgb.lookup import OrderBookLookup
from yacgb.bdt import BacktestDateTime
from yacgb.awshelper import yacgb_aws_ps
from yacgb.util import base_symbol, quote_symbol

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#AWS parameter store usage is optional, and can be overridden with environment variables
psconf=yacgb_aws_ps()

myexch = {}
for e in psconf.exch:
    myexch[e] = eval ('ccxt.%s ()' % e)
    myexch[e].enableRateLimit = False
    myexch[e].apiKey = psconf.exch_apikey[e]
    myexch[e].secret = psconf.exch_secret[e]
    myexch[e].password = psconf.exch_password[e]
    myexch[e].load_markets()


def lambda_handler(event, context):
    run_start = datetime.datetime.now(timezone.utc)
    global myexch
    global psconf
    response = {}
    orderedr = OrderedDict()
    agg = {}
    tt = 0
    
    ts = BacktestDateTime()
    
    for ex in myexch:
        balance = myexch[ex].fetchBalance (params = {})
        total = balance['total']
        e = event.get(ex+'_'+'total')
        agg[ex+'_'+'total'] = [0,1, 0, e[0], 0, e[1]]
        for t in total.copy():
            if total[t] != 0:
                if t == 'USD':
                    price = 1
                else:
                    lookup = OrderBookLookup(ex, t+'/USD')
                    lookup.getcandle(timeframe='1h', stime=ts.dtshour())
                    price = lookup.close
                e = event.get(ex+'_'+t)
                    
                
                response[ex+'_'+t] = [round(total[t],5), price, round(total[t]*price,2), e[0], 0, e[1]]
                agg[ex+'_'+'total'][0] = agg[ex+'_'+'total'][0]+total[t]*price
                agg[ex+'_'+'total'][2] = round(agg[ex+'_'+'total'][2]+total[t]*price, 2)
        tt+=round(agg[ex+'_'+'total'][0], 2)
    e = event.get('total_total')    
    agg['total_total'] = [tt, 1,tt ,e[0] ,0 ,e[1]]
    #response.update(agg)
    
    for e in response:
        if response[e][3] == 0:
            response[e][4] = 1
        else:
            response[e][4] = round((response[e][2] - response[e][3])/response[e][3], 3)
            
    for a in agg:
        if agg[a][3] == 0:
            agg[a][4] == 1
        else:
            agg[a][4] = round((agg[a][2] - agg[a][3])/agg[a][3], 3)
    
    # order based on highest to lowest holdings       
    while len(response) > 0:
        high = -1
        key = None
        for k in response:
            if response[k][2] > high:
                key = k
                high = response[k][2]
        orderedr[key] = response[key]
        del response[key]
            
    
    #orderedr.update(response)
    orderedr.update(agg)
    return (orderedr)

if __name__ == "__main__":
    import json, pprint
    pp = pprint.PrettyPrinter(indent=1)
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s', 
                            datefmt='%Y%m%d %H:%M:%S')
    if (os.environ.get('DYNAMODB_HOST') == None):
        print ('DYNAMODB_HOST not set')
        exit()
      
    print ('DYNAMODB_HOST=' + os.environ.get('DYNAMODB_HOST'))
    
    if (len(sys.argv) != 2):
        print ("error: missing event json file")
        exit(1)
    with open(sys.argv[1]) as json_file:
        event = json.load(json_file)
    
    pp.pprint (lambda_handler(event, None))
        
