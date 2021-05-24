## https://github.com/dsmorgan/yacgb

import logging

logger = logging.getLogger(__name__)


class BalanceCalc:
    # Take input from a fetchBalance response
    def __init__(self, fetchBalanceResp, base_sym, quote_sym):
        self.bs = base_sym
        self.qs = quote_sym
        self.ms = self.bs + '/' + self.qs
        self.base_all = fetchBalanceResp[base_sym]
        logger.info ('base ' + self.bs + ' ' + str(self.base_all))
        self.quote_all = fetchBalanceResp[quote_sym]
        logger.info ('quote ' + self.qs + ' ' + str(self.quote_all))
        
        self.base_total = fetchBalanceResp[base_sym]['total']
        self.base_free = fetchBalanceResp[base_sym]['free']
        self.quote_total = fetchBalanceResp[quote_sym]['total']
        self.quote_free = fetchBalanceResp[quote_sym]['free']
        self.calc_base_free = self.base_total
        self.calc_quote_free = self.quote_total
        
    
    def qsymbol(self):
        #Test for fetchOpenOrders
        if self.quote_free == None:
            # Because of this exchange, we can't tell what orders are open that are 
            #  associated with this market, so we need to query for all open orders
            return (None)
        # Return market_symbol, but since we don't have that we re-generate it
        return (self.ms)
            
    def openOrdersCalc(self, openorders):      
        for order in openorders:
            logger.info ("Open Order: " + order['id'] + ' ' +order['symbol'] + ' ' +  str(order['amount']) + ' @ ' 
                    + str(order['price']) + ' ' + order['type'] + ' ' + order['side'] )
            if (order['type'] == 'limit'):
                if (order['side'] == 'buy'):
                    # start_base and start_quote
                    self.calc_quote_free -= order['amount'] * order['price']
                elif ((order['symbol'] == self.ms) and (order['side'] == 'sell')):
                    # start_base and start_quote
                    self.calc_base_free -= order['amount']
        if self.base_free != None:
            if self.base_free < self.calc_base_free:
                # the base_free return is lower then what we calculated from OpenOrders
                logger.info("base_free (%f) reported from exchange is lower than calc_base_free (%f)" %(self.base_free, self.calc_base_free))
                self.calc_base_free = self.base_free
        if self.quote_free != None:
            if self.quote_free < self.calc_quote_free:
                # the quote_free returned is lower then what we calculated from OpenOrders
                logger.info("quote_free (%f) reported from exchange is lower than calc_quote_free (%f)" %(self.quote_free, self.calc_quote_free))
                self.calc_quote_free = self.quote_free
        
        logger.info ("calculated from open orders: free base %f %s, free quote %f %s" % (self.calc_base_free, self.bs, self.calc_quote_free, self.qs))   

       
class CandleTest:
    high = None
    low = None
    last = None
    def __init__(self, ohlcv_array):
        for candle in ohlcv_array:
            if self.high == None or self.high < candle[2]:
                self.high = candle[2]
            if self.low == None or self.low > candle[3]:
                self.low = candle[3]
            self.last = candle[4]
            
