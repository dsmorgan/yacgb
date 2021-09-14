## https://github.com/dsmorgan/yacgb
import pytest

from yacgb.util import better_bool, event2config, configsetup

@pytest.mark.parametrize("test_input,expected", [('y', True),
                                                ('true', True),
                                                ('True', True),
                                                ('TRUE', True),
                                                ('1', True),
                                                ('YEs', True),
                                                ('yes', True),
                                                ('2', False),
                                                ('ok', False),
                                                ('no', False),
                                                ('X', False),
                                                ('', False),
                                                (True, True),
                                                (False, False), 
                                                (0, False),
                                                (1, True),
                                                (2, False),
                                                (0.1, False)
                                                ])
def test_better_bool(test_input, expected):
    assert better_bool(test_input) == expected


def test_event2config1():
    event={'exchange':'kraken', 'market_symbol':'LTC/USD'}
    exch={'kraken': ['LTC/USD']}
    
    c = event2config(event, exch, must_match=True)
    
    #Required
    assert len(c) == 25
    assert c['exchange'] == 'kraken'
    assert c['market_symbol'] == 'LTC/USD'
    #Defaults
    assert c['grid_spacing'] == 0.04
    assert c['total_quote'] == None
    assert c['max_ticker'] == None
    assert c['min_ticker'] == None
    assert c['reserve'] == 0
    assert c['live_balance'] == False
    assert c['profit_protect_percent'] == None
    #TODO: Would need to match an re, '20210610 02:32'
    #assert c['backtest_start'] == None
    #assert c['backtest_end'] == None
    
def test_configsetup1():
    e = {'exchange': 'kraken', 
        'market_symbol': 'LTC/USD', 
        'grid_spacing': 0.03, 
        'total_quote': 1000, 
        'max_ticker': 405, 
        'min_ticker': 277.11,
        'reserve': 0, 
        'live_balance': False, 
        'start_base': 0, 
        'start_quote': 3000, 
        'makerfee': 0.0026, 
        'takerfee': 0.0016, 
        'feecurrency': 'USD', 
        'backtest_start': '20210507 19:00', 
        'backtest_end': '20210510 01:00', 
        'backtest_timeframe': '1h', 
        'max_percent_start': 0.25, 
        'min_percent_start': 0.25, 
        'stop_loss': None, 
        'stop_loss_precent_min': 0.05, 
        'take_profit': None, 
        'take_profit_percent_max': 0.05,
        'init_market_order': False,
        'profit_protect_percent': 0.25,
        'start_ticker': 348.86}
    exch={'kraken': ['LTC/USD']}
    
    c = event2config(e, exch, must_match=True)
    c = configsetup(c, 100)
    
    assert len(c) == 26
    assert c['start_ticker'] == 100
    assert c['max_ticker'] == 125
    assert c['min_ticker'] == 75
    assert c['stop_loss'] == 71.25
    assert c['take_profit'] == 131.25
    assert c['profit_protect_percent'] == 0.25
    
    