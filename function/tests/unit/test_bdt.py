## https://github.com/dsmorgan/yacgb
import pytest

from yacgb.bdt import BacktestDateTime

def test_bdt():
    x = BacktestDateTime()
    y = BacktestDateTime('20210317 21:00')
    z = BacktestDateTime('20210317 20:00')
    
    assert y.laterthan(x) == False
    assert x.laterthan(y) == True
    assert y.laterthan(z) == True
    z.addmin()
    z.addhour()
    assert y.laterthan(z) == False
    w = BacktestDateTime(z.dtshour())
    z.addmin(min=60)
    assert z.dtshour() == '20210317 22:00'
    assert y.laterthan(z) == False
    assert y.dtsmin() == '20210317 21:00'
    z.addmin()
    assert z.dtsmin() == '20210317 22:02'
    assert z.dtshour() == '20210317 22:00'
    
    # w and y are the same value, so neither of them are later
    assert w.laterthan(y) == False
    assert y.laterthan(w) == False

def test_bdt_min():
    timeframe = '1m'
    x = BacktestDateTime('20210629 19:59')
    y = BacktestDateTime('20210629 20:02')
    z = BacktestDateTime('20210628 23:58')
    
    assert x.laterthan(y) == False
    x.addtf(timeframe)
    x.addtf(timeframe)
    x.addtf(timeframe)
    x.addtf(timeframe)
    assert x.laterthan(y) == True
    z.addtf(timeframe)
    z.addtf(timeframe)
    z.addtf(timeframe)
    assert z.dtstf(timeframe) == '20210629 00:01'
    
def test_bdt_hour():
    timeframe = '1h'
    x = BacktestDateTime('20210629 17:00')
    y = BacktestDateTime('20210629 20:02')
    z = BacktestDateTime('20210628 23:58')
    
    assert x.laterthan(y) == False
    x.addtf(timeframe)
    x.addtf(timeframe)
    x.addtf(timeframe)
    x.addtf(timeframe)
    assert x.laterthan(y) == True
    z.addtf(timeframe)
    z.addtf(timeframe)
    z.addtf(timeframe)
    assert z.dtstf(timeframe) == '20210629 02:00'
    
def test_bdt_day():
    timeframe = '1d'
    x = BacktestDateTime('20210626 17:00')
    y = BacktestDateTime('20210629 20:02')
    z = BacktestDateTime('20210628 23:58')
    
    assert x.laterthan(y) == False
    x.addtf(timeframe)
    x.addtf(timeframe)
    x.addtf(timeframe)
    x.addtf(timeframe)
    assert x.laterthan(y) == True
    z.addtf(timeframe)
    z.addtf(timeframe)
    z.addtf(timeframe)
    assert z.dtstf(timeframe) == '20210701 00:00'
    

   
