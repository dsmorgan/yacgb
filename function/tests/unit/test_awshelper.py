## https://github.com/dsmorgan/yacgb
import pytest

import os

from yacgb.awshelper import better_bool, yacgb_aws_ps



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
def test_betterbool(test_input, expected):
    assert better_bool(test_input) == expected


def test_yacgb_aws_ps_env():
    os.environ['AWS_PS_GROUP'] = 'test'
    os.environ['EXCHANGE'] = 'binanceus'
    os.environ['MARKET_SYMBOL'] = 'XLM/USD'
    os.environ['API_KEY'] = 'test_api_key_value'
    os.environ['SECRET'] = 'test_secret'
    #os.environ['PASSWORD'] = 'test_password'
    os.environ['GBOTID'] = 'test_gbotid'
    os.environ['SANDBOX'] = 'true'
    
    testconfig = yacgb_aws_ps()
    
    assert testconfig.env == 'test'
    assert testconfig.configgrp == None
    assert testconfig.exch == {'binanceus': ['XLM/USD']}
    assert testconfig.exch_apikey == {'binanceus': 'test_api_key_value'}
    assert testconfig.exch_secret == {'binanceus': 'test_secret'}
    assert testconfig.exch_password == {'binanceus': None }
    assert testconfig.exch_sandbox == {'binanceus': True }
    assert testconfig.market_list == ['binanceus:XLM/USD']
    assert testconfig.gbotids == ['test_gbotid']
    assert testconfig.shuffled_gbotids == ['test_gbotid']
   
