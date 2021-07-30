## https://github.com/dsmorgan/yacgb

import datetime
from datetime import timezone, timedelta
import logging


from model.ohlcv import OHLCV
from model.market import Market
from yacgb.ohlcv_sync import key_time, valid_time, max_array_size
from yacgb.bdt import BacktestDateTime

logger = logging.getLogger(__name__)

class cacheItem:
    def __init__(self, key, item, expire=True):
        self.c_key = key
        self.c_item = item
        self.c_expire = expire
        self.c_timestamp = datetime.datetime.now(timezone.utc)
        
    def __getattr__(self, attr):
        return self.c_item[attr]
        
    def __str__(self):
        return ("<cacheItem %s (c_expire: %s) %s>" % (self.c_key, self.c_expire, self.c_timestamp))
        

class ohlcvLookup:
    def __init__(self, mcache_expire_seconds=10, ocache_expire_seconds=10, mcache_maxsize=32, ocache_maxsize=128):
        self.mcache_expire_seconds = mcache_expire_seconds
        self.ocache_expire_seconds = ocache_expire_seconds
        self.mcache_maxsize = mcache_maxsize
        self.ocache_maxsize = ocache_maxsize
        self.mcache = {}
        self.ocache = {}
        
    def __str__(self):
        mstr = ''
        ostr = ''
        for x in self.mcache:
            mstr += self.mcache[x].__str__() + '\n'
        for x in self.ocache:
            ostr += self.ocache[x].__str__() + '\n'
        return ("<ohlcvLookup\n...mcache %d/%d (%f)\n%s...ocache %d/%d (%f)\n%s>" % 
                (len(self.mcache), self.mcache_maxsize, self.mcache_expire_seconds, mstr,
                len(self.ocache), self.ocache_maxsize, self.ocache_expire_seconds, ostr))
        
    def _expire_cache(self, cache, expire_seconds):
        #go through each cache entry and expire if required
        nowt = datetime.datetime.now(timezone.utc)
        for ck in list(cache):
            if cache[ck].c_expire and cache[ck].c_timestamp + timedelta(seconds=expire_seconds) < nowt:
                #print("cache expire: %s expire_seconds: %f" % (ck, expire_seconds))
                logger.info("cache expire: %s expire_seconds: %f" % (ck, expire_seconds))
                del(cache[ck])
        return
        
    def _evict_cache(self, cache, maxsize):
        #go through each cache entry and evict if required     
        while len(cache) >= maxsize:
            oldest_ts = datetime.datetime.now(timezone.utc)
            oldest = None
            for ck in list(cache):
                if cache[ck].c_timestamp < oldest_ts:
                    oldest_ts = cache[ck].c_timestamp
                    oldest = ck
            #print("cache evict: %s maxsize: %d" % (oldest, maxsize))
            logger.warning("cache evict: %s maxsize: %d" % (oldest, maxsize))
            del(cache[oldest])
        return
        
    def get_market(self, exchange, market_symbol):
        self._expire_cache(self.mcache, self.mcache_expire_seconds)
        self._evict_cache(self.mcache, self.mcache_maxsize) 
        
        #get from cache
        mkey = exchange + '_' + market_symbol
        if mkey in self.mcache.keys():
            #print("get_market cache hit: %s" % mkey)
            logger.info("get_market cache hit: %s" % mkey)
            return self.mcache[mkey]
        
        #else get from dynamodb
        #TODO: add rate-limiting
        try:
            mkt = Market.get(exchange, market_symbol)
            #print ("get_market cache miss: %s" % mkey)
            logger.info("get_market cache miss: %s" % mkey)
            #add something for caching?
            self.mcache[mkey] = cacheItem(mkey, mkt.to_dict())
            return self.mcache[mkey]
        
        #not in dynamodb either
        except Market.DoesNotExist:
            logger.warning("get_market not found: %s" % mkey)
        return None
    
    def get_ohlcv(self, exchange, market_symbol, timeframe, ktimestamp):
        self._expire_cache(self.ocache, self.ocache_expire_seconds)
        self._evict_cache(self.ocache, self.ocache_maxsize) 
        
        #get from cache
        okey = exchange + '_' + market_symbol + '_' + timeframe
        #value passed is already a ktimestamp
        #ktime = key_time(timeframe, stime)
        #ktimestamp = int(ktime.timestamp()*1000)
        oktkey = okey + '_' + str(ktimestamp)
        if oktkey in self.ocache.keys():
           #print("get_ohlcv cache hit: %s" % oktkey)
            logger.info("get_ohlcv cache hit: %s" % oktkey)
            return self.ocache[oktkey]
        
        #else get from dynamodb
        try:
            o = OHLCV.get(okey, ktimestamp)
            #print("get_ohlcv cache miss: %s" % oktkey)
            logger.info("get_ohlcv cache miss: %s" % oktkey)
            e = True
            # check that:
            # 1) o.array is full (need to look at timeframe and ktimestamp to determine how many elements that should be)
            # 2) o.array[-1][0] timstamp is earlier then 1 minute/1 hour/1 day ago (or greater then market )
            # 3) 2 minutes ago is later than o.last 
            # 4) o.last - 1 minute/1 hour/1 day (based on timeframe) is later then o.array[-1][0]
            # If 1 & 2 or 3 & 4 are True, then expire should equal false
            key_btdt = BacktestDateTime(timestamp=ktimestamp)
            array_last_btdt = BacktestDateTime(timestamp=o.array[-1][0])
            now_tf_ago = BacktestDateTime()
            now_tf_ago.addtf(timeframe, -1)
            if len(o.array) == max_array_size(timeframe, key_btdt.t.year, key_btdt.t.month) and now_tf_ago.laterthan(array_last_btdt):
                #print ("cache set: 1 and 2 are true, no cache expire")
                logger.info ("cache set: 1 and 2 are true, no cache expire")
                e = False
                
            last_btdt = BacktestDateTime(o.last)
            now_twomin_ago = BacktestDateTime()
            now_twomin_ago.addmin(-2)
            last_btdt_tf = BacktestDateTime(o.last)
            last_btdt_tf.addtf(timeframe, -1)
            if now_twomin_ago.laterthan(last_btdt) and last_btdt_tf.laterthan(array_last_btdt):
                #print ("cache set: 3 & 4 are true, no cache expire")
                logger.info ("cache set: 3 & 4 are true, no cache expire")
                e = False
            
            self.ocache[oktkey] = cacheItem(oktkey, o.to_dict(), expire=e)

            return self.ocache[oktkey]
        
        #not in dynamodb either
        except OHLCV.DoesNotExist:
            logger.warning("get_ohlcv not found: %s" % oktkey)
        return None          

    def get_candle(self, exchange, market_symbol, timeframe, stime):
        #convert string time format to datatime, ensure that the time is valid for a given timeframe
        #ctime = valid_time(timeframe, datetime.datetime.strptime(stime, "%Y%m%d %H:%M").replace(tzinfo=timezone.utc))
        ctime = valid_time(timeframe, datetime.datetime.strptime(stime+'+0000', "%Y%m%d %H:%M%z"))
        ctimestamp = int(ctime.timestamp()*1000)
        #determine timestamp key value based on timeframe (i.e. 1m, 1h, 1d)
        keyctime = key_time(timeframe, ctime)
        keyctimestamp = int(keyctime.timestamp()*1000)
        ans = self.get_ohlcv(exchange, market_symbol, timeframe, keyctimestamp)
        if ans != None:
            for x in ans.array:
                if x[0] == ctimestamp:
                    resp = Candle(ctimestamp, x)
                    #print (resp)
                    return resp
        #We got through the entire array, and didn't find it OR the get_ohlcv failed
        resp = Candle(ctimestamp)
        logger.warning("get_candle not found: %s %s %s %s %s" % (exchange, market_symbol, timeframe, stime, resp))
        return (resp)
        
    def get_candles(self, exchange, market_symbol, timeframe, stime, count):
        
        start = BacktestDateTime(stime)
        end = BacktestDateTime(stime)
        if count < 0:
            start.addtf(timeframe, count+1)
        else:
            end.addtf(timeframe, count-1)
        current = BacktestDateTime(start.dtstf(timeframe))
        resp = []
        err_cnt = 0
        last = 0
        
        while current.ccxt_timestamp_key(timeframe) <= end.ccxt_timestamp_key(timeframe):
            ans = self.get_ohlcv(exchange, market_symbol, timeframe, current.ccxt_timestamp_key(timeframe))
            if ans != None:
                for x in ans.array:
                    if x[0] >= start.ccxt_timestamp(timeframe) and x[0] <= end.ccxt_timestamp(timeframe):
                        last = x[0]
                        resp.append(x)
            else:
                err_cnt +=1
            current.addkey(timeframe)
            
        if len(resp) != abs(count):
            logger.warning ("get_candles expected %d but only found %d %s %s %s %s %s" % (abs(count), len(resp), exchange, market_symbol, timeframe, start, end))
        if err_cnt > 0:
            #TODO: need a test case for this
            logger.warning("get_candles %d missing ohlcv items %s %s %s %s %s" % (err_cnt, exchange, market_symbol, timeframe, start, end))
        if last != end.ccxt_timestamp(timeframe):
            logger.warning("get_candles end array %d expected %d (%fs) %s %s %s %s %s" % (last, end.ccxt_timestamp(timeframe), 
                        (end.ccxt_timestamp(timeframe)-last)/1000, exchange, market_symbol, timeframe, start, end))
        return(resp)
            
            
class Candle:
    def __init__(self, candle_timestamp, candle_array=[0,0,0,0,0,0]):
        if candle_array[0]==0:
            self.timestamp = candle_timestamp
            self.valid = False
        else:
            self.timestamp = candle_array[0]
            self.valid = True
        self.candle_array = candle_array
        self.open = candle_array[1]
        self.high = candle_array[2]
        self.low = candle_array[3]
        self.close = candle_array[4]
        self.volume = candle_array[5]
    def __str__(self):
        dt = datetime.datetime.fromtimestamp(int(self.timestamp/1000), tz=timezone.utc)
        dt_st = dt.strftime('%Y%m%d %H:%M')
        return ("<Candle %s o-%f h-%f l-%f c-%f v-%f ?-%s>" % (dt_st, self.open, self.high, self.low, self.close, self.volume, self.valid))
            
#TODO: Remove this once migrated to 
class OrderBookLookup:
    def __init__(self, exchange, market_symbol):
        self.exchange=exchange
        self.market_symbol=market_symbol
        self.ddb = OHLCV()
        self.last_keyptimestamp = None
        self.last_time_item = None
        self.key = None
    
    def getcandle(self, timeframe='1h', stime='20210317 21:10'):
        key = self.exchange+'_'+self.market_symbol+'_'+timeframe
        if key != self.key:
            self.key = key
            self.last_keyptimestamp = None
            
        ptime = datetime.datetime.strptime(stime, "%Y%m%d %H:%M").replace(tzinfo=timezone.utc)
        ptimestamp = int(ptime.timestamp()*1000)
        #if timeframe == '1h':
        #keyptime = ptime.replace(hour=0, minute=0, second=0, microsecond=0)
        keyptime = key_time(timeframe, ptime)
        keyptimestamp = int(keyptime.timestamp()*1000)
        self.open = 0
        self.close = 0
        self.high = 0
        self.low = 999999
        self.volume = 0
        self.cnt = 0

        if (keyptimestamp == self.last_keyptimestamp):
            #Prevent another query to the database, the record we were looking for is already in this object (last_time_item)
            time_item = self.last_time_item
        else:
            try:
                time_item = OHLCV.get(self.key, keyptimestamp)
                self.last_time_item = time_item
                self.last_keyptimestamp = keyptimestamp
                
            except OHLCV.DoesNotExist:
                logger.warn("Not found in table key: %s (%s %s %s %s)" %(str(self.key), str(keyptime), str(keyptimestamp), str(ptime), str(ptimestamp)))
                self.low=0
                return

        for x in time_item.array:
           if x[0] == ptimestamp:
                self.open = x[1]
                self.high = x[2]
                self.low = x[3]
                self.close = x[4]
                self.volume = x[5]
                self.cnt = 1
                return
        logger.warn("Not found in array: %s (%s %s %s %s)" %(str(self.key), str(keyptime), str(keyptimestamp), str(ptime), str(ptimestamp)))
        self.low=0
        