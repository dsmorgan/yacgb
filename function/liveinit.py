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
#from yacgb.lookup import OrderBookLookup
#from yacgb.bdt import BacktestDateTime
from yacgb.gbotrunner import GbotRunner
from yacgb.util import base_symbol, quote_symbol, event2config, configsetup
from yacgb.ccxthelper import BalanceCalc

logger=logging.getLogger()
logger.setLevel(logging.INFO)

logger.info("CCXT version: %s" % ccxt.__version__)
#AWS parameter store usage is optional, and can be overridden with environment variables
psconf=yacgb_aws_ps()

def lambda_handler(event, context):
    run_start = datetime.datetime.now(timezone.utc)
    #load the configuration to use for backtest from environment variables and event input
    config = event2config(event, psconf.exch, must_match=True)
    #grab some things from the config
    bs = base_symbol(config['market_symbol'])
    qs = quote_symbol(config['market_symbol'])
    
    #configure ccxt to access private account on an axchange
    myexch = eval ('ccxt.%s ()' % config['exchange'])
    myexch.setSandboxMode(psconf.exch_sandbox[config['exchange']])
    myexch.apiKey = psconf.exch_apikey[config['exchange']]
    myexch.secret = psconf.exch_secret[config['exchange']]
    myexch.password = psconf.exch_password[config['exchange']]
    myexch.enableRateLimit = False
    myexch.load_markets()
    
    # Get current ticker
    fticker =  myexch.fetchTicker(config['market_symbol'])
    config = configsetup(config, fticker['last'])
    
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
    
    # create new Gbot    
    x = GbotRunner(config=config)

    #Grab the last order before we setup new orders, to borrow the timestamp
    closedorders = myexch.fetchClosedOrders(symbol=config['market_symbol'],limit=1)
    if len(closedorders) < 1:
        x.gbot.last_order_ts = 0
    else:
        x.gbot.last_order_ts = closedorders[0]['timestamp']
    x.save() 
    
    # settle any buy/sell required to get the right amount of starting base and quote
    #exit()
    
    # Setup each Buy and Sell Limit
    for gridstep in x.gbot.grid:
        if (gridstep.mode == 'buy' and gridstep.ex_orderid == None):
            logger.info("%d limit %s base quantity %f @ %f" % (gridstep.step, gridstep.mode, gridstep.buy_base_quantity, gridstep.ticker))
            gridorder = myexch.createLimitBuyOrder (config['market_symbol'], gridstep.buy_base_quantity, gridstep.ticker)
            logger.info("exchange %s id %s type %s side %s" % (config['exchange'], gridorder['id'], gridorder['type'], gridorder['side']))
            gridstep.ex_orderid=config['exchange'] + '_' + gridorder['id']
            x.save()
        elif (gridstep.mode == 'sell'and gridstep.ex_orderid == None):
            logger.info("%d limit %s base quantity %f @ %f" % (gridstep.step, gridstep.mode, gridstep.sell_base_quantity, gridstep.ticker))
            gridorder = myexch.createLimitSellOrder (config['market_symbol'], gridstep.sell_base_quantity, gridstep.ticker)
            logger.info("exchange %s id %s type %s side %s" % (config['exchange'], gridorder['id'], gridorder['type'], gridorder['side']))
            gridstep.ex_orderid=config['exchange'] + '_' + gridorder['id']
            x.save()
            
    x.totals()
    run_end = datetime.datetime.now(timezone.utc)
    logger.info('RUN TIME: %s', str(run_end-run_start))
    
    response = {}
    response['gbotid'] = x.gbot.gbotid
    logger.info(response)
    return (response)
    

    
if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s', 
                            datefmt='%Y%m%d %H:%M:%S', filename='bot.log')
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
 

    





    
    
    