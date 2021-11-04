## https://github.com/dsmorgan/yacgb

import logging

from model.orders import Orders

logger = logging.getLogger(__name__)

class OrdersGet:
    def __init__(self, gbotid):
        self.orders = []
        logger.info("OrdersGet lookup: %s" % gbotid)
        
        for o in Orders.scan(Orders.gbotid == gbotid):
            self.orders.append(o)
        
        logger.info("OrdersGet lookup returned %d orders" % len(self.orders))
    
    @property    
    def orders_dict(self):
        r = {}
    
        r['buy_timestamp'] = []
        r['buy_timestamp_st'] = []
        r['buy_average'] = []
        r['buy_price'] = []
        r['buy_amount'] = []
        r['sell_timestamp'] = []
        r['sell_timestamp_st'] = []
        r['sell_average'] = []
        r['sell_price'] = []
        r['sell_amount'] = []
        
        for o in self.orders:
            if o.side == 'buy':
                r['buy_timestamp'].append(o.timestamp)
                r['buy_timestamp_st'].append(o.timestamp_st)
                r['buy_average'].append(o.average)
                r['buy_price'].append(o.price)
                r['buy_amount'].append(o.amount)
            else:
                r['sell_timestamp'].append(o.timestamp)
                r['sell_timestamp_st'].append(o.timestamp_st)
                r['sell_average'].append(o.average)
                r['sell_price'].append(o.price)
                r['sell_amount'].append(o.amount)
                
        return(r)
        