## https://github.com/dsmorgan/yacgb
import pytest

import os

from yacgb.orderscapture import OrdersCapture


local_dynamo_avail = pytest.mark.skipif(os.environ.get('DYNAMODB_HOST') == None, 
                        reason="No local dynamodb, e.g. export DYNAMODB_HOST=http://localhost:8000")


@pytest.fixture(params=[['testgbot1', 'bogus', 0.01, 0.02]])
def setup_orders1(request):
    o = OrdersCapture(request.param[0], request.param[1], request.param[2], request.param[3])
    yield o
    o.delete_all()

    
@local_dynamo_avail
def test_orders1(setup_orders1):
 
    torder= {
        'symbol': 'XXX1/USD',
        'status':'canceled'
        }
    setup_orders1.add(4, torder)
    
    torder= {
        'symbol': 'XXX1/USD',
        'status':'closed',
        'type': 'limit',
        'side': 'sell',
        'price': 90,
        'average': 100,
        'amount': 4
        }
    setup_orders1.add(5, torder)
    
    assert len(setup_orders1.reset_list) == 1
    assert len(setup_orders1.closed_list) == 1
    assert setup_orders1.closed_list[0].cost == 400
    assert setup_orders1.closed_list[0].fee_cost == 4
    assert setup_orders1.closed_list[0].average == 100
    assert setup_orders1.closed_list[0].timestamp == 0
    
    torder= {
        'symbol': 'XXX1/USD',
        'status':'closed',
        'type': 'limit',
        'price': 100,
        'amount': 4,
        'fee': {'cost': .25, 'currency':'BNB'}
        }
    setup_orders1.add(6, torder)
    
    assert len(setup_orders1.closed_list) == 2
    assert setup_orders1.closed_list[1].fee_cost == 0.25
    assert setup_orders1.closed_list[1].fee_currency == 'BNB'

@local_dynamo_avail
def test_orders2(setup_orders1):    

# kraken and binaneus samples
    torders = [{   'amount': 2.0,
        'average': 246.11,
        'clientOrderId': '0',
        'cost': 492.22,
        'datetime': '2021-04-12T13:49:34.127Z',
        'fee': {'cost': 0.78, 'currency': 'USD', 'rate': None},
        'filled': 2.0,
        'id': 'OS63K7-6I4HL-4HIFIS',
        'info': {   'closetm': 1618239581.8319,
                    'cost': '492.22',
                    'descr': {   'close': '',
                                 'leverage': 'none',
                                 'order': 'buy 2.00000000 LTCUSD @ limit '
                                          '246.11',
                                 'ordertype': 'limit',
                                 'pair': 'LTCUSD',
                                 'price': '246.11',
                                 'price2': '0',
                                 'type': 'buy'},
                    'expiretm': 0,
                    'fee': '0.78',
                    'id': 'OS63K7-6I4HL-4HIFIS',
                    'limitprice': '0.00000',
                    'misc': '',
                    'oflags': 'fciq',
                    'opentm': 1618235374.1276,
                    'price': '246.11',
                    'reason': None,
                    'refid': None,
                    'starttm': 0,
                    'status': 'closed',
                    'stopprice': '0.00000',
                    'userref': 0,
                    'vol': '2.00000000',
                    'vol_exec': '2.00000000'},
        'lastTradeTimestamp': None,
        'postOnly': None,
        'price': 246.11,
        'remaining': 0.0,
        'side': 'buy',
        'status': 'closed',
        'stopPrice': 0.0,
        'symbol': 'LTC/USD',
        'timeInForce': None,
        'timestamp': 1618235374127,
        'trades': None,
        'type': 'limit'}, 
  {   'amount': 2116.0,
    'average': 0.4724999527410208,
    'clientOrderId': 'ios_6785a40b6a644f3f8477afa1d51db459',
    'cost': 999.8099,
    'datetime': '2021-04-20T04:48:54.191Z',
    'fee': None,
    'filled': 2116.0,
    'id': '79821916',
    'info': {   'clientOrderId': 'ios_6785a40b6a644f3f8477afa1d51db459',
                'cummulativeQuoteQty': '999.8099',
                'executedQty': '2116.00000000',
                'icebergQty': '0.00000000',
                'isWorking': True,
                'orderId': 79821916,
                'orderListId': -1,
                'origQty': '2116.00000000',
                'origQuoteOrderQty': '0.0000',
                'price': '0.4725',
                'side': 'BUY',
                'status': 'FILLED',
                'stopPrice': '0.0000',
                'symbol': 'XLMUSD',
                'time': 1618894134191,
                'timeInForce': 'GTC',
                'type': 'LIMIT',
                'updateTime': 1618901627812},
    'lastTradeTimestamp': None,
    'postOnly': False,
    'price': 0.4725,
    'remaining': 0.0,
    'side': 'buy',
    'status': 'closed',
    'stopPrice': 0.0,
    'symbol': 'XLM/USD',
    'timeInForce': 'GTC',
    'timestamp': 1618894134191,
    'trades': None,
    'type': 'limit'},
    {   'amount': 2.0,
        'average': 246.11,
        'clientOrderId': '0',
        'cost': 492.22,
        'datetime': '2021-04-12T13:49:34.127Z',
        'fee': {'cost': 0.78, 'currency': 'USD', 'rate': None},
        'filled': 2.0,
        'id': 'OS63K7-6I4HL-4HIFIS',
        'info': {   'closetm': '1618239581.8319',
                    'cost': '492.22',
                    'descr': {   'close': '',
                                 'leverage': 'none',
                                 'order': 'buy 2.00000000 LTCUSD @ limit '
                                          '246.11',
                                 'ordertype': 'limit',
                                 'pair': 'LTCUSD',
                                 'price': '246.11',
                                 'price2': '0',
                                 'type': 'buy'},
                    'expiretm': 0,
                    'fee': '0.78',
                    'id': 'OS63K7-6I4HL-4HIFIS',
                    'limitprice': '0.00000',
                    'misc': '',
                    'oflags': 'fciq',
                    'opentm': 1618235374.1276,
                    'price': '246.11',
                    'reason': None,
                    'refid': None,
                    'starttm': 0,
                    'status': 'closed',
                    'stopprice': '0.00000',
                    'userref': 0,
                    'vol': '2.00000000',
                    'vol_exec': '2.00000000'},
        'lastTradeTimestamp': None,
        'postOnly': None,
        'price': 246.11,
        'remaining': 0.0,
        'side': 'buy',
        'status': 'closed',
        'stopPrice': 0.0,
        'symbol': 'LTC/USD',
        'timeInForce': None,
        'timestamp': 1618235374127,
        'trades': None,
        'type': 'limit'}
    ]
    
    cnt = 0
    for t in torders:
        cnt +=1
        setup_orders1.add(cnt, t)
        
    assert len(setup_orders1.reset_list) == 0
    assert len(setup_orders1.closed_list) == 3
    assert setup_orders1.closed_list[0].fee_cost == 0.78
    assert setup_orders1.closed_list[0].timestamp == 1618239581831
    assert setup_orders1.closed_list[0].timestamp_st == '2021-04-12 14:59:41'
    assert setup_orders1.closed_list[1].fee_cost == 10
    assert setup_orders1.closed_list[1].timestamp == 1618901627812
    assert setup_orders1.closed_list[1].timestamp_st == '2021-04-20 06:53:47'
    #added to address scenario where closetm is a string (same data as closed_list[0])
    assert setup_orders1.closed_list[2].fee_cost == 0.78
    assert setup_orders1.closed_list[2].timestamp == 1618239581831
    assert setup_orders1.closed_list[2].timestamp_st == '2021-04-12 14:59:41'