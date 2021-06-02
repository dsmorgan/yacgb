## https://github.com/dsmorgan/yacgb

from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, MapAttribute
)

class GridLine(MapAttribute):
    step = NumberAttribute()
    ticker = NumberAttribute()
    quote_step = NumberAttribute(default=0)
    mode = UnicodeAttribute(null=True)
    buy_base_quantity = NumberAttribute(default=0)
    take = NumberAttribute(default=0)
    step_take = NumberAttribute(default=0)
    sell_quote_quantity = NumberAttribute(default=0)
    sell_base_quantity = NumberAttribute(default=0)
    buy_count = NumberAttribute(default=0)
    sell_count = NumberAttribute(default=0)
    ex_orderid = UnicodeAttribute(null=True)