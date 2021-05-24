## https://github.com/dsmorgan/yacgb
import pytest

from yacgb.ccxthelper import CandleTest, BalanceCalc

@pytest.fixture()
def fetchBalance_resp():
    return {  'LTC': {'free': None, 'total': 6.3004623, 'used': None},
    'USD': {'free': None, 'total': 1635.8293, 'used': None},
    'free': {'LTC': None, 'USD': None},
    'info': {'XLTC': '6.3004623000', 'ZUSD': '1635.8293'},
    'total': {'LTC': 6.3004623, 'USD': 1635.8293},
    'used': {'LTC': None, 'USD': None}}


@pytest.fixture()
def fetchOpenOrders_resp():
    return [{   'amount': 5.64174894,
        'average': 0.0,
        'clientOrderId': '0',
        'cost': 0.0,
        'datetime': '2021-05-20T04:57:02.498Z',
        'fee': {'cost': 0.0, 'currency': 'USD', 'rate': None},
        'filled': 0.0,
        'id': 'O3US6O-JL7UM-SYNSF5',
        'info': {   'cost': '0.00000',
                    'descr': {   'close': '',
                                 'leverage': 'none',
                                 'order': 'buy 5.64174894 LTCUSD @ limit '
                                          '177.25',
                                 'ordertype': 'limit',
                                 'pair': 'LTCUSD',
                                 'price': '177.25',
                                 'price2': '0',
                                 'type': 'buy'},
                    'expiretm': 0,
                    'fee': '0.00000',
                    'id': 'O3US6O-JL7UM-SYNSF5',
                    'limitprice': '0.00000',
                    'misc': '',
                    'oflags': 'fciq',
                    'opentm': 1621486622.4987,
                    'price': '0.00000',
                    'refid': None,
                    'starttm': 0,
                    'status': 'open',
                    'stopprice': '0.00000',
                    'userref': 0,
                    'vol': '5.64174894',
                    'vol_exec': '0.00000000'},
        'lastTradeTimestamp': None,
        'postOnly': None,
        'price': 177.25,
        'remaining': 5.64174894,
        'side': 'buy',
        'status': 'open',
        'stopPrice': 0.0,
        'symbol': 'LTC/USD',
        'timeInForce': None,
        'timestamp': 1621486622498,
        'trades': None,
        'type': 'limit'}]


@pytest.fixture()
def ohlcv_response():
    return [[1621567980000, 207.94, 209.09, 207.94, 208.95, 759.88464657],
    [1621568040000, 209.05, 209.16, 208.27, 208.73, 1096.8347085],
    [1621568100000, 208.84, 208.91, 208.01, 208.33, 73.79106818]]


def test_BalanceCalc1(fetchBalance_resp, fetchOpenOrders_resp):
    bal = BalanceCalc(fetchBalance_resp, 'LTC', 'USD')
    
    bal.openOrdersCalc(fetchOpenOrders_resp)
    
    assert bal.qsymbol() == None
    assert bal.calc_base_free == 6.3004623
    assert bal.calc_quote_free == 635.829300385


def test_CandleTest1(ohlcv_response):
    c = CandleTest(ohlcv_response)
    assert c.high == 209.16
    assert c.low == 207.94
    assert c.last == 208.33

