## https://github.com/dsmorgan

import os
import logging
from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, ListAttribute
)

logger = logging.getLogger(__name__)
    
class OHLCV(Model):
    class Meta:
        table_name = 'OHLCV'
        host = os.environ.get('DYNAMODB_HOST')

    ex_market_tf = UnicodeAttribute(hash_key=True)
    timestamp = NumberAttribute(range_key=True)
    timestamp_st = UnicodeAttribute()
    last = UnicodeAttribute()
    array = ListAttribute()
    
def ohlcv_init():
    if not OHLCV.exists():
        OHLCV.create_table(read_capacity_units=10, write_capacity_units=10, wait=True)   
        logger.info('Created Dynamodb table OHLCV')
    