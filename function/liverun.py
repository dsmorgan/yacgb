## https://github.com/dsmorgan/yacgb

import ccxt
import time
import datetime
from datetime import timezone
import logging
import os
import sys
import random

from model.orders import Orders
#from yacgb.lookup import OrderBookLookup
#from yacgb.bdt import BacktestDateTime
from yacgb.awshelper import yacgb_aws_ps
from yacgb.gbotrunner import GbotRunner
from yacgb.util import base_symbol, quote_symbol, orderid
from yacgb.ccxthelper import CandleTest

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info("CCXT version: %", ccxt.__version__)
#AWS parameter store usage is optional, and can be overridden with environment variables
psconf=yacgb_aws_ps()

myexch = {}
for e in psconf.exch:
    myexch[e] = eval ('ccxt.%s ()' % e)
    myexch[e].apiKey = psconf.exch_apikey[e]
    myexch[e].secret = psconf.exch_secret[e]
    myexch[e].password = psconf.exch_password[e]
    myexch[e].enableRateLimit = False
    myexch[e].load_markets()


def lambda_handler(event, context):
    run_start = datetime.datetime.now(timezone.utc)
    global myexch
    global psconf
    
    random.shuffle(psconf.gbotids)
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
        
    
        #TODO use the last timestamp from the Gbot to determine the right since, need to find how to since based on closetm NOT opentm
        corders = myexch[exchange].fetchClosedOrders(market_symbol, since=x.gbot.last_order_ts)
        logger.info("fetched %d closed orders to review (since %d)" % (len(corders), x.gbot.last_order_ts))
        
        step_list=[]
        reset_list=[]
        
        #Look at closed orders, and match against what is in gbot
        for corder in corders:
            logger.debug("closed order: %s, timestamp: %d" % (corder['id'], corder['timestamp']))
            matched_step = x.check_id(exchange, corder['id'])

            if matched_step != None:
                if corder['status'] == 'canceled':
                    #add it to the list to reset the order
                    reset_list.append(matched_step)
                    logger.warning("Canceled order (%d), resetting: %s %s" % (matched_step, exchange, corder['id']))
                    #setting this grid to None will trigger it to be reset
                    x.grid_array[matched_step].ex_orderid = None
                    #don't do anything else with this step, next order
                else:
                    #add it to list to recalculate the grid, and replace the buy/sell w/ the approproate sell/buy
                    step_list.append(matched_step)
                    ###This should be seperated to a class
                    if not Orders.exists():
                        Orders.create_table(read_capacity_units=3, write_capacity_units=3, wait=True)
                        logger.info('Created Dynamodb table Orders')
                    #TODO the timestamp is when the order was placed, NOT when the order completed. Need to map that to the correct field
                    # Problem is, this isn't consistent between exchanges
                    ####TODO bug related to fee.cost and fee.currency not always being defined. Where do we get this? Might have to set to zeros for now
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
        # This reconfigures the grid, moving the current "NONE" grid either up or down and the sell/buy limits are not
        for step in step_list:
            x.reset(x.grid_array[step].ticker, '*')
            
        #Get the current ticker and double check that we aren't too far off from the grid step
        fticker = CandleTest(myexch[exchange].fetchOHLCV(market_symbol, '1m', limit=3))
        logger.info("%s %s last %f h/l %f/%f", exchange, market_symbol, fticker.last, fticker.high, fticker.low)
        if x.test_slortp(fticker.last, '*'):
            #State has either changed from active, or was already not active
            x.save()
            for gridstep in x.grid_array:
                #cancel each open order
                if gridstep.ex_orderid != None:
                    try:
                        logger.info("%d> canceling order %s" % (gridstep.step, gridstep.ex_orderid))
                        gridcancel = myexch[exchange].cancelOrder(orderid(gridstep.ex_orderid))
                        logger.info(str(gridcancel))
                    except ccxt.OrderNotFound:
                        logger.warning("%s OrderNotFound" % gridstep.ex_orderid)
                    gridstep.ex_orderid = None
                    
            #additional step for stop_loss to also sell off all
            if x.gbot.state == 'stop_loss':
                #TODO: How do we retry this and check that it succeded?
                x.gbot.state = 'stop_loss_sold_all'
                #TODO we probably need to get the  amount to sell from adding up all of the sell limits in the grid. base_balance isn't correct
                logger.info("Stop Loss, Sell All %s (%f)" %(market_symbol, x.gbot.base_balance))
                sellall = myexch[exchange].createMarketSellOrder(market_symbol, x.gbot.base_balance)
                logger.info(str(sellall))
                x.save()
                
        #TODO: Check if the state is now 'stop_loss' or 'take_profit', ensure that all open orders are canceled. 
        ## If stop_loss, then we also need to add up all the base quantity and market sell it.
        ## Each time, we should check to make sure that all orders have been canceled safely. 
        
        
        # Find all grids that are buy/sell, but don't have an order_id. Setup the new limit orders
        # Setup each Buy and Sell Limit, if we are still active
        if x.gbot.state == 'active':
            # This can be mostly pushed into gbotrunner
            for gridstep in x.grid_array:
                if (gridstep.mode == 'buy' and gridstep.ex_orderid == None):
                    logger.info("%d limit %s base quantity %f @ %f" % (gridstep.step, gridstep.mode, gridstep.buy_base_quantity, gridstep.ticker))
                    gridorder = myexch[exchange].createLimitBuyOrder (market_symbol, gridstep.buy_base_quantity, gridstep.ticker)
                    logger.info("exchange %s id %s type %s side %s" % (exchange, gridorder['id'], gridorder['type'], gridorder['side']))
                    gridstep.ex_orderid=exchange + '_' + gridorder['id']
                    x.save()
                elif (gridstep.mode == 'sell'and gridstep.ex_orderid == None):
                    logger.info("%d limit %s base quantity %f @ %f" % (gridstep.step, gridstep.mode, gridstep.sell_quote_quantity, gridstep.ticker))
                    gridorder = myexch[exchange].createLimitSellOrder (market_symbol, gridstep.sell_quote_quantity, gridstep.ticker)
                    logger.info("exchange %s id %s type %s side %s" % (exchange, gridorder['id'], gridorder['type'], gridorder['side']))
                    gridstep.ex_orderid=exchange + '_' + gridorder['id']
                    x.save()
        
        #TODO: set timestamp as well, so to check since last timestamp found. Or is that even possible?
        
        #TODO: Only print the grid if we've changed something.
        if (len(step_list) + len (reset_list) > 0):
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
        
        