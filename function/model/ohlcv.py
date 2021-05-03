## https://github.com/dsmorgan

import os
from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, ListAttribute
)

    
class OHLCV(Model):
    class Meta:
        table_name = 'OHLCV'
        host = os.environ.get('DYNAMODB_HOST')

    ex_market_tf = UnicodeAttribute(hash_key=True)
    timestamp = NumberAttribute(range_key=True)
    timestamp_st = UnicodeAttribute()
    last = UnicodeAttribute()
    array = ListAttribute()