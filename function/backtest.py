## https://github.com/dsmorgan/yacgb

import ccxt
import time
import datetime
from datetime import timezone
import logging
import os
import sys

#from model.orders import Orders
from yacgb.awshelper import yacgb_aws_ps
from yacgb.lookup import OrderBookLookup
from yacgb.bdt import BacktestDateTime
from yacgb.gbotrunner import GbotRunner
from yacgb.util import base_symbol, quote_symbol, event2config, configsetup
from yacgb.ccxthelper import BalanceCalc

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info("CCXT version: %s" % ccxt.__version__)
#AWS parameter store usage is optional, and can be overridden with environment variables
psconf=yacgb_aws_ps()

def lambda_handler(event, context):
    run_start = datetime.datetime.now(timezone.utc)

    #load the configuration to use for backtest from environment variables and event input
    config = event2config(event, psconf.exch, must_match=True)
    #grab some things from the psconfig
    bs = base_symbol(config['market_symbol'])
    qs = quote_symbol(config['market_symbol'])
    start = BacktestDateTime(config['backtest_start'])
    end = BacktestDateTime(config['backtest_end'])
    timeframe = config['backtest_timeframe']
    lookup = OrderBookLookup(config['exchange'], config['market_symbol'])
    #If this returns zero, then might need to advance to see if we can find a valid OHLCV table entry
    while end.laterthan(start):
        lookup.getcandle(timeframe=timeframe, stime=start.dtstf(timeframe))
        if lookup.open != 0:
            break
        start.addtf(timeframe)
    #Some configuration is dependant upon the initial value when the backtest starts, pass that and also some validation
    config = configsetup(config, lookup.open)

    # test for fetchBalance
    if config['live_balance']:
        #configure ccxt to access private account on an axchange
        myexch = eval ('ccxt.%s ()' % config['exchange'])
        myexch.apiKey = psconf.exch_apikey[config['exchange']]
        myexch.secret = psconf.exch_secret[config['exchange']]
        myexch.password = psconf.exch_password[config['exchange']]
        myexch.enableRateLimit = False
        myexch.load_markets()
        
        # Get makerfee and takerfee, feecurrency is only seen on closedOrders
        market = myexch.market(config['market_symbol'])
        #override the config settings for maker & taker
        config['makerfee'] = market['maker']
        config['takerfee'] = market['taker']
        
        # Get the balance info from this account
        bal = BalanceCalc(myexch.fetchBalance(params = {}), bs, qs)

        # Get open orders from the account and calculate what quote and base are available
        bal.openOrdersCalc(myexch.fetchOpenOrders(symbol=bal.qsymbol()))
        
        # override the config settings of these from what we've calculated
        config['start_base'] = bal.calc_base_free
        config['start_quote'] = bal.calc_quote_free
    
    #log the translated config applied to the gbot    
    logger.info ("config: %s" % config)
    
    # create a new Gbot
    x = GbotRunner(config=config, type='backtest')
    
    #### backtest run START
    while end.laterthan(start):
        lookup.getcandle(timeframe=timeframe, stime=start.dtstf(timeframe))
        
        x.backtest(lookup.open, start.dtstf(timeframe))
        x.backtest(lookup.low, start.dtstf(timeframe))
        x.backtest(lookup.high, start.dtstf(timeframe))
        x.backtest(lookup.close, start.dtstf(timeframe))
        start.addtf(timeframe)
    x.save()    
    x.totals()
    #### backtest run END
    
    run_end = datetime.datetime.now(timezone.utc)
    logger.info('RUN TIME: %s', str(run_end-run_start))
    
    #Make the response the gbotid that was just created and backtested
    response = {}
    response['gbotid'] = x.gbot.gbotid
    logger.info(response)
    return (response)
    
if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s', 
                            datefmt='%Y%m%d %H:%M:%S', filename='backtest.log')
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