## https://github.com/dsmorgan

import os
import logging
from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, JSONAttribute
)

logger = logging.getLogger(__name__)

class Orders(Model):
    class Meta:
        table_name = 'Orders'
        host = os.environ.get('DYNAMODB_HOST')
        region = os.environ.get('AWS_REGION')
    
    ex_orderid = UnicodeAttribute(hash_key=True)
    #exchange + '_' + ordereid
    exchange = UnicodeAttribute()
    accountid = UnicodeAttribute(null=True)
    gbotid = UnicodeAttribute()
    market_symbol = UnicodeAttribute()
    timestamp = NumberAttribute()
    timestamp_st = UnicodeAttribute()
    side = UnicodeAttribute()
    type = UnicodeAttribute()
    status = UnicodeAttribute()
    cost = NumberAttribute()
    price = NumberAttribute()
    amount = NumberAttribute()
    average = NumberAttribute()
    fee_cost = NumberAttribute()
    fee_currency = UnicodeAttribute()
    raw = JSONAttribute(null=True)
    #[{'id': 'OS63K7-6I4HL-4HIFIS', 'clientOrderId': '0', 'info': {'id': 'OS63K7-6I4HL-4HIFIS', 'refid': None, 'userref': 0, 'status': 'closed', 
    #'reason': None, 'opentm': 1618235374.1276, 'closetm': 1618239581.8319, 'starttm': 0, 'expiretm': 0, 'descr': {'pair': 'LTCUSD', 'type': 'buy', 
    #'ordertype': 'limit', 'price': '246.11', 'price2': '0', 'leverage': 'none', 'order': 'buy 2.00000000 LTCUSD @ limit 246.11', 'close': ''}, 
    #'vol': '2.00000000', 'vol_exec': '2.00000000', 'cost': '492.22', 'fee': '0.78', 'price': '246.11', 'stopprice': '0.00000', 'limitprice': 
    #'0.00000', 'misc': '', 'oflags': 'fciq'}, 'timestamp': 1618235374127, 'datetime': '2021-04-12T13:49:34.127Z', 'lastTradeTimestamp': None, 
    #'status': 'closed', 'symbol': 'LTC/USD', 'type': 'limit', 'timeInForce': None, 'postOnly': None, 'side': 'buy', 'price': 246.11, 'stopPrice': 0.0, 
    #'cost': 492.22, 'amount': 2.0, 'filled': 2.0, 'average': 246.11, 'remaining': 0.0, 'fee': {'cost': 0.78, 'rate': None, 'currency': 'USD'}, 
    #'trades': None}]

def orders_init():
    if not Orders.exists():
        Orders.create_table(read_capacity_units=3, write_capacity_units=3, wait=True)
        logger.info('Created Dynamodb table Orders')