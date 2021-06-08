## https://github.com/dsmorgan/yacgb
import pytest

import os

from yacgb.gbotrunner import GbotRunner


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
            'start_ticker': request.param}
    g = GbotRunner(config=config_gbot, type='pytest')
    print ("New gbot:", g.gbot.gbotid)
    yield g
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
            'start_base': 0, 
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
            'start_ticker': request.param}
    g = GbotRunner(config=config_gbot, type='pytest')
    print ("New gbot:", g.gbot.gbotid)
    yield g
    print ("Delete gbot:", g.gbot.gbotid)
    g.gbot.delete()



@local_dynamo_avail
def test_grid1(setup_gbot1):
    
    total_quantity_buy=0
    total_sell=0
    total_quantity_sell=0
    print("Grid...", setup_gbot1.gbot.gbotid)
    for g in setup_gbot1.gbot.grid:
        print (g.step, g.ticker, 'q_step:', g.buy_quote_quantity, g.mode, 'b_b:', g.buy_base_quantity, 's_q:', g.sell_quote_quantity, 
                's_b:', g.sell_base_quantity, 't:', g.take, 's_t:', g.step_take, 'counts (b/s)', g.buy_count, g.sell_count, g.ex_orderid)
                
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
    
    
    
    