## https://github.com/dsmorgan/yacgb

import datetime
from datetime import timezone, timedelta
import logging
import re


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
    def __init__(self, mcache_expire_seconds=10, ocache_expire_seconds=10, mcache_maxsize=64, ocache_maxsize=2048, quiet=False):
        self.mcache_expire_seconds = mcache_expire_seconds
        self.ocache_expire_seconds = ocache_expire_seconds
        self.mcache_maxsize = mcache_maxsize
        self.ocache_maxsize = ocache_maxsize
        self.mcache = {}
        self.ocache = {}
        self.quiet=quiet
        
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
            logger.warning("cache evict: %s maxsize: %d" % (oldest, maxsize))
            del(cache[oldest])
        return
        
    def get_market(self, exchange, market_symbol):
        self._expire_cache(self.mcache, self.mcache_expire_seconds)
        self._evict_cache(self.mcache, self.mcache_maxsize) 
        
        #get from cache
        mkey = exchange + '_' + market_symbol
        if mkey in self.mcache.keys():
            logger.debug("get_market cache hit: %s" % mkey)
            return self.mcache[mkey]
        
        #else get from dynamodb
        #TODO: add rate-limiting
        try:
            mkt = Market.get(exchange, market_symbol)
            if self.quiet:
                logger.debug("get_market cache miss: %s" % mkey)
            else:
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
            logger.debug("get_ohlcv cache hit: %s" % oktkey)
            return self.ocache[oktkey]
        
        #else get from dynamodb
        try:
            o = OHLCV.get(okey, ktimestamp)
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
                logger.debug ("cache set: 1 & 2 are true, no cache expire")
                e = False
                
            last_btdt = BacktestDateTime(o.last)
            now_twomin_ago = BacktestDateTime()
            now_twomin_ago.addmin(-2)
            last_btdt_tf = BacktestDateTime(o.last)
            last_btdt_tf.addtf(timeframe, -1)
            if now_twomin_ago.laterthan(last_btdt) and last_btdt_tf.laterthan(array_last_btdt):
                logger.debug ("cache set: 3 & 4 are true, no cache expire")
                e = False
            if self.quiet:
                logger.debug("get_ohlcv cache miss: %s (%s)" % (oktkey, str(e)))
            else:
                logger.info("get_ohlcv cache miss: %s (%s)" % (oktkey, str(e)))
                
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
                    resp = Candle(ctimestamp, timeframe, x)
                    #print (resp)
                    return resp
        #We got through the entire array, and didn't find it OR the get_ohlcv failed
        resp = Candle(ctimestamp, timeframe)
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
        resp = Candles(timeframe=timeframe)
        err_cnt = 0
        last = 0
        
        while current.ccxt_timestamp_key(timeframe) <= end.ccxt_timestamp_key(timeframe):
            ans = self.get_ohlcv(exchange, market_symbol, timeframe, current.ccxt_timestamp_key(timeframe))
            if ans != None:
                resp.set_last(ans.last)
                for x in ans.array:
                    if x[0] >= start.ccxt_timestamp(timeframe) and x[0] <= end.ccxt_timestamp(timeframe):
                        last = x[0]
                        resp.append(x)
            else:
                err_cnt +=1
            current.addkey(timeframe)
            
        if len(resp.candles_array) != abs(count):
            logger.warning ("get_candles expected %d but only found %d %s %s %s %s %s" % (abs(count), len(resp.candles_array), exchange, market_symbol, timeframe, start, end))
        if err_cnt > 0:
            #TODO: need a test case for this
            logger.warning("get_candles %d missing ohlcv items %s %s %s %s %s" % (err_cnt, exchange, market_symbol, timeframe, start, end))
        if last != end.ccxt_timestamp(timeframe):
            logger.warning("get_candles end array %d expected %d (%fs) %s %s %s %s %s" % (last, end.ccxt_timestamp(timeframe), 
                        (end.ccxt_timestamp(timeframe)-last)/1000, exchange, market_symbol, timeframe, start, end))
        return(resp)
            
            
class Candle:
    def __init__(self, candle_timestamp, timeframe='1m', candle_array=[0,0,0,0,0,0]):
        self.timeframe=timeframe
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
        return ("<Candle %s t:%s o:%f h:%f l:%f c:%f v:%f ?:%s>" % (dt_st, self.timeframe, self.open, self.high, self.low, self.close, self.volume, self.valid))
        
        
class Candles:
    def __init__(self, timeframe='1m', candles_array=[], last=None):
        self.timeframe=timeframe
        self.last=last
        if len(candles_array)==0:
            self.valid = False
            self.candles_array = [[0,0,0,0,0,0]]
        else:
            self.valid = True
            self.candles_array = candles_array

    def set_last(self, last):
        self.last=last
    
    def append(self, candle_array):
        if self.valid == False:
            self.candles_array = []
            self.valid = True
        self.candles_array.append(candle_array)
        
    def update(self, candles_array):
        for c in candles_array:
            if c[0] > self.candles_array[-1][0]:
                # if the timestamp of the candle is later then the last timestamp in the current list, then append it to the list
                self.append(c)
            else:
                # otherwise, we need to check if the candle has a matching timestamp, so that we can replace it
                for i, v in enumerate(self.candles_array):
                    if v[0] == c[0]:
                        self.candles_array[i] = c
                        break
    @property     
    def open(self):
        return self.candles_array[0][1]
    
    @property    
    def high(self):
        ret = self.candles_array[0][2]
        for c in self.candles_array:
            if c[2] > ret:
                ret = c[2]
        return ret
    
    @property    
    def low(self):
        ret = self.candles_array[0][3]
        for c in self.candles_array:
            if c[3] < ret:
                ret = c[3]
        return ret
    
    @property    
    def close(self):
        return self.candles_array[-1][4]
    
    @property    
    def volume(self):
        ret = 0
        for c in self.candles_array:
            ret += c[5]
        return ret
    
    @property
    def wavg_close(self):
        t = 0
        v = 0
        for c in self.candles_array:
            t += c[4] * c[5]
            v += c[5]
        if v == 0:
            return 0
        return (t/v)
    
    @property
    def change(self):
        open = self.open
        if open == 0:
            return 0
        return round(((self.close-open)/open)*100, 3)
    
    @property
    def amplitude(self):
        open = self.open
        if open == 0:
            return 0
        return round((abs((self.high-open)/open) + abs((self.low-open)/open))*100, 3)
        
    def avg_volume(self, trim=True):
        if not trim or len(self.candles_array) < 2:
            return (self.volume/len(self.candles_array))
        a = 0
        for c in self.candles_array[:-1]:
            a += c[5]
        return (a/len(self.candles_array[:-1]))
        
    def dejitter_close(self, last=4):
        # take the last x entries of the candles_array, and remove the extreme high and low close values. 
        # If duplicate high and/or low values, then the most recent (last) close value is used.
        # The goal is to reduce chances of single candle drops or jumps from triggering stop_loss, take_profit, or profit_protect_percent
        size = last
        if len(self.candles_array) < size:
            size = len(self.candles_array)
        close = self.candles_array[-1][4]
        h_close = self.candles_array[-size][4]
        l_close = self.candles_array[-size][4]
        for x in self.candles_array[-size:]:
            if x[4] > h_close:
                h_close = x[4]
            elif x[4] < l_close:
                l_close = x[4]
        for y in self.candles_array[-size:]:
            if y[4] < h_close and y[4] > l_close:
                close = y[4]
        return close
    
    @property
    def last_candle_age(self):
        #this should adjust based on the current timestamp size
        nowbdt = BacktestDateTime()
        ts_bdt = BacktestDateTime(timestamp=self.candles_array[-1][0])
        return (nowbdt.difftf(self.timeframe, ts_bdt))
    
    @property    
    def ohlcv_age(self):
        nowbdt = BacktestDateTime()
        last_bdt = BacktestDateTime(self.last)
        return (nowbdt.diffsec(last_bdt))
        
    def aggregate(self, newtimeframe=None):
        #take an array of candles and aggregate into a new Candles. Usually requires starting with: 1m, 1h, 1d; but others might work as well 
        # (e.g. 5m if going to 10m).
        # See validate_tf for set of valid timeframes, which is restricted to ensure that the offsets always align across source and 
        # destination candles.
       
        #this function will always return an array, although valid=False would indicate its empty of problematic.
        ret = Candles(newtimeframe, last=self.last)
        
        #validate some inputs, parse the requested destination timeframe and compatability with the source timeframe
        if newtimeframe == None or self.valid == False:
            return ret
        increment_tf = validate_tf(self.timeframe, newtimeframe)
        if increment_tf < 1:
            return ret
        
        #first, need to align the source array and dest array. The dest array timeframe determines how aggregation will occur,
        # with the intent to ensure consistency across time.
        array_start = BacktestDateTime(timestamp=self.candles_array[0][0])
        new_start = BacktestDateTime(timestamp=(array_start.ccxt_timestamp_key(self.timeframe)))
        logger.debug("array_start %s new_start %s" %(array_start, new_start))
        while array_start.laterthan(new_start):
            new_start.addtf(self.timeframe, increment_tf)
            logger.debug("new_start.addtf(%d) %s" % (increment_tf, new_start))
        
        #new_start now points to the intersection timestamp, determine the next dest timestamp and use
        # match as an interim timestamp to match in between current and next timestamps.
        new_next = BacktestDateTime(timestamp=new_start.ccxt_timestamp(self.timeframe))
        new_next.addtf(self.timeframe, increment_tf)
        match = BacktestDateTime(timestamp=new_start.ccxt_timestamp(self.timeframe))
        started = False
        x = 0
        logger.debug("len(self.candles_array) %d" % len(self.candles_array))
        
        #Here we start to traverse the source array and stuff it into the destination array
        while x < len(self.candles_array):
            if started == False:
                if self.candles_array[x][0] >= new_start.ccxt_timestamp(self.timeframe):
                    #Match 1st candle
                    started = True
                    logger.debug("started %d %s" % (x, self.candles_array[x][0]))
                else:
                    #Haven't started yet, looking to match 1st candles
                    logger.debug("skipping %d %s" % (x, self.candles_array[x][0]))
                    x+=1
                
            if started == True:
                #all candle_array entries are evaluated from here on
                if self.candles_array[x][0] >= new_next.ccxt_timestamp(self.timeframe):
                    #skip to the next target candle
                    logger.warning("Skipping dest candle %s (match %s) source %s", new_start, match.ccxt_timestamp(self.timeframe), self.candles_array[x][0])
                    new_next.addtf(self.timeframe, increment_tf)
                    new_start.addtf(self.timeframe, increment_tf)
                    match = BacktestDateTime(timestamp=new_start.ccxt_timestamp(self.timeframe))
                
                elif self.candles_array[x][0] >= new_start.ccxt_timestamp(self.timeframe):
                    #the current candle (and possible the next increment of candles) belong in this dest candle
                    rr=[]
                    z=0
                    for y in range(0,increment_tf):
                        #catch an unlikley scenario, if we find candles out of order we  need to skip them
                        while x < len(self.candles_array) and self.candles_array[x][0] < match.ccxt_timestamp(self.timeframe):
                            logger.error("source candle (%s) now earlier then match(%s) in destination %s, out of sequence" % 
                                            (self.candles_array[x][0], match.ccxt_timestamp(self.timeframe), new_start))
                            x+=1
                          
                        #We have to check this again in case the while loop ran to end of array (corner case)
                        if x >= len(self.candles_array):
                            logger.debug("end of source array %d, break" % x)
                            break  
            
                        #try to fill the dest candle with up to increment of source candles
                        if self.candles_array[x][0] == match.ccxt_timestamp(self.timeframe):
                            rr.append(self.candles_array[x])
                            x+=1
                            z+=1
                        else: #self.candles_array[x][0] > match.ccxt_timestamp(self.timeframe)
                            logger.warning("source candle missing, found (%s) but match (%s) for destination %s" % 
                                            (self.candles_array[x][0], match.ccxt_timestamp(self.timeframe), new_start))
                        match.addtf(self.timeframe)

                        
                    logger.debug ('destination %s source array(%d) %s' %(new_start, len(rr), rr))

                    if z > 0:
                        r = []
                        high = []
                        low = []
                        close = None
                        volume = 0
                        # timestamp 0
                        r.append(new_start.ccxt_timestamp(self.timeframe))
                        # open 1
                        r.append(rr[0][1])
 
                        for i in rr:
                            high.append(i[2])
                            low.append(i[3])
                            close = i[4]
                            volume += i[5]
                        
                        #high 2   
                        r.append(max(high))
                        #low 3
                        r.append(min(low))
                        #close 4
                        r.append(close)
                        #volume 5
                        r.append(volume)
                        logger.debug("output %s" % r)
                        ret.append(r)

                    new_start.addtf(self.timeframe, increment_tf)
                    new_next.addtf(self.timeframe, increment_tf)
                    match = BacktestDateTime(timestamp=new_start.ccxt_timestamp(self.timeframe))
                    
        return (ret)
    
    @property
    def dts_st(self):
        dts = datetime.datetime.fromtimestamp(int(self.candles_array[0][0]/1000), tz=timezone.utc)
        return(dts.strftime('%Y%m%d %H:%M'))
        
    @property
    def dte_st(self):
        dte = datetime.datetime.fromtimestamp(int(self.candles_array[-1][0]/1000), tz=timezone.utc)
        return(dte.strftime('%Y%m%d %H:%M'))
    
    def __str__(self):
        return ("<Candles s:%s e:%s t:%s o:%f h:%f l:%f c:%f wac:%f v:%f av:%f pc:%f pa:%f lca:%f age:%f ?:%s>" % (self.dts_st, self.dte_st, self.timeframe, self.open, self.high, 
                        self.low, self.close, self.wavg_close, self.volume, self.avg_volume(), self.change, self.amplitude, self.last_candle_age, self.ohlcv_age, self.valid))
                        
def validate_tf(current_tf, new_tf=None):
    validtfs = {'m': [1,2,3,4,5,6,10,12,15,20,30,60],
                'h': [1,2,3,4,6,8,12,24],
                'd': [1]
                }
    c = re.findall(r'(\d+|[mhd])', current_tf)
    if len(c) != 2:
        #parse issue, return a negative number
        return(-2)
    
    if new_tf == None:
        #just return an integer as it was valid
        return int(c[0])
        
    n = re.findall(r'(\d+|[mhd])', new_tf)
    if len(n) != 2:
        #parse issue, return a negative number
        return(-1)
    
    if c[1] != n[1] or int(c[0]) < 1 or int(c[0]) > int(n[0]):
        #the new and old are not the same type, return 0
        return (0)
    

    r = int(n[0]) // int(c[0])
    if r in validtfs[n[1]]:
        return r
    return (0)
    
    
    
                        