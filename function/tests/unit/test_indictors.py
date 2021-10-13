## https://github.com/dsmorgan/yacgb
import pytest

import os, datetime, time
from datetime import timezone

from yacgb.lookup import Candles
from yacgb.indicators import Indicators

@pytest.fixture
def setup_Indicators():
    ohlcv_list={}

    ohlcv_path = "function/tests/unit/ohlcv_data2/"
    included_extensions = ['.csv']
    file_names = [fn for fn in os.listdir(ohlcv_path)
              if any(fn.endswith(ext) for ext in included_extensions)]
    #print (file_names)
    for f in file_names:
        exchange = f.split('_', 1)[0]
        temp = f.split('_', 1)[1]
        ma = temp.split('__', 1)[0]
        mz = temp.split('__', 1)[1]
        mb = mz.split('_', 1)[0]
        market_symbol = ma + '/' + mb.split('_', 1)[0]
        timeframe = mz.split('_', 1)[1].rstrip('.csv')
        
        ca = Candles(timeframe)
        with open(ohlcv_path + f, 'r') as fl:
            while line := fl.readline():
                #convert to 1 int and 5 floats
                l = line.rstrip().split(',', 5)
                l[0]=int(l[0])
                for x in [1,2,3,4,5]:
                    l[x]=float(l[x])
                ca.append(l)
        print (exchange, market_symbol, timeframe, ca)

        ohlcv_list[exchange+'_'+market_symbol+'_'+timeframe] = ca
    
    print (len(ohlcv_list))
    # return dict of Candles
    yield (ohlcv_list)
    print("nothing to cleanup")
    
def test_Indicators_all(setup_Indicators):
    for x in setup_Indicators.keys():
        print (setup_Indicators[x])
        y = Indicators(setup_Indicators[x])
        print (y)
        assert y.rsi < 100
        assert y.rsi > 0
        
def test_Indicators_1m(setup_Indicators):
    x = setup_Indicators['pytest_ETH1/USD_1m'].aggregate('1m')
    print (x)
    xx = Indicators(x)
    print (xx)
    assert xx.rsi == 33.388027760616424
    
    y = x.aggregate('2m')
    print (y)
    yy = Indicators(y)
    print (yy)
    assert yy.rsi == 28.741090719199732
    
    z = x.aggregate('60m')
    print (z)
    zz = Indicators(z)
    print (zz)
    assert zz.rsi == 30.573834696240226
    assert zz.macd == -5.319450284596769
    assert zz.macds == -0.12164047515190028
    assert zz.macdh == -5.197809809444869

def test_Indicators_1m_indicator(setup_Indicators):
    i = setup_Indicators['pytest_ETH1/USD_1m'].aggregate('5m')
    print (i)
    ii = Indicators(i)
    print (ii)
    assert ii.rsi == 24.273064565786257
    assert ii.buy_indicator == False
    assert ii.sell_indicator == True
    
def test_Indicators_1m_jsonp(setup_Indicators):
    i = setup_Indicators['pytest_ETH1/USD_1m'].aggregate('5m')
    print (i)
    ii = Indicators(i)
    print (ii)
    print(ii.jsonp)
    assert ii.jsonp[:98] == '{"Indicators": {"rsi": 24.273064565786257, "buy_indicator": false, "sell_indicator": true, "macd":'
    assert ii.jsonp[-15:] == '"valid": true}}'