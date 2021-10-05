## https://github.com/dsmorgan/yacgb
import pytest

import os

from yacgb.lookup import Candle

from yacgb.gbotrunner import GbotRunner
from model.orders import Orders


local_dynamo_avail = pytest.mark.skipif(os.environ.get('DYNAMODB_HOST') == None, 
                        reason="No local dynamodb, e.g. export DYNAMODB_HOST=http://localhost:8000")


@pytest.fixture(params=[200])
def setup_gbot4(request):
    config_gbot= {'exchange': 'binanceus', 
            'market_symbol': 'BNB/USD', 
            'grid_spacing': 0.1, 
            'total_quote': 1000, 
            'max_ticker': 250, 
            'min_ticker': 150, 
            'reserve': 0, 
            'live_balance': False, 
            'start_base': 5, 
            'start_quote': 700, 
            'makerfee': 0.001, 
            'takerfee': 0.001, 
            'feecurrency': 'USD', 
            'backtest_start': '20210526 19:00', 
            'backtest_end': '20210528 01:00', 
            'backtest_timeframe': '1h', 
            'max_percent_start': None, 
            'min_percent_start': None, 
            'stop_loss': 100, 
            'stop_loss_precent_min': None, 
            'take_profit': 300, 
            'take_profit_percent_max': None, 
            'init_market_order': False, 
            'profit_protect_percent': 0.25,
            'dynamic_grid': True,
            'start_ticker': request.param}
    g = GbotRunner(config=config_gbot, type='pytest')
    print ("New gbot:", g.gbot.gbotid)
    yield g
    print ("Delete any Orders records:", g.gbot.gbotid)
    for o in Orders.scan(Orders.gbotid == g.gbot.gbotid):
        print(o.ex_orderid)
    print ("Delete gbot:", g.gbot.gbotid)
    g.gbot.delete()

    
@local_dynamo_avail
def test_grid4_dynamic_grid_adjust(setup_gbot4):
    print("Grid...", setup_gbot4.gbot.gbotid)
    for g in setup_gbot4.gbot.grid:
        print ("%2d %0.3f %4s buy %0.3f %0.5f sell %0.3f %0.5f  counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.buy_quote_quantity, g.buy_base_quantity,
                g.sell_quote_quantity, g.sell_base_quantity, g.buy_count, g.sell_count, g.ex_orderid))
                
    assert setup_gbot4.grids() == 6
    assert setup_gbot4.gbot.state == 'active'
    assert setup_gbot4.total_buy_q() == 600
    assert setup_gbot4.total_sell_b() == 1.91244
    assert setup_gbot4.gbot.need_quote == 0
    assert setup_gbot4.gbot.need_base == 0
    assert setup_gbot4.gbot.balance_quote == 100
    assert setup_gbot4.gbot.balance_base == 3.08756
    
    setup_gbot4.dynamic_grid_adjust(245.11)
    setup_gbot4.dynamic_grid_adjust(199.65)
    setup_gbot4.dynamic_grid_adjust(145.25)
    setup_gbot4.dynamic_grid_adjust(199.65)
    
    print("Grid (reset)...", setup_gbot4.gbot.gbotid)
    for g in setup_gbot4.gbot.grid:
        print ("%2d %0.3f %4s buy %0.3f %0.5f sell %0.3f %0.5f  counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.buy_quote_quantity, g.buy_base_quantity,
                g.sell_quote_quantity, g.sell_base_quantity, g.buy_count, g.sell_count, g.ex_orderid))
    
    assert setup_gbot4.total_buy_q() == 600
    assert setup_gbot4.total_sell_b() == 1.91244
    
    
@local_dynamo_avail   
def test_grid4_backtest1(setup_gbot4):
    print("Grid...", setup_gbot4.gbot.gbotid)
    c = Candle(1,'1h',candle_array=[1,180,200,180,200,1])
    setup_gbot4.backtest(c)
    c = Candle(1,'1h',candle_array=[1,220.1,220.1,219.25,219.25,1])
    setup_gbot4.backtest(c)
    setup_gbot4.save()
    
    for g in setup_gbot4.gbot.grid:
        print ("%2d %0.3f %4s buy %0.3f %0.5f sell %0.3f %0.5f  counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.buy_quote_quantity, g.buy_base_quantity,
                g.sell_quote_quantity, g.sell_base_quantity, g.buy_count, g.sell_count, g.ex_orderid))
                
    assert setup_gbot4.gbot.state == 'active'
    assert setup_gbot4.gbot.transactions == 3
    assert setup_gbot4.gbot.at_low_ticker == 180
    assert setup_gbot4.gbot.at_high_ticker == 220.1
    assert setup_gbot4.gbot.last_ticker == 219.25
    #before dynamic_grid
    #assert round(setup_gbot4.gbot.profit, 2) == 32.60
    assert round(setup_gbot4.gbot.profit, 2) == 32.93
    assert round(setup_gbot4.gbot.step_profit, 2) == 39.36
    assert round(setup_gbot4.gbot.total_fees, 2) == 0.64
    
    
@local_dynamo_avail   
def test_grid4_backtest2(setup_gbot4):
    print("Grid...", setup_gbot4.gbot.gbotid)
    c = Candle(1,'1h',candle_array=[1,180,180,180,180,1])
    setup_gbot4.backtest(c)
    #dynamic_grid_adjust is already called as part of backtest
    #setup_gbot4.dynamic_grid_adjust(180)
    c = Candle(1,'1h',candle_array=[1,200,200,200,200,1])
    setup_gbot4.backtest(c)
    #setup_gbot4.dynamic_grid_adjust(200)
    c = Candle(1,'1h',candle_array=[1,220.1,220.1,220.1,220.1,1])
    setup_gbot4.backtest(c)
    #setup_gbot4.dynamic_grid_adjust(220.1)
    c = Candle(1,'1h',candle_array=[1,219.25,219.25,219.25,219.25,1])
    setup_gbot4.backtest(c)
    setup_gbot4.save()
    
    for g in setup_gbot4.gbot.grid:
        print ("%2d %0.3f %4s buy %0.3f %0.5f sell %0.3f %0.5f  counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.buy_quote_quantity, g.buy_base_quantity,
                g.sell_quote_quantity, g.sell_base_quantity, g.buy_count, g.sell_count, g.ex_orderid))
                
    assert setup_gbot4.gbot.state == 'active'
    assert setup_gbot4.gbot.transactions == 3
    assert setup_gbot4.gbot.at_low_ticker == 180
    assert setup_gbot4.gbot.at_high_ticker == 220.1
    assert setup_gbot4.gbot.last_ticker == 219.25
    #assert round(setup_gbot4.gbot.profit, 2) == 39.01
    ##assert round(setup_gbot4.gbot.profit, 2) == 25.78
    ###assert round(setup_gbot4.gbot.profit, 2) == 23.4
    ##<>##assert round(setup_gbot4.gbot.profit, 2) == 31.16
    assert round(setup_gbot4.gbot.profit, 2) == 32.93
    assert round(setup_gbot4.gbot.step_profit, 2) == 39.36
    assert round(setup_gbot4.gbot.total_fees, 2) == 0.64


@pytest.fixture(params=[150])
def setup_gbot5(request):
    config_gbot= {'exchange': 'bogus', 
            'market_symbol': 'ABC/USD', 
            'grid_spacing': 0.07, 
            'total_quote': 1000, 
            'max_ticker': 200, 
            'min_ticker': 100, 
            'reserve': 0, 
            'live_balance': False, 
            'start_base': 4, 
            'start_quote': 600, 
            'makerfee': 0, 
            'takerfee': 0, 
            'feecurrency': 'USD', 
            'backtest_start': '20210526 19:00', 
            'backtest_end': '20210528 01:00', 
            'backtest_timeframe': '1h', 
            'max_percent_start': None, 
            'min_percent_start': None, 
            'stop_loss': 100, 
            'stop_loss_precent_min': None, 
            'take_profit': 300, 
            'take_profit_percent_max': None, 
            'init_market_order': False, 
            'profit_protect_percent': 0.25,
            'dynamic_grid': False,
            'start_ticker': request.param}
    g = GbotRunner(config=config_gbot, type='pytest')
    print ("New gbot:", g.gbot.gbotid)
    yield g
    print ("Delete any Orders records:", g.gbot.gbotid)
    for o in Orders.scan(Orders.gbotid == g.gbot.gbotid):
        print(o.ex_orderid)
    print ("Delete gbot:", g.gbot.gbotid)
    g.gbot.delete()
    
@local_dynamo_avail   
def test_grid5(setup_gbot5):
    print("Grid...", setup_gbot5.gbot.gbotid)
    for g in setup_gbot5.gbot.grid:
        print ("%2d %0.3f %4s buy (b/q) %0.5f/%0.3f sell (b/q) %0.5f/%0.3f counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.buy_base_quantity, g.buy_quote_quantity,
                g.sell_base_quantity, g.sell_quote_quantity, g.buy_count, g.sell_count, g.ex_orderid))
    setup_gbot5.save()       

    assert setup_gbot5._current_none() == 6
    assert round(setup_gbot5.gbot.cost_basis,2) == 362.25
    assert round(setup_gbot5.base_cost(),2) == 150

    #setup_gbot5.backtest(219.25)
    #setup_gbot5.reset_grid(220.1)
    

kraken_sample = [{'amount': 0.71299,
        'average': 140.11,
        'clientOrderId': '0',
        'cost': 100,
        'datetime': '2021-04-12T13:49:34.127Z',
        'fee': {'cost': 0.16, 'currency': 'USD', 'rate': None},
        'filled': 0.71299,
        'id': 'AAAAA-99999-YYYYYY',
        'info': {   'closetm': 1618239581.8319,
                    'cost': '100.00',
                    'descr': {   'close': '',
                                 'leverage': 'none',
                                 'type': 'buy'},
                    'expiretm': 0,
                    'fee': '0.78',
                    'id': 'AAAAA-99999-ZZZZZZ',
                    'limitprice': '0.00000',
                    'misc': '',
                    'oflags': 'fciq',
                    'opentm': 1618235374.1276,
                    'price': '140.11',
                    'reason': None,
                    'refid': None,
                    'starttm': 0,
                    'status': 'closed',
                    'stopprice': '0.00000',
                    'userref': 0,
                    'vol': '0.71299',
                    'vol_exec': '0.71299'},
        'lastTradeTimestamp': None,
        'postOnly': None,
        'price': 140.11,
        'remaining': 0.0,
        'side': 'buy',
        'status': 'canceled',
        'stopPrice': 0.0,
        'symbol': 'ABC/USD',
        'timeInForce': None,
        'timestamp': 1618235374127,
        'trades': None,
        'type': 'limit'}]

binanceus_sample = [{'amount': 0.66634,
    'average': 160.578,
    'clientOrderId': 'ios_7785a40b6a644f3f8477afa1d51db453',
    'cost': 107.00,
    'datetime': '2021-04-20T04:48:54.191Z',
    'fee': None,
    'filled': 0.66634,
    'id': '97289161',
    'info': {   'clientOrderId': 'ios_7785a40b6a644f3f8477afa1d51db453',
                'cummulativeQuoteQty': '107.00',
                'executedQty': '0.66634',
                'icebergQty': '0.00000000',
                'isWorking': True,
                'orderId': 97289161,
                'orderListId': -1,
                'origQty': '0.66634',
                'origQuoteOrderQty': '0.0000',
                'price': '161.25',
                'side': 'SELL',
                'status': 'FILLED',
                'stopPrice': '0.0000',
                'symbol': 'XLMUSD',
                'time': 1618894134191,
                'timeInForce': 'GTC',
                'type': 'LIMIT',
                'updateTime': 1618901627812},
    'lastTradeTimestamp': None,
    'postOnly': False,
    'price': 161.25,
    'remaining': 0.0,
    'side': 'sell',
    'status': 'closed',
    'stopPrice': 0.0,
    'symbol': 'ABC/USD',
    'timeInForce': 'GTC',
    'timestamp': 1618894134191,
    'trades': None,
    'type': 'limit'}]
    
@local_dynamo_avail   
def test_grid5_closed_adjust_ordersmatch_kraken(setup_gbot5):
    
    ##No orders test
    orderid = 'AAAAA-99999-ZZZZZZ'
    setup_gbot5.gbot.grid[5].ex_orderid = 'bogus_'+orderid
    setup_gbot5.save()
    setup_gbot5.closed_adjust(setup_gbot5.ordersmatch([]), '*')
    
    print("Grid (no orders)...", setup_gbot5.gbot.gbotid)
    for g in setup_gbot5.gbot.grid:
        print ("%2d %0.3f %4s %s buy (b/q) %0.5f/%0.3f sell (b/q) %0.5f/%0.3f counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.type, g.buy_base_quantity, g.buy_quote_quantity,
                g.sell_base_quantity, g.sell_quote_quantity, g.buy_count, g.sell_count, g.ex_orderid))
    
    #No match test
    setup_gbot5.save()
    setup_gbot5.closed_adjust(setup_gbot5.ordersmatch(kraken_sample), '*')
    
    print("Grid (no matches)...", setup_gbot5.gbot.gbotid)
    for g in setup_gbot5.gbot.grid:
        print ("%2d %0.3f %4s %s buy (b/q) %0.5f/%0.3f sell (b/q) %0.5f/%0.3f counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.type, g.buy_base_quantity, g.buy_quote_quantity,
                g.sell_base_quantity, g.sell_quote_quantity, g.buy_count, g.sell_count, g.ex_orderid))
    
    assert setup_gbot5._current_none() == 6
    assert setup_gbot5.gbot.transactions == 0  
    
    
    ##Reset Test (status: 'canceled') 
    kraken_sample[0]['id']=orderid
    setup_gbot5.closed_adjust(setup_gbot5.ordersmatch(kraken_sample), '*')
    setup_gbot5.save()
    
    print("Grid (canceled)...", setup_gbot5.gbot.gbotid)
    for g in setup_gbot5.gbot.grid:
        print ("%2d %0.3f %4s %s buy (b/q) %0.5f/%0.3f sell (b/q) %0.5f/%0.3f counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.type, g.buy_base_quantity, g.buy_quote_quantity,
                g.sell_base_quantity, g.sell_quote_quantity, g.buy_count, g.sell_count, g.ex_orderid))
    
    assert setup_gbot5._current_none() == 6
    assert setup_gbot5.gbot.transactions == 0
    assert round(setup_gbot5.base_cost(), 2) == 150
    
    #Closed Test (status: 'closed')
    setup_gbot5.gbot.grid[5].ex_orderid = 'bogus_'+orderid
    kraken_sample[0]['status'] = 'closed'
    setup_gbot5.closed_adjust(setup_gbot5.ordersmatch(kraken_sample), '*')
    setup_gbot5.save()
    
    print("Grid (buy)...", setup_gbot5.gbot.gbotid)
    for g in setup_gbot5.gbot.grid:
        print ("%2d %0.3f %4s %s buy (b/q) %0.5f/%0.3f sell (b/q) %0.5f/%0.3f counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.type, g.buy_base_quantity, g.buy_quote_quantity,
                g.sell_base_quantity, g.sell_quote_quantity, g.buy_count, g.sell_count, g.ex_orderid))
    
    assert setup_gbot5._current_none() == 5
    assert setup_gbot5.gbot.transactions == 1
    assert round(setup_gbot5.base_cost(), 2) == 147.83
    
    
@local_dynamo_avail   
def test_grid5_closed_adjust_ordersmatch_binanceus(setup_gbot5):
    
    setup_gbot5.gbot.grid[7].ex_orderid = 'bogus_97289161'
    setup_gbot5.save()
    setup_gbot5.closed_adjust(setup_gbot5.ordersmatch([]), '*')
    
    print("Grid...", setup_gbot5.gbot.gbotid)
    for g in setup_gbot5.gbot.grid:
        print ("%2d %0.3f %4s %s buy (b/q) %0.5f/%0.3f sell (b/q) %0.5f/%0.3f counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.type, g.buy_base_quantity, g.buy_quote_quantity,
                g.sell_base_quantity, g.sell_quote_quantity, g.buy_count, g.sell_count, g.ex_orderid))
    
    assert round(setup_gbot5.gbot.cost_basis, 2) == 362.25
    assert round(setup_gbot5.base_cost(), 2) == 150
    
    setup_gbot5.closed_adjust(setup_gbot5.ordersmatch(binanceus_sample), '*')
    setup_gbot5.save()
    
    print("Grid (sell)...", setup_gbot5.gbot.gbotid)
    for g in setup_gbot5.gbot.grid:
        print ("%2d %0.3f %4s %s buy (b/q) %0.5f/%0.3f sell (b/q) %0.5f/%0.3f counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.type, g.buy_base_quantity, g.buy_quote_quantity,
                g.sell_base_quantity, g.sell_quote_quantity, g.buy_count, g.sell_count, g.ex_orderid))
    
    assert setup_gbot5._current_none() == 7
    assert setup_gbot5.gbot.transactions == 1
    assert round(setup_gbot5.gbot.cost_basis, 2) == 262.30
    assert round(setup_gbot5.base_cost(), 2) == 150
    
@local_dynamo_avail   
def test_grid5_open_orders(setup_gbot5):
    o = 'bogus_97289161'
    setup_gbot5.totals()
    assert setup_gbot5.open_orders == False
    print ("add order", o)
    setup_gbot5.gbot.grid[7].ex_orderid = o
    setup_gbot5.save()
    setup_gbot5.totals()
    assert setup_gbot5.open_orders == True
    
@local_dynamo_avail   
def test_grid5_dynamic_set_triggers_static(setup_gbot5):
    setup_gbot5.dynamic_set_triggers()
    for g in setup_gbot5.gbot.grid:
        assert g.type == 'limit'

@pytest.fixture(params=[150])    
def setup_gbot6(request):
    config_gbot= {'exchange': 'bogus', 
            'market_symbol': 'ABC/USD', 
            'grid_spacing': 0.07, 
            'total_quote': 1000, 
            'max_ticker': 200, 
            'min_ticker': 100, 
            'reserve': 0, 
            'live_balance': False, 
            'start_base': 4, 
            'start_quote': 600, 
            'makerfee': 0, 
            'takerfee': 0, 
            'feecurrency': 'USD', 
            'backtest_start': '20210526 19:00', 
            'backtest_end': '20210528 01:00', 
            'backtest_timeframe': '1h', 
            'max_percent_start': None, 
            'min_percent_start': None, 
            'stop_loss': 100, 
            'stop_loss_precent_min': None, 
            'take_profit': 300, 
            'take_profit_percent_max': None, 
            'init_market_order': False, 
            'profit_protect_percent': 0.25,
            'dynamic_grid': True,
            'start_ticker': request.param}
    g = GbotRunner(config=config_gbot, type='pytest')
    print ("New gbot:", g.gbot.gbotid)
    yield g
    print ("Delete any Orders records:", g.gbot.gbotid)
    for o in Orders.scan(Orders.gbotid == g.gbot.gbotid):
        print(o.ex_orderid)
    print ("Delete gbot:", g.gbot.gbotid)
    g.gbot.delete()   
    
@local_dynamo_avail   
def test_grid6_dynamic_set_triggers_dynamic(setup_gbot6):
    setup_gbot6.dynamic_set_triggers()
    trigger = 0
    limit = 0
    n = 0
    for g in setup_gbot6.gbot.grid:
        if g.type == 'trigger':
            trigger+=1
        elif g.type == 'limit':
            limit+=1
        else:
            n+=1
    assert trigger == 2
    assert limit == 0
    assert n == 9
    
@local_dynamo_avail   
def test_grid6_dynamic_check_triggers_dynamic(setup_gbot6):
    class Ind:
        def __init__(self, b=False, s=False):
            self.buy_indicator=b
            self.sell_indicator=s
    
    setup_gbot6.dynamic_set_triggers()

    print("Grid...", setup_gbot6.gbot.gbotid)
    for g in setup_gbot6.gbot.grid:
        print ("%2d %0.3f %4s %s buy (b/q) %0.5f/%0.3f sell (b/q) %0.5f/%0.3f counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.type, g.buy_base_quantity, g.buy_quote_quantity,
                g.sell_base_quantity, g.sell_quote_quantity, g.buy_count, g.sell_count, g.ex_orderid))    
    
    # buy should happen
    setup_gbot6.dynamic_set_triggers()
    i = Ind(True, True)
    setup_gbot6.dynamic_check_triggers(tick=110, indicator=i)
    
    trigger = 0
    limit = 0
    n = 0
    for g in setup_gbot6.gbot.grid:
        if g.type == 'trigger':
            trigger+=1
        elif g.type == 'limit':
            limit+=1
        else:
            n+=1
    assert trigger == 1
    assert limit == 1
    assert n == 9
    assert setup_gbot6.gbot.grid[5].type == 'limit'
    
    # buy should NOT happen (delay)
    setup_gbot6.dynamic_set_triggers()
    i = Ind(False, False)
    setup_gbot6.dynamic_check_triggers(tick=110, indicator=i)
    
    trigger = 0
    limit = 0
    n = 0
    for g in setup_gbot6.gbot.grid:
        if g.type == 'trigger':
            trigger+=1
        elif g.type == 'limit':
            limit+=1
        else:
            n+=1
    assert trigger == 2
    assert limit == 0
    assert n == 9
    
    
    # sell should happen
    setup_gbot6.dynamic_set_triggers()
    i = Ind(True, True)
    setup_gbot6.dynamic_check_triggers(tick=201, indicator=i)
    
    trigger = 0
    limit = 0
    n = 0
    for g in setup_gbot6.gbot.grid:
        if g.type == 'trigger':
            trigger+=1
        elif g.type == 'limit':
            limit+=1
        else:
            n+=1
    assert trigger == 1
    assert limit == 1
    assert n == 9
    assert setup_gbot6.gbot.grid[7].type == 'limit'
    
    #sell should NOT happen (delay)
    setup_gbot6.dynamic_set_triggers()
    i = Ind(False, False)
    setup_gbot6.dynamic_check_triggers(tick=201, indicator=i)
    
    trigger = 0
    limit = 0
    n = 0
    for g in setup_gbot6.gbot.grid:
        if g.type == 'trigger':
            trigger+=1
        elif g.type == 'limit':
            limit+=1
        else:
            n+=1
    assert trigger == 2
    assert limit == 0
    assert n == 9