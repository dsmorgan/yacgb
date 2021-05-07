## https://github.com/dsmorgan/yacgb

import ccxt
import time
import datetime
from datetime import timezone
import logging
import os
import sys

#from model.orders import Orders
#from yacgb.lookup import OrderBookLookup
#from yacgb.bdt import BacktestDateTime
from yacgb.awshelper import yacgb_aws_ps
from yacgb.gbotrunner import GbotRunner
from yacgb.util import base_symbol, quote_symbol, event2config, configsetup

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#AWS parameter store usage is optional, and can be overridden with environment variables
psconf=yacgb_aws_ps()


def lambda_handler(event, context):
    run_start = datetime.datetime.now(timezone.utc)
    #load the configuration to use for backtest from environment variables and event input
    config = event2config(event, psconf.exch, must_match=True)
    
    myexch = eval ('ccxt.%s ()' % config['exchange'])
    myexch.apiKey = psconf.exch_apikey[config['exchange']]
    myexch.secret = psconf.exch_secret[config['exchange']]
    myexch.enableRateLimit = False
    myexch.load_markets()
    
    
    #grab some things from the config
    bs = base_symbol(config['market_symbol'])
    qs = quote_symbol(config['market_symbol'])
    #start = BacktestDateTime(config['backtest_start'])
    #end = BacktestDateTime(config['backtest_end'])
    #lookup = OrderBookLookup(config['exchange'], config['market_symbol'])
    #TODO: this shouldn't start at hour, necessarily
    #lookup.getcandle(stime=start.dtshour())
    # Get makerfee and feecurrency
    market = myexch.market(config['market_symbol'])
    # Get current ticker
    fticker =  myexch.fetchTicker(config['market_symbol'])
    config = configsetup(config, fticker['last'])
    logger.info(config)
    # Get the balance info from this account
    balance = myexch.fetchBalance(params = {})

    base_total = balance[bs]['total']
    base_free = balance[bs]['free']
    quote_total = balance[qs]['total']
    quote_free = balance[qs]['free']
    logger.info ('base ' + bs + ' ' + str(balance[bs]))
    logger.info ('quote ' + qs + ' ' + str(balance[qs]))
    #Test for fetchOpenOrders
    if quote_free == None:
        # Because of this exchange, we can't tell what orders are open that are 
        #  associated with this market, so we need to query for all open orders
        qsymbol = None
    else:
        qsymbol = config['market_symbol']
    #TODO: override the config settings of these
    openorders = myexch.fetchOpenOrders(symbol=qsymbol)
    # start_base and start_quote
    config['start_quote'] = quote_total
    config['start_base'] = base_total
    for order in openorders:
        logger.info ("Open Order: " + order['id'] + ' ' +order['symbol'] + ' ' + str(myexch.amount_to_precision(config['market_symbol'], order['amount'])) + ' @ ' 
                + str(order['price']) + ' ' + order['type'] + ' ' + order['side'] )
        if (order['type'] == 'limit'):
            if (order['side'] == 'buy'):
                # start_base and start_quote
                config['start_quote'] -= order['amount'] * order['price']
            elif ((order['symbol'] == market_symbol) and (order['side'] == 'sell')):
                # start_base and start_quote
                config['start_base'] -= order['amount']
    # start_base and start_quote
    logger.info ("calculated from open orders: free base %f %s, free quote %f %s" % 
                (config['start_base'], bs, config['start_quote'], qs))
                    
    # Get makerfee and feecurrency
    market = myexch.market(config['market_symbol'])
    # Get start_ticker - in the case of live, use the current last ticker. But for backtrace you need to use the 1st ticker
    fticker =  myexch.fetchTicker(config['market_symbol'])
    logging.info ("market %s: last %f makerfee %f feecurrency %s" % (config['market_symbol'], fticker['last'], market['maker'], market['quote'])) 
    
    # create new Gbot

    ##TODO: make sure that start_base and start_quote are coming from the right place
        
    x = GbotRunner(None, config['exchange'], config['market_symbol'],  
                grid_spacing=config['grid_spacing'], total_quote=config['total_quote'], 
                max_ticker=config['max_ticker'], min_ticker=config['min_ticker'], reserve=config['reserve'],
                start_ticker=fticker['last'], 
                start_base=config['start_base'], start_quote=config['start_quote'], 
                makerfee=market['maker'], takerfee=market['taker'], feecurrency=market['quote'])
        

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
    for gridstep in x.grid_array:
        if (gridstep.mode == 'buy' and gridstep.ex_orderid == None):
            logging.info("%d limit %s base quantity %f @ %f" % (gridstep.step, gridstep.mode, gridstep.buy_base_quantity, gridstep.ticker))
            gridorder = myexch.createLimitBuyOrder (config['market_symbol'], gridstep.buy_base_quantity, gridstep.ticker)
            logging.info("exchange %s id %s type %s side %s" % (config['exchange'], gridorder['id'], gridorder['type'], gridorder['side']))
            gridstep.ex_orderid=config['exchange'] + '_' + gridorder['id']
            x.save()
        elif (gridstep.mode == 'sell'and gridstep.ex_orderid == None):
            logging.info("%d limit %s base quantity %f @ %f" % (gridstep.step, gridstep.mode, gridstep.sell_quote_quantity, gridstep.ticker))
            gridorder = myexch.createLimitSellOrder (config['market_symbol'], gridstep.sell_quote_quantity, gridstep.ticker)
            logging.info("exchange %s id %s type %s side %s" % (config['exchange'], gridorder['id'], gridorder['type'], gridorder['side']))
            gridstep.ex_orderid=config['exchange'] + '_' + gridorder['id']
            x.save()
            
    x.totals()
    run_end = datetime.datetime.now(timezone.utc)
    logging.info('RUN TIME: %s', str(run_end-run_start))
    
    response = {}
    response['gbotid'] = x.gbot.gbotid
    logging.info(response)
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
 

    





    
    
    