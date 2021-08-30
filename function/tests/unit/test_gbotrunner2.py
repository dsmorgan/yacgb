## https://github.com/dsmorgan/yacgb
import pytest

import os

from yacgb.gbotrunner import GbotRunner


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
            'start_ticker': request.param}
    g = GbotRunner(config=config_gbot, type='pytest')
    print ("New gbot:", g.gbot.gbotid)
    yield g
    print ("Delete gbot:", g.gbot.gbotid)
    g.gbot.delete()

    
@local_dynamo_avail
def test_grid4(setup_gbot4):
    print("Grid...", setup_gbot4.gbot.gbotid)
    for g in setup_gbot4.gbot.grid:
        print ("%2d %0.3f %4s buy %0.3f %0.5f sell %0.3f %0.5f  counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.buy_quote_quantity, g.buy_base_quantity,
                g.sell_quote_quantity, g.sell_base_quantity, g.buy_count, g.sell_count, g.ex_orderid))
                
    assert setup_gbot4.grids() == 6
    assert setup_gbot4.gbot.state == 'active'
    assert setup_gbot4.total_buy_q() == 600
    assert setup_gbot4.total_sell_b() == 1.9124
    assert setup_gbot4.gbot.need_quote == 0
    assert setup_gbot4.gbot.need_base == 0
    assert setup_gbot4.gbot.balance_quote == 100
    assert setup_gbot4.gbot.balance_base == 3.0876
    
    setup_gbot4.dynamic_grid_adjust(245.11)
    setup_gbot4.dynamic_grid_adjust(199.65)
    setup_gbot4.dynamic_grid_adjust(145.25)
    setup_gbot4.dynamic_grid_adjust(199.65)
    
    print("Grid (reset)...", setup_gbot4.gbot.gbotid)
    for g in setup_gbot4.gbot.grid:
        print ("%2d %0.3f %4s buy %0.3f %0.5f sell %0.3f %0.5f  counts (b/s) %d/%d %s" % (g.step, g.ticker, g.mode, g.buy_quote_quantity, g.buy_base_quantity,
                g.sell_quote_quantity, g.sell_base_quantity, g.buy_count, g.sell_count, g.ex_orderid))
    
    assert setup_gbot4.total_buy_q() == 600
    assert setup_gbot4.total_sell_b() == 1.9124
    
    
@local_dynamo_avail   
def test_grid4_backtest(setup_gbot4):
    print("Grid...", setup_gbot4.gbot.gbotid)
    setup_gbot4.backtest(180)
    setup_gbot4.backtest(200)
    setup_gbot4.backtest(220.1)
    setup_gbot4.backtest(219.25)
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
    assert round(setup_gbot4.gbot.profit, 2) == 32.59
    assert round(setup_gbot4.gbot.step_profit, 2) == 39.36
    assert round(setup_gbot4.gbot.total_fees, 2) == 0.64
    
    
@local_dynamo_avail   
def test_grid4_backtest2(setup_gbot4):
    print("Grid...", setup_gbot4.gbot.gbotid)
    setup_gbot4.backtest(180)
    setup_gbot4.dynamic_grid_adjust(180)
    setup_gbot4.backtest(200)
    setup_gbot4.dynamic_grid_adjust(200)
    setup_gbot4.backtest(220.1)
    setup_gbot4.dynamic_grid_adjust(220.1)
    setup_gbot4.backtest(219.25)
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
    assert round(setup_gbot4.gbot.profit, 2) == 31.16
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
            'start_quote': 500, 
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
            'start_ticker': request.param}
    g = GbotRunner(config=config_gbot, type='pytest')
    print ("New gbot:", g.gbot.gbotid)
    yield g
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
    assert round(setup_gbot5.gbot.cost_basis,2) == 362.26
    assert round(setup_gbot5.base_cost(),2) == 150
    
    

    #setup_gbot5.backtest(219.25)
    #setup_gbot5.reset_grid(220.1)
    
   
    
 