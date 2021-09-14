## https://github.com/dsmorgan/yacgb
import pytest

import os

from yacgb.gbotrunner import GbotRunner
from model.orders import Orders


local_dynamo_avail = pytest.mark.skipif(os.environ.get('DYNAMODB_HOST') == None, 
                        reason="No local dynamodb, e.g. export DYNAMODB_HOST=http://localhost:8000")


@pytest.fixture(params=[0.01, 10, 90, 150, 175, 200, 300, 1000, 10000, 1000000])
def setup_gbot1(request):
    config_gbot= {'exchange': 'kraken', 
            'market_symbol': 'LTC/USD', 
            'grid_spacing': 0.05, 
            'total_quote': 200000, 
            'max_ticker': 200, 
            'min_ticker': 100, 
            'reserve': 0, 
            'live_balance': True, 
            'start_base': 1000, 
            'start_quote': 300000, 
            'makerfee': 0.001, 
            'takerfee': 0.002, 
            'feecurrency': 'USD', 
            'backtest_start': '20210507 19:00', 
            'backtest_end': '20210510 01:00', 
            'backtest_timeframe': '1h', 
            'max_percent_start': None, 
            'min_percent_start': None, 
            'stop_loss': None, 
            'stop_loss_precent_min': None, 
            'take_profit': None, 
            'take_profit_percent_max': None, 
            'init_market_order': False, 
            'profit_protect_percent': None,
            'start_ticker': request.param}
    g = GbotRunner(config=config_gbot, type='pytest')
    print ("New gbot:", g.gbot.gbotid)
    yield g
    print ("Delete any Orders records:", g.gbot.gbotid)
    for o in Orders.scan(Orders.gbotid == g.gbot.gbotid):
        print(o.ex_orderid)
        o.delete()
    
    print ("Delete gbot:", g.gbot.gbotid)
    g.gbot.delete()

@pytest.fixture(params=[0.4427,0.3500,0.5500])
def setup_gbot2(request):
    config_gbot= {'exchange': 'binanceus', 
            'market_symbol': 'XLM/USD', 
            'grid_spacing': 0.01, 
            'total_quote': 3000, 
            'max_ticker': 0.45, 
            'min_ticker': 0.4, 
            'reserve': 0, 
            'live_balance': False, 
            'start_base': 9000, 
            'start_quote': 3001, 
            'makerfee': 0.001, 
            'takerfee': 0.001, 
            'feecurrency': 'USD', 
            'backtest_start': '20210526 19:00', 
            'backtest_end': '20210528 01:00', 
            'backtest_timeframe': '1h', 
            'max_percent_start': None, 
            'min_percent_start': None, 
            'stop_loss': 0.35, 
            'stop_loss_precent_min': None, 
            'take_profit': 0.55, 
            'take_profit_percent_max': None, 
            'init_market_order': False, 
            'profit_protect_percent': None,
            'start_ticker': request.param}
    g = GbotRunner(config=config_gbot, type='pytest')
    print ("New gbot:", g.gbot.gbotid)
    yield g
    print ("Delete any Orders records:", g.gbot.gbotid)
    for o in Orders.scan(Orders.gbotid == g.gbot.gbotid):
        print(o.ex_orderid)
    print ("Delete gbot:", g.gbot.gbotid)
    g.gbot.delete()


@pytest.fixture(params=[200])
def setup_gbot3(request):
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
def test_grid1(setup_gbot1):
    
    total_quantity_buy=0
    total_sell=0
    total_quantity_sell=0
    print("Grid...", setup_gbot1.gbot.gbotid)
    for g in setup_gbot1.gbot.grid:
        print ("%2d %0.3f %4s buy %0.3f %0.5f sell %0.3f %0.5f  counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.buy_quote_quantity, g.buy_base_quantity,
                g.sell_quote_quantity, g.sell_base_quantity, g.buy_count, g.sell_count, g.ex_orderid))
                
        if g.mode == 'buy':
            total_quantity_buy += g.ticker * g.buy_base_quantity
            
        if g.mode == 'sell':
            total_sell += g.sell_base_quantity
            total_quantity_sell += g.sell_quote_quantity
       
    print ('total_quantity_buy', total_quantity_buy, 'total_quantity_sell', total_quantity_sell, 'config-total_quote', setup_gbot1.gbot.config.total_quote)
    print ('config-start_base', setup_gbot1.gbot.config.start_base, 'config-start_quote', setup_gbot1.gbot.config.start_quote)
    print ('balance_base', setup_gbot1.gbot.balance_base, 'need_base', setup_gbot1.gbot.need_base, 'balance_quote', setup_gbot1.gbot.balance_quote, 'need_quote', setup_gbot1.gbot.need_quote)
    print(setup_gbot1.gbot.gbotid)
    
    assert len(setup_gbot1.gbot.grid) == setup_gbot1.grids()
    assert round(total_quantity_buy + (total_quantity_sell*(1/(1+setup_gbot1.gbot.config.grid_spacing))), 2) == setup_gbot1.gbot.config.total_quote
    assert round(setup_gbot1.total_buy_q() + (setup_gbot1.total_sell_q()*(1/(1+setup_gbot1.gbot.config.grid_spacing))),2) == setup_gbot1.gbot.config.total_quote
    #if (setup_gbot1.gbot.state != 'error'):
    assert (setup_gbot1.gbot.state != 'error')
    assert round(total_sell, 2) <= round(setup_gbot1.gbot.config.start_base + setup_gbot1.gbot.need_base, 2)
    assert round(total_quantity_buy, 2) <= round(setup_gbot1.gbot.config.start_quote + setup_gbot1.gbot.need_quote, 2)

    
@local_dynamo_avail
def test_grid2(setup_gbot2):
    print("Grid...", setup_gbot2.gbot.gbotid)
    
    print ('config-total_quote', setup_gbot2.gbot.config.total_quote, 'last_ticker', setup_gbot2.gbot.last_ticker)
    print ('config-start_base', setup_gbot2.gbot.config.start_base, 'config-start_quote', setup_gbot2.gbot.config.start_quote)
    print ('balance_base', setup_gbot2.gbot.balance_base, 'need_base', setup_gbot2.gbot.need_base, 'balance_quote', setup_gbot2.gbot.balance_quote, 'need_quote', setup_gbot2.gbot.need_quote)
    print(setup_gbot2.gbot.gbotid)
    
    assert round(setup_gbot2.total_buy_q() + (setup_gbot2.total_sell_q()*(1/(1+setup_gbot2.gbot.config.grid_spacing))),1) == setup_gbot2.gbot.config.total_quote
    assert setup_gbot2.gbot.state == 'active'
    
    
@local_dynamo_avail
def test_grid3_basic(setup_gbot3):
    print("Grid...", setup_gbot3.gbot.gbotid)
    for g in setup_gbot3.gbot.grid:
        print ("%2d %0.3f %4s buy %0.3f %0.5f sell %0.3f %0.5f  counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.buy_quote_quantity, g.buy_base_quantity,
                g.sell_quote_quantity, g.sell_base_quantity, g.buy_count, g.sell_count, g.ex_orderid))

    assert setup_gbot3.grids() == 6
    assert setup_gbot3.gbot.state == 'active'
    assert setup_gbot3.total_buy_q() == 600
    assert setup_gbot3.total_sell_b() == 1.91244
    assert setup_gbot3.gbot.need_quote == 0
    assert setup_gbot3.gbot.need_base == 0
    assert setup_gbot3.gbot.balance_quote == 100
    assert setup_gbot3.gbot.balance_base == 3.08756


@local_dynamo_avail   
def test_grid3_backtest(setup_gbot3):
    print("Grid...", setup_gbot3.gbot.gbotid)
    setup_gbot3.backtest(180)
    setup_gbot3.backtest(200)
    setup_gbot3.backtest(220)
    setup_gbot3.backtest(219.25)
    setup_gbot3.save()
    
    for g in setup_gbot3.gbot.grid:
        print ("%2d %0.3f %4s buy %0.3f %0.5f sell %0.3f %0.5f  counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.buy_quote_quantity, g.buy_base_quantity,
                g.sell_quote_quantity, g.sell_base_quantity, g.buy_count, g.sell_count, g.ex_orderid))

    assert setup_gbot3.gbot.state == 'active'
    assert setup_gbot3.gbot.transactions == 3
    assert setup_gbot3.gbot.at_low_ticker == 180
    assert setup_gbot3.gbot.at_high_ticker == 220
    assert setup_gbot3.gbot.last_ticker == 219.25
    #assert round(setup_gbot3.gbot.profit, 2) == 39.01
    ##assert round(setup_gbot3.gbot.profit, 2) == 25.78
    assert round(setup_gbot3.gbot.profit, 2) == 32.60
    assert round(setup_gbot3.gbot.step_profit, 2) == 39.36
    assert round(setup_gbot3.gbot.total_fees, 2) == 0.64
    

@local_dynamo_avail   
def test_grid3_backtest_profit_protect(setup_gbot3):
    print("Grid...", setup_gbot3.gbot.gbotid)
    setup_gbot3.backtest(180)
    setup_gbot3.backtest(200)
    setup_gbot3.backtest(220)
    setup_gbot3.backtest(201)
    setup_gbot3.backtest(182)
    setup_gbot3.backtest(164)
    setup_gbot3.backtest(180)
    setup_gbot3.save()
    
    for g in setup_gbot3.gbot.grid:
        print ("%2d %0.3f %4s buy %0.3f %0.5f sell %0.3f %0.5f  counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.buy_quote_quantity, g.buy_base_quantity,
                g.sell_quote_quantity, g.sell_base_quantity, g.buy_count, g.sell_count, g.ex_orderid))
                
    assert setup_gbot3.gbot.state == 'profit_protect'
    assert setup_gbot3.gbot.transactions == 4


@local_dynamo_avail   
def test_grid3_backtest_take_profit(setup_gbot3):
    print("Grid...", setup_gbot3.gbot.gbotid)
    setup_gbot3.backtest(180)
    setup_gbot3.backtest(200)
    setup_gbot3.backtest(220)
    setup_gbot3.backtest(240)
    setup_gbot3.backtest(266)
    setup_gbot3.backtest(301)
    setup_gbot3.backtest(240)
    setup_gbot3.backtest(219)
    setup_gbot3.backtest(180)
    setup_gbot3.save()
    
    for g in setup_gbot3.gbot.grid:
        print ("%2d %0.3f %4s buy %0.3f %0.5f sell %0.3f %0.5f  counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.buy_quote_quantity, g.buy_base_quantity,
                g.sell_quote_quantity, g.sell_base_quantity, g.buy_count, g.sell_count, g.ex_orderid))

    assert setup_gbot3.gbot.state == 'take_profit'
    assert setup_gbot3.gbot.transactions == 4
  
@local_dynamo_avail   
def test_grid3_backtest_stop_loss(setup_gbot3):
    print("Grid...", setup_gbot3.gbot.gbotid)
    #work around for now to disable this
    setup_gbot3.gbot.config.profit_protect_percent=None
    setup_gbot3.backtest(180)
    setup_gbot3.backtest(160)
    setup_gbot3.backtest(145)
    setup_gbot3.backtest(99.87)
    setup_gbot3.backtest(152)
    setup_gbot3.backtest(200)
    setup_gbot3.save()
    
    for g in setup_gbot3.gbot.grid:
        print ("%2d %0.3f %4s buy %0.3f %0.5f sell %0.3f %0.5f  counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.buy_quote_quantity, g.buy_base_quantity,
                g.sell_quote_quantity, g.sell_base_quantity, g.buy_count, g.sell_count, g.ex_orderid))

    assert setup_gbot3.gbot.state == 'stop_loss'
    assert setup_gbot3.gbot.transactions == 3
    
    
@local_dynamo_avail   
def test_grid3_closed_adjust(setup_gbot3):
    print("Grid...", setup_gbot3.gbot.gbotid)
    for g in setup_gbot3.gbot.grid:
        print ("%2d %0.3f %4s buy %0.3f %0.5f sell %0.3f %0.5f  counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.buy_quote_quantity, g.buy_base_quantity,
                g.sell_quote_quantity, g.sell_base_quantity, g.buy_count, g.sell_count, g.ex_orderid))

    setup_gbot3.closed_adjust({})
    setup_gbot3.closed_adjust(setup_gbot3.stepsmatch({2:[100,1618239581831], 4:[200,1618239581831]}))
    setup_gbot3.save()
    assert setup_gbot3.gbot.state == 'active'
    assert setup_gbot3.gbot.transactions == 2
    assert setup_gbot3._current_none() == 3    
    
    print("Grid...", setup_gbot3.gbot.gbotid)
    for g in setup_gbot3.gbot.grid:
        print ("%2d %0.3f %4s buy %0.3f %0.5f sell %0.3f %0.5f  counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.buy_quote_quantity, g.buy_base_quantity,
                g.sell_quote_quantity, g.sell_base_quantity, g.buy_count, g.sell_count, g.ex_orderid))
   
    
    setup_gbot3.closed_adjust(setup_gbot3.stepsmatch({1:[100,1618239581831], 2:[200,1618239581831]}))
    assert setup_gbot3.gbot.state == 'active'
    assert setup_gbot3.gbot.transactions == 4
    assert setup_gbot3._current_none() == 1
    
    
    setup_gbot3.closed_adjust(setup_gbot3.stepsmatch({3:[400,1618239581831], 2:[300,1618239581831], 4:[500,1618239581831], 0:[100,1618239581831]}))           
    assert setup_gbot3.gbot.state == 'active'
    assert setup_gbot3.gbot.transactions == 8
    assert setup_gbot3._current_none() == 3
    
    print("Grid...", setup_gbot3.gbot.gbotid)
    for g in setup_gbot3.gbot.grid:
         print ("%2d %0.3f %4s buy %0.3f %0.5f sell %0.3f %0.5f  counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.buy_quote_quantity, g.buy_base_quantity,
                g.sell_quote_quantity, g.sell_base_quantity, g.buy_count, g.sell_count, g.ex_orderid))
    
    setup_gbot3.closed_adjust(setup_gbot3.stepsmatch({2:[300,1618239581831]})) 
    setup_gbot3.closed_adjust(setup_gbot3.stepsmatch({1:[200,1618239600001]})) 
    setup_gbot3.closed_adjust(setup_gbot3.stepsmatch({2:[300,1618239710003]})) 

    assert setup_gbot3.gbot.state == 'active'
    assert setup_gbot3.gbot.transactions == 11
    assert setup_gbot3._current_none() == 2
    
    print("Grid...", setup_gbot3.gbot.gbotid)
    for g in setup_gbot3.gbot.grid:
        print ("%2d %0.3f %4s buy %0.3f %0.5f sell %0.3f %0.5f  counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.buy_quote_quantity, g.buy_base_quantity,
                g.sell_quote_quantity, g.sell_base_quantity, g.buy_count, g.sell_count, g.ex_orderid))
            
    setup_gbot3.closed_adjust(setup_gbot3.stepsmatch({5:[600,1618239600001], 3:[400,1618239600001], 1:[200,1618239600001], 4:[500,1618239600001]})) 

    assert setup_gbot3.gbot.state == 'active'
    assert setup_gbot3.gbot.transactions == 15
    assert setup_gbot3._current_none() == 4