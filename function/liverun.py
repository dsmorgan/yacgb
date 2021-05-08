## https://github.com/dsmorgan/yacgb

import ccxt
import time
import datetime
from datetime import timezone
import logging
import os
import sys

from model.orders import Orders
#from yacgb.lookup import OrderBookLookup
#from yacgb.bdt import BacktestDateTime
from yacgb.awshelper import yacgb_aws_ps
from yacgb.gbotrunner import GbotRunner
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
    myexch[e].load_markets()


def lambda_handler(event, context):
    run_start = datetime.datetime.now(timezone.utc)
    global myexch
    global psconf
    
    response = {}
    response['gbotids'] = psconf.gbotids
    logger.info(response)

    for gbotid in psconf.gbotids:
        #load Gbot
        x = GbotRunner(gbotid=gbotid)
        exchange=x.gbot.exchange
        market_symbol=x.gbot.market_symbol
        
        bs = base_symbol(market_symbol)
        qs = quote_symbol(market_symbol)
    
    
        #fetchClosedOrders([symbol[, since[, limit[, params]]]])
        #>>> corders = myexch.fetchClosedOrders(market_symbol, since=1618235374000)
        #>>> corders
        #[{'id': 'OS63K7-6I4HL-4HIFIS', 'clientOrderId': '0', 'info': {'id': 'OS63K7-6I4HL-4HIFIS', 'refid': None, 'userref': 0, 'status': 'closed', 
        #'reason': None, 'opentm': 1618235374.1276, 'closetm': 1618239581.8319, 'starttm': 0, 'expiretm': 0, 'descr': {'pair': 'LTCUSD', 'type': 'buy', 
        #'ordertype': 'limit', 'price': '246.11', 'price2': '0', 'leverage': 'none', 'order': 'buy 2.00000000 LTCUSD @ limit 246.11', 'close': ''}, 
        #'vol': '2.00000000', 'vol_exec': '2.00000000', 'cost': '492.22', 'fee': '0.78', 'price': '246.11', 'stopprice': '0.00000', 'limitprice': 
        #'0.00000', 'misc': '', 'oflags': 'fciq'}, 'timestamp': 1618235374127, 'datetime': '2021-04-12T13:49:34.127Z', 'lastTradeTimestamp': None, 
        #'status': 'closed', 'symbol': 'LTC/USD', 'type': 'limit', 'timeInForce': None, 'postOnly': None, 'side': 'buy', 'price': 246.11, 'stopPrice': 0.0, 
        #'cost': 492.22, 'amount': 2.0, 'filled': 2.0, 'average': 246.11, 'remaining': 0.0, 'fee': {'cost': 0.78, 'rate': None, 'currency': 'USD'}, 
        #'trades': None}]
        #>>> corders[0]['id']
        #'OS63K7-6I4HL-4HIFIS'
    
        #TODO use the last timestamp from the Gbot to determine the right since, need to find how to since based on closetm NOT opentm
        corders = myexch[exchange].fetchClosedOrders(market_symbol, since=x.gbot.last_order_ts)
        logger.info("fetched %d closed orders to review (since %d)" % (len(corders), x.gbot.last_order_ts))
        
        step_list=[]
        reset_list=[]
        
        for corder in corders:
            #logger.info("closed order: %s, timestamp: %d" % (corder['id'], corder['timestamp']))
            matched_step = x.check_id(exchange, corder['id'])

            if matched_step != None:
                if corder['status'] == 'canceled':
                    reset_list.append(matched_step)
                    logger.warning("Canceled order (%d), resetting: %s %s" % (matched_step, exchange, corder['id']))
                    #setting this grid to None will trigger it to be reset
                    x.grid_array[matched_step].ex_orderid = None
                    #don't do anything else with this step, next order
                else:
                    #add it to list to reset grid
                    step_list.append(matched_step)
                    if not Orders.exists():
                        Orders.create_table(read_capacity_units=3, write_capacity_units=3, wait=True)
                        logger.info('Created Dynamodb table Orders')
                    #TODO the timestamp is when the order was placed, NOT when the order completed. Need to map that to the correct field
                    ord = Orders(exchange+'_'+corder['id'], exchange=exchange, accountid=None, gbotid=x.gbot.gbotid, market_symbol=corder['symbol'], timestamp=corder['timestamp'], 
                        timestamp_st=datetime.datetime.fromtimestamp(corder['timestamp']/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                        side=corder['side'], type=corder['type'], status=corder['status'], cost=corder['cost'], price=corder['price'], amount=corder['amount'], 
                        average=corder['average'], fee_cost=corder['fee']['cost'], fee_currency=corder['fee']['currency'], raw=corder
                        )
                    #x.gbot.last_order_ts=corder['timestamp'] <--this isn't correct, need to find a better solution
                    #TODO: There doesn't seem to be a safe way to filter the corder list based on 'since'.
                    ord.save()
    
        logger.info("step_list %s reset_list %s" % (str(step_list), str(reset_list)))
        # sequence list, in case there were multiple orders that matched
        ## assume that they come in the right order for now TODO, these are NOT ordered
        
        # apply x.reset() against each grid (step_list) that matched an order, ensure that resets the ex_orderid too
        for step in step_list:
            x.reset(x.grid_array[step].ticker)
            
        #TODO: We should get the current ticker and double check that we aren't too far off from the grid
        
        # Find all grids that are buy/sell, but don't have an order_id. Setup the new limit orders
        # Setup each Buy and Sell Limit
        for gridstep in x.grid_array:
            if (gridstep.mode == 'buy' and gridstep.ex_orderid == None):
                logging.info("%d limit %s base quantity %f @ %f" % (gridstep.step, gridstep.mode, gridstep.buy_base_quantity, gridstep.ticker))
                gridorder = myexch[exchange].createLimitBuyOrder (market_symbol, gridstep.buy_base_quantity, gridstep.ticker)
                logging.info("exchange %s id %s type %s side %s" % (exchange, gridorder['id'], gridorder['type'], gridorder['side']))
                gridstep.ex_orderid=exchange + '_' + gridorder['id']
                x.save()
            elif (gridstep.mode == 'sell'and gridstep.ex_orderid == None):
                logging.info("%d limit %s base quantity %f @ %f" % (gridstep.step, gridstep.mode, gridstep.sell_quote_quantity, gridstep.ticker))
                gridorder = myexch[exchange].createLimitSellOrder (market_symbol, gridstep.sell_quote_quantity, gridstep.ticker)
                logging.info("exchange %s id %s type %s side %s" % (exchange, gridorder['id'], gridorder['type'], gridorder['side']))
                gridstep.ex_orderid=exchange + '_' + gridorder['id']
                x.save()
        
        #TODO: set timestamp as well, so to check since last timestamp found. Or is that even possible?
        x.totals()
        
    run_end = datetime.datetime.now(timezone.utc)
    logger.info('RUN TIME: %s', str(run_end-run_start))
    return (response)

if __name__ == "__main__":
    logfile = 'bot.log'
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
        sleep_time = 60 - (time.time()-25) % 60
        logging.info("sleeping %f error count %d" %(sleep_time, error_count))
        time.sleep(sleep_time)
        
        