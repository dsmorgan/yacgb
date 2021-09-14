## https://github.com/dsmorgan/yacgb

import ccxt
import time
import datetime
from datetime import timezone
import logging
import os
import sys
import random

from model.orders import Orders, orders_init
#from yacgb.lookup import OrderBookLookup
#from yacgb.bdt import BacktestDateTime
from yacgb.awshelper import yacgb_aws_ps
from yacgb.gbotrunner import GbotRunner
from yacgb.util import base_symbol, quote_symbol, orderid
#from yacgb.ccxthelper import CandleTest
from yacgb.lookup import ohlcvLookup
from yacgb.bdt import BacktestDateTime
from yacgb.indicators import Indicators

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info("CCXT version: %s" % ccxt.__version__)
#AWS parameter store usage is optional, and can be overridden with environment variables
psconf=yacgb_aws_ps()
#OHLCV table lookup cache
olcache = ohlcvLookup()

myexch = {}
for e in psconf.exch:
    myexch[e] = eval ('ccxt.%s ()' % e)
    myexch[e].apiKey = psconf.exch_apikey[e]
    myexch[e].secret = psconf.exch_secret[e]
    myexch[e].password = psconf.exch_password[e]
    myexch[e].enableRateLimit = False
    myexch[e].load_markets()

orders_init()

def lambda_handler(event, context):
    run_start = datetime.datetime.now(timezone.utc)
    global myexch
    global psconf
    
    random.shuffle(psconf.gbotids)
    response = {}
    response['gbotids'] = psconf.gbotids
    logger.info(response)

    for gbotid in psconf.gbotids:
        #load Gbot, TODO: need to handle if it can't be found
        x = GbotRunner(gbotid=gbotid)
        exchange=x.gbot.exchange
        market_symbol=x.gbot.market_symbol
        
        bs = base_symbol(market_symbol)
        qs = quote_symbol(market_symbol)
        
        corders =[]

        # Regardless of state, we'll check for closed orders only if there are open orders for this gbot
        if x.open_orders:
            #TODO use the last timestamp from the Gbot to determine the right since, need to find how to since based on closetm NOT opentm
            corders = myexch[exchange].fetchClosedOrders(market_symbol, since=x.gbot.last_order_ts)
            logger.info("fetched %d closed orders to review (since %d)" % (len(corders), x.gbot.last_order_ts))
        
        x.closed_adjust(x.ordersmatch(corders), '*')
        
        timeframe = '1m'
        nowbdt = BacktestDateTime()
        lookup = olcache.get_candles(exchange, market_symbol, timeframe, nowbdt.dtstf(timeframe), -300)
        ts_bdt = BacktestDateTime(timestamp=lookup.candles_array[-1][0])
        last_bdt = BacktestDateTime(lookup.last)
        logger.info("%s %s %s tsdiffsec: %f difflastsec: %f" %(exchange, market_symbol, lookup, ts_bdt.diffsec(nowbdt), last_bdt.diffsec(nowbdt)))
        # check here how far behind the last candle is, and when the record was written
        if ts_bdt.diffsec(nowbdt) < -29:
            lookup.update(myexch[exchange].fetchOHLCV(market_symbol, timeframe, limit=10))
            ts_bdt = BacktestDateTime(timestamp=lookup.candles_array[-1][0])
            logger.info("<U> %s %s %s tsdiffsec: %f" %(exchange, market_symbol, lookup, ts_bdt.diffsec(nowbdt)))
        #
        i = Indicators(lookup.candles_array)
        logger.info("%s %s dc:%f %s" %(exchange, market_symbol, lookup.dejitter_close(), i))
        #
        lll = lookup.aggregate('3m')
        iii = Indicators(lll.candles_array)
        logger.info("%s %s %s tsdiffsec: %f" %(exchange, market_symbol, lll, ts_bdt.diffsec(nowbdt)))
        logger.info("%s %s dc:%f %s" %(exchange, market_symbol, lll.dejitter_close(), iii))
        #
        lllll = lookup.aggregate('5m')
        iiiii = Indicators(lllll.candles_array)
        logger.info("%s %s %s tsdiffsec: %f" %(exchange, market_symbol, lllll, ts_bdt.diffsec(nowbdt)))
        logger.info("%s %s dc:%f %s" %(exchange, market_symbol, lllll.dejitter_close(), iiiii))
        #
        tenl = lookup.aggregate('10m')
        teni = Indicators(tenl.candles_array)
        logger.info("%s %s %s tsdiffsec: %f" %(exchange, market_symbol, tenl, ts_bdt.diffsec(nowbdt)))
        logger.info("%s %s dc:%f %s" %(exchange, market_symbol, tenl.dejitter_close(), teni))
        
        if x.test_slortp(lookup.dejitter_close(), lookup.high, lookup.low, '*'):
            x.save()
            #State has either changed from active, or was already not active
            for gridstep in x.gbot.grid:
                #cancel each open order
                gridcancel = None
                if gridstep.ex_orderid != None:
                    try:
                        logger.info("%d> canceling order %s" % (gridstep.step, gridstep.ex_orderid))
                        #Apparently some exchanges (binanceus) require the market_symbol in additon to the orderid
                        gridcancel = myexch[exchange].cancelOrder(orderid(gridstep.ex_orderid), market_symbol)
                        logger.info(str(gridcancel))
                    except ccxt.OrderNotFound:
                        logger.warning("%s OrderNotFound: %s" % (gridstep.ex_orderid, gridcancel))
                    gridstep.ex_orderid = None
            #Need to save again
            x.save()
                    
            #additional step for stop_loss and profit_protect to also sell off all held base. take_profit generally
            #shouldn't get triggered unless we are above the top of the grid, but doesn't hurt to attempt to sell if we somehow have some
            if x.gbot.state == 'stop_loss' or x.gbot.state == 'take_profit' or x.gbot.state == 'profit_protect':
                #TODO: How do we retry this and check that it succeded?
                x.gbot.state = x.gbot.state + '_sold_all'
                #TODO we probably need to get the  amount to sell from adding up all of the sell limits in the grid. base_balance isn't correct
                ttsell = x.total_sell_b()
                logger.info("State: %s Total To Sell %f" % (x.gbot.state, ttsell))
                if round(ttsell, 4) > 0:
                    logger.info("Market Sell All %s (%f)" %(market_symbol, ttsell))
                    sellall = myexch[exchange].createMarketSellOrder(market_symbol, ttsell)
                    logger.info(str(sellall))
                x.totals()
                x.save()
        
        # Find all grids that are buy/sell, but don't have an order_id. Setup the new limit orders
        # Setup each Buy and Sell Limit, if we are still active
        if x.gbot.state == 'active':
            x.save()
            # This can be mostly pushed into gbotrunner
            for gridstep in x.gbot.grid:
                if (gridstep.mode == 'buy' and gridstep.ex_orderid == None):
                    logger.info("%d limit %s base quantity %f @ %f" % (gridstep.step, gridstep.mode, gridstep.buy_base_quantity, gridstep.ticker))
                    gridorder = myexch[exchange].createLimitBuyOrder (market_symbol, gridstep.buy_base_quantity, gridstep.ticker)
                    logger.info("exchange %s id %s type %s side %s" % (exchange, gridorder['id'], gridorder['type'], gridorder['side']))
                    gridstep.ex_orderid=exchange + '_' + gridorder['id']
                    x.save()
                elif (gridstep.mode == 'sell'and gridstep.ex_orderid == None):
                    logger.info("%d limit %s base quantity %f @ %f" % (gridstep.step, gridstep.mode, gridstep.sell_base_quantity, gridstep.ticker))
                    gridorder = myexch[exchange].createLimitSellOrder (market_symbol, gridstep.sell_base_quantity, gridstep.ticker)
                    logger.info("exchange %s id %s type %s side %s" % (exchange, gridorder['id'], gridorder['type'], gridorder['side']))
                    gridstep.ex_orderid=exchange + '_' + gridorder['id']
                    x.save()
        
        #TODO: set timestamp as well, so to check since last timestamp found. Or is that even possible?
        
        # Only print the grid if we've changed something.
        #if (len(closed_list) + len (reset_list) > 0):
        x.totals()
        ## END OF GBOT LOOP
        
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