## https://github.com/dsmorgan

import os
import logging
from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute
)

logger = logging.getLogger(__name__)

class Market(Model):
    class Meta:
        table_name = os.environ.get("TABLE_MARKET", "Market")
        host = os.environ.get('DYNAMODB_HOST')
        region = os.environ.get('AWS_REGION')

    exchange = UnicodeAttribute(hash_key=True)
    market = UnicodeAttribute(range_key=True)
    precision_base = NumberAttribute(default=8)
    precision_quote = NumberAttribute(default=2)
    start_timestamp = NumberAttribute(null=True)
    last_timestamp = NumberAttribute(null=True)
    start = UnicodeAttribute(null=True) 
    #when we created this table, not the earliest record in OHLCV, which has at least 2 weeks of 1h before this
    last = UnicodeAttribute(null=True)
    maker = NumberAttribute(default=0)
    taker = NumberAttribute(default=0)
    limits_amount_max = NumberAttribute(null=True)
    limits_amount_min = NumberAttribute(null=True)
    limits_cost_max = NumberAttribute(null=True)
    limits_cost_min = NumberAttribute(null=True)
    limits_price_max = NumberAttribute(null=True)
    limits_price_min = NumberAttribute(null=True)
    
    def to_dict(self):
        rval = {}
        for key in self.attribute_values:
            rval[key] = self.__getattribute__(key)
        return rval
    

def market_init():
    if not Market.exists():
        Market.create_table(read_capacity_units=2, write_capacity_units=2, wait=True)
        logger.info('Created Dynamodb table Market')