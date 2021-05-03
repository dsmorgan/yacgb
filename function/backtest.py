## https://github.com/dsmorgan/yacgb

import ccxt
import time
import datetime
from datetime import timezone
import logging
import os
import sys

#from model.orders import Orders
from yacgb.lookup import OrderBookLookup
from yacgb.bdt import BacktestDateTime
from yacgb.gbotrunner import GbotRunner
from yacgb.util import base_symbol, quote_symbol, event2config, get_os_env, configsetup

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environmental passed comfiguration
exchange = get_os_env('EXCHANGE', required=False)
market_symbol = get_os_env('MARKET_SYMBOL', required=False)
api_key = get_os_env('API_KEY', required=False)
secret = get_os_env('SECRET', required=False, encrypted=True)


def backtest(event, context):
    run_start = datetime.datetime.now(timezone.utc)
    #load the configuration to use for backtest from environment variables and event input
    config = event2config(event, exchange, market_symbol)
    #grab some things from the config
    bs = base_symbol(config['market_symbol'])
    qs = quote_symbol(config['market_symbol'])
    start = BacktestDateTime(config['backtest_start'])
    end = BacktestDateTime(config['backtest_end'])
    lookup = OrderBookLookup(config['exchange'], config['market_symbol'])
    #TODO: this shouldn't start at hour, necessarily
    lookup.getcandle(stime=start.dtshour())
    #Some configuration is dependant upon the initial value when the backtest starts, pass that and also some validation
    config = configsetup(config, lookup.open)

    #print(config)
    #exit()
    # test for fetchBalance
    if config['live_balance']:
        myexch = eval ('ccxt.%s ()' % config['exchange'])
        myexch.apiKey = api_key
        myexch.secret = secret
        myexch.enableRateLimit = True
        myexch.load_markets()
        
        # Get makerfee and feecurrency
        market = myexch.market(config['market_symbol'])
        # Get the balance info from this account
        balance = myexch.fetchBalance (params = {})

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
            qsymbol = market_symbol
        #TODO: override the config settings of these
        openorders = myexch.fetchOpenOrders(symbol=qsymbol)
        # start_base and start_quote
        calc_quote_free = quote_total
        calc_base_free = base_total
        for order in openorders:
            logger.info ("Open Order: " + order['id'] + ' ' +order['symbol'] + ' ' + str(myexch.amount_to_precision(market_symbol, order['amount'])) + ' @ ' 
                    + str(order['price']) + ' ' + order['type'] + ' ' + order['side'] )
            if (order['type'] == 'limit'):
                if (order['side'] == 'buy'):
                    # start_base and start_quote
                    calc_quote_free -= order['amount'] * order['price']
                elif ((order['symbol'] == market_symbol) and (order['side'] == 'sell')):
                    # start_base and start_quote
                    calc_base_free -= order['amount']
        # start_base and start_quote
        logger.info ("calculated from open orders: free base %f %s, free quote %f %s" % 
                    (calc_base_free, bs, calc_quote_free, qs))


    #for backtesting, use the 1st ticker (lookup.open)
    logging.info ("market %s: last %f makerfee %f feecurrency %s" % (config['market_symbol'], lookup.open, config['makerfee'], config['makerfee']))
    
    x = GbotRunner(None, config['exchange'], config['market_symbol'],  
                    grid_spacing=config['grid_spacing'], total_quote=config['total_quote'], 
                    max_ticker=config['max_ticker'], min_ticker=config['min_ticker'], reserve=config['reserve'],
                    start_ticker=lookup.open, start_base=config['start_base'], start_quote=config['start_quote'], 
                    makerfee=config['makerfee'], takerfee=config['takerfee'], feecurrency=config['feecurrency'])
    
    while end.laterthan(start):
        #print (start.dtshour())
        #TODO: we need to pass the timestamp along with the price, so that the timestamp can be captured with the buy/sell
        lookup.getcandle(stime=start.dtshour())
        x.next_ticker(lookup.open)
        x.next_ticker(lookup.low)
        x.next_ticker(lookup.high)
        x.next_ticker(lookup.close)
        start.addhour()
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

    print (backtest(event, None))
