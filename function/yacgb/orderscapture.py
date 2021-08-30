## https://github.com/dsmorgan/yacgb

import logging
import uuid
import datetime
from datetime import timezone

from model.orders import Orders, orders_init

logger = logging.getLogger(__name__)

class OrderParse:
    def __init__(self, step, gbotid, exchange, makerfee, takerfee, accountid, order):
        fee = takerfee
        self.step = step
        self.oid = order.get(id, uuid.uuid4().hex)
        self.ex_orderid = exchange+'_'+self.oid
        self.exchange = exchange
        self.accountid = accountid
        self.gbotid = gbotid
        self.price = order.get('price', 0)
        self.amount = order.get('amount', 0)
        self.average = order.get('average',self.price)
        self.cost = order.get('cost', self.price*self.amount)
        self.side = order.get('side', '')
        self.type = order.get('type', '')
        self.status = order.get('status', 'canceled')
        self.market_symbol = order.get('symbol')
        self.symbol = order.get('symbol')
        self.timestamp = order.get('timestamp', 0)
        self.timestamp_st=datetime.datetime.fromtimestamp(self.timestamp/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        if order.get('fee', None) != None:
            self.fee_cost = order['fee'].get('cost', 0)
            self.fee_currency = order['fee'].get('currency', 'USD')
        else:
            if self.type == 'limit':
                fee = makerfee
            self.fee_cost = round(self.cost * fee, 2)
            self.fee_currency = 'USD'
        self.raw = order
 
class OrdersCapture:
    def __init__(self, gbotid, exchange, makerfee, takerfee, accountid=None, save=True):
        self.gbotid=gbotid
        self.accountid=accountid
        self.exchange=exchange
        self.makerfee=makerfee
        self.takerfee=takerfee
        self.save=save
        self.closed_list=[]
        self.reset_list=[]
        orders_init()
            
    def delete_all(self):
        if self.save:
            for dorder in self.closed_list:
                try:
                    dd = Orders.get(dorder.ex_orderid)
                    dd.delete()
                except Orders.DoesNotExist:
                    print ("Error, %s does not exist" % dorder.ex_orderid)
    
    def add(self, matched_step, corder):
        o = OrderParse(step=matched_step, gbotid=self.gbotid, exchange=self.exchange, makerfee=self.makerfee, takerfee=self.takerfee, 
                accountid=self.accountid, order=corder)
        
        if o.status == 'canceled':
            #add it to the list to reset the order
            self.reset_list.append(o)
            logger.warning("Canceled order (%d), resetting: %s %s" % (o.step, o.market_symbol, o.ex_orderid))
            #setting this grid to None will trigger it to be reset
            ##TODO x.gbot.grid[matched_step].ex_orderid = None
            #don't do anything else with this step, next order
        else:
            #add it to list to recalculate the grid, and replace the buy/sell w/ the approproate sell/buy
            self.closed_list.append(o)
            ###This should be seperated to a class, the class should handle both writing to the table, and replace the
            ### matched_step so that additional values that we require are passed to gbot (step, price, base_amt, quote_amt, fee)
                
            #TODO the timestamp is when the order was placed, NOT when the order completed. Need to map that to the correct field
            # Problem is, this isn't consistent between exchanges
            if self.save:
                ord = Orders(o.ex_orderid, 
                            exchange=o.exchange, accountid=o.accountid, gbotid=o.gbotid, market_symbol=o.market_symbol, 
                            timestamp=o.timestamp, timestamp_st=o.timestamp_st, side=o.side, type=o.type, status=o.status, 
                            cost=o.cost, price=o.price, amount=o.amount, average=o.average, fee_cost=o.fee_cost, fee_currency=o.fee_currency, 
                            raw=o.raw
                        )
                #x.gbot.last_order_ts=corder['timestamp'] <--this isn't correct, need to find a better solution
                #TODO: There doesn't seem to be a safe way to filter the corder list based on 'since'.
                ord.save()