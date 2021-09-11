import ccxt
import time
#import pprint
import datetime
from datetime import timezone

#pp = pprint.PrettyPrinter(indent=4)


ex = {'kraken_ETH/USD':'pytest_ETH1__USD', 'binanceus_XLM/USD':'pytest_XL2__USD'}
tf = {'1m': 500, '1h': 500, '1d': 500}


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
