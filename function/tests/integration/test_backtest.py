## https://github.com/dsmorgan/yacgb
import pytest

import os

from yacgb.bdt import BacktestDateTime

from model.market import Market
from model.ohlcv import OHLCV
from model.gbot import Gbot 
from model.orders import Orders


local_dynamo_avail = pytest.mark.skipif(os.environ.get('DYNAMODB_HOST') == None, 
                        reason="No local dynamodb, e.g. export DYNAMODB_HOST=http://localhost:8000")

@pytest.fixture()
def setup_env():
    #Careful that this doesn't overlap with real exchange/market_symbol values you may use locally, otherwise it will get deleted on clean up. 
    #  However, these values need to exist on the sandbox api service    
    test_exchange = 'binanceus'
    test_market = 'ETH/BUSD'
    
    os.environ['AWS_PS_GROUP'] = 'test'
    os.environ['EXCHANGE'] = test_exchange
    os.environ['MARKET_SYMBOL'] = test_market
    #os.environ['API_KEY'] = 'test_api_key_value'
    #os.environ['SECRET'] = 'test_secret'
    #os.environ['PASSWORD'] = 'test_password'
    #os.environ['GBOTID'] = 'test_gbotid'
    os.environ['SANDBOX'] = 'true'
    yield [test_exchange, test_market]
    
    print ("Delete market:",test_exchange, test_market)
    m = Market(exchange=test_exchange, market=test_market)
    m.delete()
    x = test_exchange + '_' + test_market + '_'
    print ("Deleting OHLCV via scan:", x)
    for item in OHLCV.scan(OHLCV.ex_market_tf.startswith(x)):
        print ("...delete", item.ex_market_tf, item.timestamp)
        item.delete()

@pytest.fixture()
def setup_backtest_event(setup_env):
    start = BacktestDateTime()
    start.addtf(tf='1h', offset=-240)
    end = BacktestDateTime()
    end.addtf(tf='1h', offset=-1)
    
    config_gbot= {'exchange': setup_env[0], 
            'market_symbol': setup_env[1], 
            'grid_spacing': 0.02, 
            'total_quote': 10000, 
            'min_percent_start': 0.25, 
            'max_percent_start': 0.25, 
            'reserve': 0, 
            'live_balance': 'False', 
            'start_base': 7500, 
            'start_quote': 7500, 
            'makerfee': 0.001, 
            'takerfee': 0.001, 
            'feecurrency': 'USD', 
            'backtest_start': start.dtstf('1h'), 
            'backtest_end': end.dtstf('1h'), 
            'backtest_timeframe': '1h',
            'dynamic_grid': 'False'}
            
    yield(config_gbot)

    
@pytest.fixture()
def setup_synctickers(setup_env):
    import synctickers
    sresp = synctickers.lambda_handler(None, None)
    assert sresp == "OK"
    yield sresp

@pytest.fixture()
def run_backtest(setup_synctickers, setup_backtest_event):
    import backtest
    bresp = backtest.lambda_handler(setup_backtest_event, None)
    yield bresp
    
    print ("Delete any Orders records:", bresp['gbotid'])
    for o in Orders.scan(Orders.gbotid == bresp['gbotid']):
        print(o.ex_orderid)
    print ("Delete gbot:", bresp['gbotid'])
    g = Gbot.get(bresp['gbotid'])
    g.delete()
    
    
@local_dynamo_avail
def test_backtest(run_backtest):
    assert list(run_backtest.keys())[0] == "gbotid"