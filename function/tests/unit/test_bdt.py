## https://github.com/dsmorgan/yacgb
import pytest

from yacgb.bdt import BacktestDateTime

def test_betterbool():
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
    assert y.dtsmin() == '20210317 21:00:00'
    z.addmin()
    assert z.dtsmin() == '20210317 22:02:00'
    assert z.dtshour() == '20210317 22:00'
    
    # w and y are the same value, so neither of them are later
    assert w.laterthan(y) == False
    assert y.laterthan(w) == False



   
