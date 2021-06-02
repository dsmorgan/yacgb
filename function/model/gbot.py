## https://github.com/dsmorgan/yacgb

import os
from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, ListAttribute, MapAttribute
)

from model.gridline import GridLine

class Gbot(Model):
    class Meta:
        table_name = 'Gbot'
        host = os.environ.get('DYNAMODB_HOST')
    
    gbotid = UnicodeAttribute(hash_key=True)
    exchange = UnicodeAttribute()
    market_symbol = UnicodeAttribute()
    #accountid = UnicodeAttribute(null=True)
    last_ticker = NumberAttribute()
    total_base = NumberAttribute(default=0)
    quote_balance = NumberAttribute(default=0)
    base_balance = NumberAttribute(default=0)
    transactions = NumberAttribute(default=0)
    profit = NumberAttribute(default=0)
    step_profit = NumberAttribute(default=0)
    total_fees = NumberAttribute(default=0)
    grid = ListAttribute(of=GridLine) 
    grids = NumberAttribute(default=0)
    # DELETE THIS
    #original_grid = JSONAttribute()
    #should this be null?
    last_order_ts = NumberAttribute(default=0)
    #not used yet
    start_timestamp = NumberAttribute(null=True)
    start = UnicodeAttribute(null=True)
    last_timestamp = NumberAttribute(null=True)
    last = UnicodeAttribute(null=True)
    ## NEW
    state=UnicodeAttribute(default='active')
    type=UnicodeAttribute(default='unknown')
    config = MapAttribute(default={})
    # Candidates - do we need?
    #stop_loss = NumberAttribute(null=True)
    #take_profit = NumberAttribute(null=True)
    