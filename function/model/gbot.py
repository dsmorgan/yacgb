## https://github.com/dsmorgan/yacgb

import os
from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, JSONAttribute
)

class Gbot(Model):
    class Meta:
        table_name = 'Gbot'
        host = os.environ.get('DYNAMODB_HOST')
    
    gbotid = UnicodeAttribute(hash_key=True)
    exchange = UnicodeAttribute()
    market_symbol = UnicodeAttribute()
    accountid = UnicodeAttribute(null=True)
    # grid inputs
    grid_spacing = NumberAttribute()
    total_quote = NumberAttribute()
    start_quote = NumberAttribute()
    start_base =  NumberAttribute()
    reserve = NumberAttribute()
    # discovered inputs
    start_ticker = NumberAttribute()
    last_ticker = NumberAttribute()
    max_ticker = NumberAttribute()
    min_ticker = NumberAttribute()
    makerfee = NumberAttribute()
    takerfee = NumberAttribute()
    feecurrency = UnicodeAttribute()
    # outputs and calculations
    total_base = NumberAttribute(default=0)
    quote_balance = NumberAttribute(default=0)
    base_balance = NumberAttribute(default=0)
    transactions = NumberAttribute(default=0)
    profit = NumberAttribute(default=0)
    step_profit = NumberAttribute(default=0)
    total_fees = NumberAttribute(default=0)
    grid = JSONAttribute() 
    grids = NumberAttribute(default=0)
    original_grid = JSONAttribute()
    #should this be null?
    last_order_ts = NumberAttribute(default=0)
    #not used yet
    start_timestamp = NumberAttribute(null=True)
    start = UnicodeAttribute(null=True)
    last_timestamp = NumberAttribute(null=True)
    last = UnicodeAttribute(null=True)
    ##
    #state=UnicodeAttribute(default='active')
    #stop_loss = NumberAttribute(null=True)
    #take_profit = NumberAttribute(null=True)