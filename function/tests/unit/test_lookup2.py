## https://github.com/dsmorgan/yacgb
import pytest

import os, datetime, time
from datetime import timezone

from yacgb.lookup import validate_tf, Candles

@pytest.fixture
def setup_Candles_aggregate():
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
    

def test_validate_tf():
    #just validate
    assert validate_tf('1m') == 1
    assert validate_tf('1h') == 1
    assert validate_tf('1x') == -2
    assert validate_tf('5d') == 5
    assert validate_tf('60m') == 60
    #validate between current and new
    assert validate_tf('1m', '1x') == -1
    assert validate_tf('1m', '1m') == 1
    assert validate_tf('1h', '1h') == 1
    assert validate_tf('1d', '1d') == 1
    assert validate_tf('1m', '2m') == 2
    assert validate_tf('1m', '3m') == 3
    assert validate_tf('1m', '4m') == 4
    assert validate_tf('1m', '5m') == 5
    assert validate_tf('1m', '6m') == 6
    assert validate_tf('1m', '10m') == 10
    assert validate_tf('1m', '15m') == 15
    assert validate_tf('1m', '30m') == 30
    assert validate_tf('1m', '60m') == 60
    assert validate_tf('1m', '24m') == 0
    assert validate_tf('1h', '2h') == 2
    assert validate_tf('1h', '3h') == 3
    assert validate_tf('1h', '4h') == 4
    assert validate_tf('1h', '6h') == 6
    assert validate_tf('1h', '12h') == 12
    assert validate_tf('1h', '24h') == 24
    assert validate_tf('1h', '7h') == 0
    assert validate_tf('4h', '1h') == 0
    #not sure why this ignores negatives
    assert validate_tf('1h', '-3h') == 3
    # not supported yet
    assert validate_tf('1d', '7d') == 0
    #not expected, but could work
    assert validate_tf('5m', '10m') == 2
    # side effect
    assert validate_tf('2m', '11m') == 5

def test_Candles_aggregate_500(setup_Candles_aggregate):
    for k in setup_Candles_aggregate.keys():
        tf = k.split('_', 2)[2]
        print ('input', tf, k, setup_Candles_aggregate[k])
        x = setup_Candles_aggregate[k].aggregate(tf)
        print ('output', x)
        assert x.valid == True
        assert len(x.candles_array) == 500

def test_Candles_aggregate_invalidtf(setup_Candles_aggregate):
    invalid_tfs={
        '1m':['2d','30d', '1h', '2h', '3h', '15h', '60h', '24m', '8m', '1d'],
        '1h':['2d','30d', '60h', '1m', '2m', '6m', '60m', '4m', '24m', '1d', '5h'],
        '1d':['2d','30d', '1h', '2h', '3h', '15h', '60h', '1m', '2m', '6m', '60m', '4m', '24m']
    }
    for k in setup_Candles_aggregate.keys():
        tf = k.split('_', 2)[2]
        for itf in invalid_tfs[tf]:
            print ('input', itf, k, setup_Candles_aggregate[k])
            x = setup_Candles_aggregate[k].aggregate(itf)
            print ('output', x)
            assert x.valid == False
            assert len(x.candles_array) == 1

def test_Candles_aggregate_1m(setup_Candles_aggregate):
    k = 'pytest_ETH1/USD_1m'
    tfc_array = [['2m', 250], ['3m', 167], ['4m', 125], ['5m', 100], ['6m', 83], ['10m', 50], ['12m', 41], ['15m', 34], ['20m', 25], ['30m', 17], ['60m', 8]]
    for tfc in tfc_array: 
        print ('input', tfc[0], k, setup_Candles_aggregate[k], len(setup_Candles_aggregate[k].candles_array))
        x = setup_Candles_aggregate[k].aggregate(tfc[0])
        print ('output', x, len(x.candles_array))
        assert x.valid == True
        assert len(x.candles_array) == tfc[1]
        
def test_Candles_aggregate_1h(setup_Candles_aggregate):
    k = 'pytest_ETH1/USD_1h'
    tfc_array = [['2h', 250], ['3h', 167], ['4h', 125], ['6h', 83], ['8h', 62], ['12h', 41], ['24h', 20]]
    for tfc in tfc_array: 
        print ('input', tfc[0], k, setup_Candles_aggregate[k], len(setup_Candles_aggregate[k].candles_array))
        x = setup_Candles_aggregate[k].aggregate(tfc[0])
        print ('output', x, len(x.candles_array))
        assert x.valid == True
        assert len(x.candles_array) == tfc[1]  
        
def test_Candles_aggregate_compare_60m(setup_Candles_aggregate):
    m = setup_Candles_aggregate['pytest_ETH1/USD_1m'].aggregate('60m')
    print ("testing", m, len(m.candles_array))
    print ("against", setup_Candles_aggregate['pytest_ETH1/USD_1h'], len(setup_Candles_aggregate['pytest_ETH1/USD_1h'].candles_array))
    
    found = 0
    for x in m.candles_array[:-1]:
        print("search", x)
        for y in setup_Candles_aggregate['pytest_ETH1/USD_1h'].candles_array:
            if x[0] == y[0]:
                found +=1
                print ("match", y)
                assert x[1] == y[1]
                assert x[2] == y[2]
                assert x[3] == y[3]
                assert x[4] == y[4]
                assert round(x[5],3) == round(y[5],3)
    #because the 1m and 1h candles weren't collected at exactly the same time, the last candles don't match exactly, so skipping it
    assert found == 7

def test_Candles_aggregate_compare_24h(setup_Candles_aggregate):
    h = setup_Candles_aggregate['pytest_ETH1/USD_1h'].aggregate('24h')
    print ("testing", h, len(h.candles_array))
    print ("against", setup_Candles_aggregate['pytest_ETH1/USD_1d'], len(setup_Candles_aggregate['pytest_ETH1/USD_1d'].candles_array))
    
    found = 0
    for x in h.candles_array[:-1]:
        print("search", x)
        for y in setup_Candles_aggregate['pytest_ETH1/USD_1d'].candles_array:
            if x[0] == y[0]:
                found +=1
                print ("match", y)
                assert x[1] == y[1]
                assert x[2] == y[2]
                assert x[3] == y[3]
                assert x[4] == y[4]
                assert round(x[5],3) == round(y[5],3)
    #because the 1h and 1d candles weren't collected at exactly the same time, the last candles don't match exactly, so skipping it
    assert found == 19
