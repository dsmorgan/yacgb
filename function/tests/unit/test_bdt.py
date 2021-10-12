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
    
def test_bdt_offset():
    timeframe='1m'
    x = BacktestDateTime('20210626 17:00')
    x.addtf(timeframe, 61)
    assert x.dtstf(timeframe) == '20210626 18:01'
    assert x.dtskey(timeframe) == '20210626 18:00'
    timeframe='1h'
    x = BacktestDateTime('20210626 17:00')
    x.addtf(timeframe, 25)
    assert x.dtstf(timeframe) == '20210627 18:00'
    assert x.dtskey(timeframe) == '20210627 00:00'
    timeframe='1d'
    x = BacktestDateTime('20210626 17:00')
    assert x.ccxt_timestamp(timeframe) == 1624665600000
    x.addtf(timeframe, 31)
    assert x.dtstf(timeframe) == '20210727 00:00'
    assert x.ccxt_timestamp(timeframe) == 1627344000000
    assert x.dtskey(timeframe) == '20210701 00:00'
    
def test_bdt_offset_negative():
    timeframe='1m'
    x = BacktestDateTime('20210626 17:00')
    x.addtf(timeframe, -61)
    assert x.dtstf(timeframe) == '20210626 15:59'
    assert x.ccxt_timestamp(timeframe) == 1624723140000
    assert x.dtskey(timeframe) == '20210626 15:00'
    assert x.ccxt_timestamp_key(timeframe) == 1624719600000
    timeframe='1h'
    x = BacktestDateTime('20210626 17:00')
    x.addtf(timeframe, -25)
    assert x.dtskey(timeframe) == '20210625 00:00'
    assert x.ccxt_timestamp_key(timeframe) == 1624579200000
    assert x.dtstf(timeframe) == '20210625 16:00'
    assert x.ccxt_timestamp(timeframe) == 1624636800000
    x.addtf(timeframe, -2)
    assert x.ccxt_timestamp_key(timeframe) == 1624579200000
    assert x.ccxt_timestamp(timeframe) == 1624629600000
    timeframe='1d'
    x = BacktestDateTime('20210626 17:00')
    x.addtf(timeframe, -31)
    assert x.dtstf(timeframe) == '20210526 00:00'
    assert x.ccxt_timestamp(timeframe) == 1621987200000
    assert x.dtskey(timeframe) == '20210501 00:00' 
    assert x.ccxt_timestamp_key(timeframe) == 1619827200000
    x.addkey(timeframe)
    assert x.dtskey(timeframe) == '20210601 00:00' 
    assert x.dtstf(timeframe) == '20210626 00:00'

def test_bdt_offset_day_corner():
    timeframe='1d'
    x = BacktestDateTime('20210531 17:23')
    x.addkey(timeframe)
    assert x.dtskey(timeframe) == '20210601 00:00'
    assert x.dtstf(timeframe) == '20210630 00:00'
    timeframe='1m'
    assert x.dtstf(timeframe) == '20210630 17:23'
    timeframe='1d'
    y = BacktestDateTime('20201231 04:20')
    y.addkey(timeframe, offset=2)
    assert y.dtstf(timeframe) == '20210228 00:00'
    
def test_bdt_now():
    x = BacktestDateTime()
    y = BacktestDateTime()
    assert x.__str__() == y.__str__()
    
def test_bdt_altformat():
    x = BacktestDateTime()
    y = BacktestDateTime("2021-07-13 02:39:32.467951+00:00")
    assert x.laterthan(y) == True
    assert y.laterthan(x) == False
    
def test_bdt_timestamp():
    ts = 1624723140000
    tf = '1m'
    x = BacktestDateTime(timestamp=ts)
    assert x.ccxt_timestamp(tf) == ts
    
def test_bdt_diffsec():
    x = BacktestDateTime('20210531 17:23')
    y = BacktestDateTime('20210531 17:25')
    assert x.diffsec(y) == -120
    assert y.diffsec(x) == 120
    
def test_bdt_difftf_1m():
    x = BacktestDateTime('20210531 17:23')
    y = BacktestDateTime('20210531 17:25')
    assert x.difftf('1m', y) == -120
    assert y.difftf('15m', x) == 120
    
def test_bdt_difftf_1h():
    x = BacktestDateTime('20210531 15:10')
    y = BacktestDateTime('20210531 17:21')
    assert x.difftf('1h', y) == -131
    assert y.difftf('12h', x) == 131
    
def test_bdt_difftf_1d():
    x = BacktestDateTime('20210531 12:15')
    y = BacktestDateTime('20210601 00:00')
    assert x.difftf('1d', y) == -11.75
    assert y.difftf('1d', x) == 11.75
    
    
    
