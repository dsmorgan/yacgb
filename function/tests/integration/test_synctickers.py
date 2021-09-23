## https://github.com/dsmorgan/yacgb
import pytest

import os

from model.market import Market
from model.ohlcv import OHLCV

local_dynamo_avail = pytest.mark.skipif(os.environ.get('DYNAMODB_HOST') == None, 
                        reason="No local dynamodb, e.g. export DYNAMODB_HOST=http://localhost:8000")

@pytest.fixture
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
    yield None
    
    print ("Delete market:",test_exchange, test_market)
    m = Market(exchange=test_exchange, market=test_market)
    m.delete()
    x = test_exchange + '_' + test_market + '_'
    print ("Deleting OHLCV via scan:", x)
    for item in OHLCV.scan(OHLCV.ex_market_tf.startswith(x)):
        print ("...delete", item.ex_market_tf, item.timestamp)
        item.delete()
    

@local_dynamo_avail
def test_synctickers_1(setup_env):
    import synctickers
    
    resp = synctickers.lambda_handler(None, None)
    assert resp == "OK"