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
    if s.lower() in ['true', '1', 'y', 'yes']:
        return (True)
    else:
        return (False)

def exists_or_default(key, d, default):
    if key in d:
        return (d[key])
    else:
        return (default)
            
def event2config(e, exch, mark_sym, must_match=False):
    conf = {}
    #"exchange": "kraken",
    conf['exchange'] = exists_or_default('exchange', e, exch)
    if (must_match and e['exchange'] != exch):
        logger.critical("exchange in event config doesn't match environment %s::%s" % (e['exchange'], exch))
        exit()
    #"market_symbol": "LTC/USD", 
    conf['market_symbol'] = exists_or_default('market_symbol', e, exch)
    if (must_match and e['market_symbol'] != mark_sym):
        logger.critical("market_symbol in event config doesn't match environment %s::%s" % (e['market_symbol'], exch))
        exit()
    #"grid_spacing": 0.05, 
    conf['grid_spacing'] = exists_or_default('grid_spacing', e, 0.04)
    #"total_quote": 1000, 
    conf['total_quote'] = exists_or_default('total_quote', e, None)
    #"max_ticker": 300, 
    conf['max_ticker'] = exists_or_default('max_ticker', e, None)
    #"min_ticker": 150, 
    conf['min_ticker'] = exists_or_default('min_ticker', e, None)
    #"reserve": 0,
    conf['reserve'] = exists_or_default('reserve', e, 0.0)
    #"live_balance": "False",
    conf['live_balance'] = better_bool(exists_or_default('live_balance', e, "False"))
    #"start_base": 0,
    conf['start_base'] = exists_or_default('start_base', e, 0.0)
    #"start_quote": 1100, 
    conf['start_quote'] = exists_or_default('start_quote', e, 0.0)
    #"makerfee": 0.0026,
    conf['makerfee'] = exists_or_default('makerfee', e, 0.0026)
    #"takerfee": 0.0016, 
    conf['takerfee'] = exists_or_default('takerfee', e, 0.0016)
    #"feecurrency": "USD",
    conf['feecurrency'] = exists_or_default('feecurrency', e, 0.0016)
    #"start": "20210422 16:00",
    nowts = BacktestDateTime()
    conf['backtest_start'] = exists_or_default('backtest_start', e, nowts.dtsmin())
    #"end": "20210422 17:00",
    conf['backtest_end'] = exists_or_default('backtest_end', e, nowts.dtsmin())
    #"timeframe": "1h"
    conf['backtest_timeframe'] = exists_or_default('backtest_timeframe', e, "1h")
    if conf['backtest_timeframe'] not in ['1d', '1h', '1m']:
        logger.warning("timeframe in event not valid (%s), setting to default: 1h" % conf['backtest_timeframe'])
        conf['backtest_timeframe'] = "1h"
    
    conf['max_percent_start'] = exists_or_default('max_percent_start', e, None)
    conf['min_percent_start'] = exists_or_default('min_percent_start', e, None)
    conf['stop_loss'] = exists_or_default('stop_loss', e, None)
    conf['stop_loss_precent_min'] = exists_or_default('stop_loss_precent_min', e, None)
    conf['take_profit'] = exists_or_default('take_profit', e, None)
    conf['take_profit_percent_max'] = exists_or_default('take_profit_percent_max', e, None)
    
    return (conf)
    
def configsetup(c, start_ticker):
    if c['max_percent_start']:
        c['max_ticker'] = start_ticker * (1+c['max_percent_start'])
    if c['min_percent_start']:
        c['min_ticker'] = start_ticker * (1-c['min_percent_start'])
    if not c['min_ticker'] or not c['max_ticker']:
        logger.critical("min_ticker (%s) and/or max_ticker (%s) not valid" %(str(c['min_ticker']), str(c['max_ticker'])))
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
    