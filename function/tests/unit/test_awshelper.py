## https://github.com/dsmorgan/yacgb
import pytest

import os

from ssm_cache import SSMParameterGroup

from yacgb.awshelper import better_bool, yacgb_aws_ps

aws_ssm_parameter_store = pytest.mark.skipif(os.environ.get('AWS_PS_GROUP') == None, 
                        reason="AWS PS testing disabled. Enable w/ export AWS_PS_GROUP=test")


@pytest.mark.parametrize("test_input,expected", [('y', True),
                                                ('true', True),
                                                ('True', True),
                                                ('TRUE', True),
                                                ('1', True),
                                                ('YEs', True),
                                                ('yes', True),
                                                ('2', False),
                                                ('-1', False),
                                                ('ok', False),
                                                ('no', False),
                                                ('X', False),
                                                ('None', False),
                                                ('', False),
                                                (True, True),
                                                (False, False), 
                                                (0, False),
                                                (1, True),
                                                (2, False),
                                                (0.1, False),
                                                (-1, False),
                                                (None, False)
                                                ])
def test_betterbool(test_input, expected):
    assert better_bool(test_input) == expected


@aws_ssm_parameter_store
def test_yacgb_aws_ps_live():
    testconfig = yacgb_aws_ps()
    assert testconfig.env == 'test'
    assert testconfig.configgrp != None
    print (testconfig.exch)
    assert testconfig.exch == {'binanceus': ['XLM/USD', 'ONE/USD', 'ADA/USD', 'ALGO/USD', 'ATOM/USD', 'BNB/USD', 'UNI/USD'], 'kraken': ['LTC/USD', 'FIL/USD']}
    assert testconfig.exch_apikey == {'binanceus': 'testapikey', 'kraken': 'testapikey'}
    assert testconfig.exch_secret == {'binanceus': 'testsecret', 'kraken': 'testsecret'}
    assert testconfig.exch_password == {'binanceus': None, 'kraken': None}
    assert testconfig.exch_sandbox == {'binanceus': False, 'kraken': False}
    assert len(testconfig.market_list) == 9
    assert testconfig.gbotids == ['testgbotid']
    
    
    assert testconfig.shuffled_gbotids == ['testgbotid']
    assert len(testconfig.new_exch) == 0
    assert len(testconfig.del_exch) == 0
    
    testconfig.collect()
    assert testconfig.exch == {'binanceus': ['XLM/USD', 'ONE/USD', 'ADA/USD', 'ALGO/USD', 'ATOM/USD', 'BNB/USD', 'UNI/USD'], 'kraken': ['LTC/USD', 'FIL/USD']}
    assert len(testconfig.new_exch) == 0
    assert len(testconfig.del_exch) == 0
    
    #need to change some internal parameters to simulate a change in PS, without actually changing anything in PS
    testconfig.env='test2'
    testconfig.configgrp = SSMParameterGroup(base_path='/'+testconfig.bp+'/'+testconfig.env)
    testconfig._last_refresh_time = None
    
    testconfig.collect()
    print (testconfig.exch)
    assert testconfig.exch == {'binanceus': ['XLM/USD'], 'kraken': ['LTC/USD'], 'coinbasepro': ['BTC/USD', 'ETH/USD']}
    print(testconfig.new_exch)
    assert len(testconfig.new_exch) == 2
    print(testconfig.del_exch)
    assert len(testconfig.del_exch) == 1
    

@aws_ssm_parameter_store
def test_yacgb_aws_ps_invalid():
    t = os.environ['AWS_PS_GROUP']
    os.environ['AWS_PS_GROUP'] = 'invalid'
    testconfig = yacgb_aws_ps()
    print (testconfig.exch)
    assert testconfig.env == 'invalid'
    assert testconfig.configgrp != None
    assert testconfig.exch == {}
    assert testconfig.exch_apikey == {}
    assert testconfig.exch_secret == {}
    assert testconfig.exch_password == {}
    assert testconfig.exch_sandbox == {}
    assert testconfig.market_list == []
    assert testconfig.gbotids == ['not_set']
    assert testconfig.shuffled_gbotids == ['not_set']
    
    #reset back to what it was (necessary?)
    os.environ['AWS_PS_GROUP'] = t
 
    
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
    print (testconfig.exch)
    
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