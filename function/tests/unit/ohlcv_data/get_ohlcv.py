import ccxt
import time
#import pprint
import datetime
from datetime import timezone

#pp = pprint.PrettyPrinter(indent=4)


ex = {'binanceus_BTC/USD':'pytest_XXX1__USD', 'kraken_BTC/USD':'pytest_XXX2__USD', 'coinbasepro_BTC/USD':'pytest_XXX3__USD',
    'binanceus_ETH/USD':'pytest_YYY1__USD','kraken_ETH/USD':'pytest_YYY2__USD', 'coinbasepro_ETH/USD':'pytest_YYY3__USD',
    'binanceus_ADA/USD':'pytest_ZZZ1__USD','kraken_ADA/USD':'pytest_ZZZ2__USD', 'coinbasepro_ADA/USD':'pytest_ZZZ3__USD'}
tf = {'1m': 660, '1h': 360, '1d': 62}


for key in ex:
    exchange = key.split('_', 1)[0]
    market_symbol = key.split('_', 1)[1]
    #ms = ex[key].split('_', 1)[1]
    myexch = eval ('ccxt.%s ()' % exchange)
    myexch.load_markets()
    for tf_key in tf:
        timeframe = tf_key
        lim = tf[tf_key]
        print ("==", key, ex[key], tf_key, str(tf[tf_key]), "==")
        print ("Now Local Time:", datetime.datetime.now(timezone.utc))
        fticker = myexch.fetchOHLCV(market_symbol, timeframe, limit=lim)
        print ("Last OHLCV Time:", datetime.datetime.fromtimestamp(fticker[-1][0]/1000, tz=timezone.utc))
        print("")
        filename = ex[key] + '_' + timeframe + '.csv'
        with open(filename, 'w') as fl:
            for x in fticker:
                line = ''
                for y in x:
                    line += str(y) + ','
                line = line[:-1]
                print(line, file=fl)
    time.sleep(1)
