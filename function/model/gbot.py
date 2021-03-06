## https://github.com/dsmorgan/yacgb

import os
import logging
from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, ListAttribute, MapAttribute
)

from model.gridline import GridLine

logger = logging.getLogger(__name__)

class Gbot(Model):
    class Meta:
        table_name =  os.environ.get("TABLE_GBOT", "Gbot")
        host = os.environ.get('DYNAMODB_HOST')
        region = os.environ.get('AWS_REGION')
    
    gbotid = UnicodeAttribute(hash_key=True)
    exchange = UnicodeAttribute()
    market_symbol = UnicodeAttribute()
    #accountid = UnicodeAttribute(null=True)
    state=UnicodeAttribute(default='active')
    type=UnicodeAttribute(default='unknown')
    config = MapAttribute(default={})
    last_ticker = NumberAttribute()
    at_high_ticker = NumberAttribute()
    at_low_ticker = NumberAttribute()
    balance_quote = NumberAttribute(default=0)
    balance_base = NumberAttribute(default=0)
    need_quote = NumberAttribute(default=0)
    need_base = NumberAttribute(default=0)
    cost_basis = NumberAttribute(default=0)
    ###
    transactions = NumberAttribute(default=0)
    profit = NumberAttribute(default=0)
    step_profit = NumberAttribute(default=0)
    total_fees = NumberAttribute(default=0)
    grid = ListAttribute(of=GridLine) 
    last_order_ts = NumberAttribute(default=0)
    ####not used yet - add
    start_timestamp = NumberAttribute(null=True)
    start = UnicodeAttribute(null=True)
    last_timestamp = NumberAttribute(null=True)
    last = UnicodeAttribute(null=True)
    
    def to_dict(self):
        rval = {}
        for key in self.attribute_values:
            if key == 'config':
                rval[key] = None
            elif key == 'grid':
                rval[key] = None
            else:
                rval[key] = self.__getattribute__(key)
        return rval

def gbot_init():
    if not Gbot.exists():
        Gbot.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
        logger.info('Created Dynamodb table Gbot')