## https://github.com/dsmorgan/yacgb
import pytest

import os

from yacgb.gbotrunner import GbotRunner


local_dynamo_avail = pytest.mark.skipif(os.environ.get('DYNAMODB_HOST') == None, 
                        reason="No local dynamodb, e.g. export DYNAMODB_HOST=http://localhost:8000")


@pytest.fixture(params=[0.01, 10, 90, 150, 175, 200, 300, 1000, 10000, 1000000])
def setup_gbot(request):
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


@local_dynamo_avail
def test_grid1(setup_gbot):
    
    total_buy=0
    total_sell=0
    print("Grid...", setup_gbot.gbot.gbotid)
    for g in setup_gbot.grid_array:
        print (g.step, g.ticker, 'q_step:', g.quote_step, g.mode, 'b_b:', g.buy_base_quantity, 's_q:', g.sell_quote_quantity, 
                's_b:', g.sell_base_quantity, 't:', g.take, 's_t:', g.step_take, 'counts (b/s)', g.buy_count, g.sell_count, g.ex_orderid)
                
        if g.mode == 'buy':
            total_buy += g.ticker * g.buy_base_quantity
            
        if g.mode == 'sell':
            total_sell += g.ticker * g.sell_quote_quantity
       
    print ('total_buy', total_buy, 'total_sell', total_sell, 'total_quote', setup_gbot.gbot.config.total_quote)
    print(setup_gbot.gbot.gbotid)
    
    assert len(setup_gbot.grid_array) == setup_gbot.gbot.grids
    assert round(total_buy + (total_sell*(1/(1+setup_gbot.gbot.config.grid_spacing))), 2) == setup_gbot.gbot.config.total_quote
    

