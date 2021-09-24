## https://github.com/dsmorgan/yacgb

import os
import logging

from yacgb.bdt import BacktestDateTime
from yacgb.awshelper import decrypt_environ

logger = logging.getLogger(__name__)

def base_symbol(ms):
    return (ms.split('/', 1)[0])
    
def quote_symbol(ms):
    return (ms.split('/', 1)[1])
    
def orderid(eo):
    return (eo.split('_', 1)[1])

def get_os_env(env, required=True, encrypted=False):
    var = None
    if encrypted:
        if 'ENC_'+env in os.environ:
            return (decrypt_environ('ENC_'+env))
    if env in os.environ:
        var = os.environ[env]
        if encrypted:
            logger.warning("Unecrypted environment variable %s (use ENC_%s instead)" % (env, env))
    if required and var == None:
        logger.error("Required environment variable %s" % env)
        exit()
    return (var)
    
def better_bool(s):
    if isinstance(s, bool):
        return s
    elif isinstance(s, int):
        if s == 1:
            return True
        else:
            return False
    if isinstance(s, str) and s.lower() in ['true', '1', 'y', 'yes']:
        return (True)
    else:
        return (False)
            
def event2config(e, exch_dict, must_match=False):
    conf = {}
    #"exchange": "kraken",
    conf['exchange'] =e.get('exchange', "not_set")
    if (conf['exchange']=="not_set" or (must_match and not conf['exchange'] in exch_dict)):
        logger.critical("exchange in event config doesn't match environment %s::%s" % (conf['exchange'], str(exch_dict.keys())))
        exit()
    #"market_symbol": "LTC/USD", 
    conf['market_symbol'] =e.get('market_symbol', "not_set")
    if (conf['market_symbol']=="not_set" or (must_match and not conf['market_symbol'] in exch_dict[conf['exchange']])):
        logger.critical("market_symbol in event config doesn't match environment %s::%s" % (conf['market_symbol'], str(exch_dict[conf['exchange']])))
        exit()
    #"grid_spacing": 0.05, 
    conf['grid_spacing'] =e.get('grid_spacing', 0.04)
    #"total_quote": 1000, 
    conf['total_quote'] =e.get('total_quote', None)
    #"max_ticker": 300, 
    conf['max_ticker'] =e.get('max_ticker', None)
    #"min_ticker": 150, 
    conf['min_ticker'] =e.get('min_ticker', None)
    #"reserve": 0,
    conf['reserve'] =e.get('reserve', 0.0)
    #"live_balance": "False",
    conf['live_balance'] = better_bool(e.get('live_balance', False))
    #"start_base": 0,
    conf['start_base'] =e.get('start_base', 0.0)
    #"start_quote": 1100, 
    conf['start_quote'] = e.get('start_quote', 0.0)
    #"makerfee": 0.0026,
    conf['makerfee'] = e.get('makerfee', 0.0026)
    #"takerfee": 0.0016, 
    conf['takerfee'] = e.get('takerfee', 0.0016)
    #"feecurrency": "USD",
    conf['feecurrency'] = e.get('feecurrency', 'USD')
    #"start": "20210422 16:00",
    nowts = BacktestDateTime()
    conf['backtest_start'] = e.get('backtest_start', nowts.dtsmin())
    #"end": "20210422 17:00",
    conf['backtest_end'] = e.get('backtest_end', nowts.dtsmin())
    #"timeframe": "1h"
    conf['backtest_timeframe'] = e.get('backtest_timeframe', "1h")
    if conf['backtest_timeframe'] not in ['1d', '1h', '1m']:
        logger.warning("timeframe in event not valid (%s), setting to default: 1h" % conf['backtest_timeframe'])
        conf['backtest_timeframe'] = "1h"
    
    conf['max_percent_start'] = e.get('max_percent_start', None)
    conf['min_percent_start'] = e.get('min_percent_start', None)
    conf['stop_loss'] = e.get('stop_loss', None)
    conf['stop_loss_precent_min'] = e.get('stop_loss_precent_min', None)
    conf['take_profit'] = e.get('take_profit', None)
    conf['take_profit_percent_max'] = e.get('take_profit_percent_max', None)
    conf['init_market_order'] = better_bool(e.get('init_market_order', False))
    conf['profit_protect_percent'] = e.get('profit_protect_percent', None)
    conf['dynamic_grid'] = better_bool(e.get('dynamic_grid', False))
    return (conf)
    
def configsetup(c, start_ticker):
    c['start_ticker'] = start_ticker
    if c['max_percent_start']:
        c['max_ticker'] = start_ticker * (1+c['max_percent_start'])
    if c['min_percent_start']:
        c['min_ticker'] = start_ticker * (1-c['min_percent_start'])
    if not c['min_ticker'] or not c['max_ticker']:
        logger.critical("min_ticker (%s) and/or max_ticker (%s) not valid [start_ticker: %s]" %(str(c['min_ticker']), str(c['max_ticker']), str(start_ticker)))
        exit()
    if c['min_ticker'] > c['max_ticker']:
        logger.critical("min_ticker (%f) is greater then max_ticker (%f)" %(c['min_ticker'], c['max_ticker']))
        exit()
    #Stop Loss
    #"stop_loss": 200, <OR>
    #"stop_loss_precent_min": 0.05,
    if c['stop_loss_precent_min']:
        c['stop_loss'] = c['min_ticker'] * (1-c['stop_loss_precent_min'])
    if c['stop_loss'] and c['stop_loss'] > c['min_ticker']:
        logger.critical("stop_loss (%f) is greater then min_ticker (%f)" %(c['stop_loss'], c['min_ticker']))
        exit()
    #Take Profit
    #"take_profit": 320, <OR>
    #"take_profit_percent_max": 0.05,
    if c['take_profit_percent_max']:
        c['take_profit'] = c['max_ticker'] * (1+c['take_profit_percent_max'])
    if c['take_profit'] and c['take_profit'] < c['max_ticker']:
        logger.critical("take_profit (%f) is less then max_ticker (%f)" %(c['take_profit'], c['max_ticker']))
        exit()
    #Required to be set, no default for this parameter
    if not c['total_quote']:
        logger.critical("total_quote must be configured")
        exit()
    return (c)
    