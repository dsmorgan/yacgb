## https://github.com/dsmorgan/yacgb

import logging
import uuid
import jsonpickle

from model.gbot import Gbot

logger = logging.getLogger(__name__)


class Grid:
    def __init__(self, step=0, ticker=0):
        self.step = step
        self.ticker = ticker
        self.quote_step = 0
        self.buy_base_quantity = 0
        self.sell_quote_quantity = 0
        self.sell_base_quantity = 0
        self.mode = None
        self.take = 0
        self.step_take = 0
        self.buy_count = 0
        self.sell_count = 0
        self.ex_orderid = None

    
    def allocate(self, quote_step=0, sell_quantity=0, mode=None, take=0, step_take=0):
        self.quote_step = quote_step
        self.buy_base_quantity = self.quote_step/self.ticker
        self.sell_quote_quantity = sell_quantity
        self.sell_base_quantity = sell_quantity*self.ticker
        self.mode = mode
        self.take = take
        self.step_take = step_take

class GbotRunner:
    grid_array = []
    gbot = None
    
    # def setup(self, grid_spacing=0.0426, total_quote=2500, max_ticker=225.00, min_ticker=125, start_ticker=173.27, start_base=7.499, start_quote=1345.80):
    def __init__(self, gbotid=None, exchange=None, market_symbol=None, 
                # inputs
                grid_spacing=0, total_quote=0, max_ticker=0, min_ticker=0, reserve=0,
                # discovered from exchange/account
                start_ticker=0, start_base=0, start_quote=0, makerfee=0.005, takerfee=0.005, feecurrency='USD'):
        #RESET
        #Gbot.delete_table()
        
        if not Gbot.exists():
            Gbot.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
            logger.info('Created Dynamodb table Gbot')
        if gbotid != None:
            try:
                self.gbot = Gbot.get(gbotid)
                self.grid_array = jsonpickle.decode(self.gbot.grid)
                logger.info("Lookup existing gbot, gbotid: " + gbotid)
            except Gbot.DoesNotExist:
                logger.error('Unable to find gbot, gbotid: ' + gbotid)
                exit()
        else:
            # create a new bot
            self.gbot = Gbot(str(uuid.uuid1()), 
                    exchange=exchange, 
                    market_symbol=market_symbol,
                    
                    grid_spacing=grid_spacing,
                    total_quote=total_quote,
                    max_ticker=max_ticker,
                    min_ticker=min_ticker,
                    reserve=reserve,
                    
                    start_ticker=start_ticker, last_ticker=start_ticker,
                    start_base=start_base,
                    start_quote=start_quote,
                    makerfee=makerfee,
                    takerfee=takerfee,
                    feecurrency=feecurrency
                    )
            
            logger.info("Created new gbot, gbotid: " + self.gbot.gbotid)
            # initalize new bot
            self.setup()
            # not clear if I should save now, but probably a good idea
            #self.gbot.save()
    
    def save(self):
        self.gbot.grid = jsonpickle.encode(self.grid_array)
        self.gbot.save()
        
                

    def next_ticker(self, tick=0):
        if tick > 0:
            self.gbot.last_ticker=tick
            # find lowest sell and highest buy grids
            lowest_sell = 999999999
            highest_buy = 0
            sell_grid = -1
            buy_grid = -1
            #grid_below = -1
            #grid_above = -1
            reset_array = []
            for g in self.grid_array:
                if g.mode == 'sell' and g.ticker < lowest_sell:
                    lowest_sell = g.ticker
                    sell_grid = g.step
                if g.mode == 'sell' and g.ticker <= tick:
                    reset_array.append(g.step)
                if g.mode == 'buy' and g.ticker > highest_buy:
                    highest_buy = g.ticker
                    buy_grid = g.step
                if g.mode == 'buy' and g.ticker >= tick:
                    reset_array.insert(0,g.step)
            logger.debug("tick %.2f sell_grid %d @ %.2f buy_grid %d @ %.2f [%s]" %(tick, sell_grid, lowest_sell, buy_grid, highest_buy, str(reset_array)))  
            
            for gg in reset_array:
                self.reset(self.grid_array[gg].ticker)
        
        else:
            logger.info("Skipped ticker: " + str(tick))
    
    
    def check_id(self, exchange, orderid):
        for g in self.grid_array:
            #logger.info("Grid: \n%s" %str(g))
            if g.ex_orderid == exchange + '_' + orderid:
                logger.info("%d Matched %s" %(g.step, g.ex_orderid))
                return (g.step)
        return (None)
                
    
    
    def reset(self, grid_ticker=-1):
        # used to take last Buy and setup the next Limit Sell
        temp_ticker = 0
        temp_quantity = 0
        
        if grid_ticker > 0:
            for g in self.grid_array:
                if g.ticker == grid_ticker:
                    if g.mode == 'buy':
                        logger.info("Bought %.8f @ %.2f Total: %.2f" % (g.buy_base_quantity, g.ticker, g.ticker*g.buy_base_quantity))
                        self.gbot.base_balance += g.buy_base_quantity
                        #subtract the transaction cost from profit
                        self.gbot.total_fees += g.ticker*g.buy_base_quantity*self.gbot.makerfee
                        self.gbot.profit -= g.ticker*g.buy_base_quantity*self.gbot.makerfee
                        self.gbot.step_profit -= g.ticker*g.buy_base_quantity*self.gbot.makerfee
                        # take purchased amount (buy_base_quantity) and use to calculate sale and profit(s)
                        temp_ticker = g.ticker
                        temp_quantity = g.buy_base_quantity
                        self.gbot.transactions += 1
                        g.buy_count +=1
                        g.ex_orderid=None
                        g.mode = "NONE"
                    if g.mode == 'sell':
                        logger.info("Sold %.8f @ %.2f Total: %.2f" % (g.sell_quote_quantity, g.ticker, g.ticker*g.sell_quote_quantity))
                        self.gbot.quote_balance += g.ticker*g.sell_quote_quantity
                        self.gbot.total_fees += g.ticker*g.sell_quote_quantity*self.gbot.makerfee
                        self.gbot.profit += g.take - g.ticker*g.sell_quote_quantity*self.gbot.makerfee
                        self.gbot.step_profit += g.step_take - g.ticker*g.sell_quote_quantity*self.gbot.makerfee
                        self.gbot.transactions += 1
                        g.sell_count +=1
                        g.ex_orderid=None
                        g.mode =  "NONE"
                    break
        for g in self.grid_array:
            if g.mode ==  "NONE" and g.ticker != grid_ticker:
                if g.ticker < grid_ticker:
                    #buy
                    g.mode = "buy"
                    logger.info("Limit Buy %.8f @ %.2f Total: %.2f" % (g.buy_base_quantity, g.ticker, g.ticker*g.buy_base_quantity))
                    self.gbot.quote_balance -= g.ticker*g.buy_base_quantity
                else:
                    #sell
                    g.mode = "sell"
                    # change the sellbase and recalculate the profit
                    # g.sell_quote_quantity replaced with g.buy_base_quantity
                    if temp_quantity > 0: ######
                        #not sure why, but a limit sell following a sell, this doesn't work
                        g.sell_quote_quantity = temp_quantity
                        # use above g.ticker and this g.ticker
                        g.take = (g.ticker-temp_ticker) * temp_quantity
                        g.step_take = (g.ticker-temp_ticker) * temp_quantity
                        g.sell_base_quantity = g.sell_quote_quantity*g.ticker
                    logger.info("Limit Sell %.8f @ %.2f Total: %.2f" % (g.sell_quote_quantity, g.ticker, g.ticker*g.sell_quote_quantity))
                    self.gbot.base_balance -= g.sell_quote_quantity
            
       
    def setup(self):
        #leave some off for reserve
        usable_quote = self.gbot.total_quote * (1-self.gbot.reserve)
        #amt of total that is split at each step
       
        # check max larger then min
        #grid_step = (max_ticker - min_ticker)/(self.grids-1)
        now_ticker = self.gbot.min_ticker
        #track grids above start_ticker
        sell_count = 0
        sell_quantity = -1
        closest_grid = -1
        closest = 9999999
        #Create each grid
        while now_ticker <= self.gbot.max_ticker:
            # add a new grid
            self.grid_array.append(Grid(self.gbot.grids, now_ticker))
            if now_ticker > self.gbot.start_ticker:
                sell_count += 1
            if abs(self.gbot.start_ticker - now_ticker) < closest:
                closest = abs(self.gbot.start_ticker - now_ticker)
                closest_grid = self.gbot.grids
            #print (x, now_ticker)
            now_ticker = now_ticker*(1+self.gbot.grid_spacing)
            self.gbot.grids += 1
        
        #divide the usable amount evenly for each step, for buying 
        quote_step = usable_quote/(self.gbot.grids-1) 
        #use the current ticker to split the quantity to seel at each step
        # TODO: this should instead be sell the previous grid step, close enought for now
        sell_quantity = usable_quote/self.gbot.start_ticker/(self.gbot.grids-1) 
        
        
        #Determine total step and quote
        totalq = 0
        totalb = 0
        total_buy_b = 0
        total_sell_q = 0
        last_step = self.gbot.min_ticker

        for g in self.grid_array:
            if (closest_grid == g.step):
                g.allocate(quote_step, sell_quantity, "NONE", 0, (g.ticker-last_step)*sell_quantity)
            elif g.ticker > self.gbot.start_ticker:
                g.allocate(quote_step, sell_quantity, "sell", (g.ticker-self.gbot.start_ticker)*sell_quantity, (g.ticker-last_step)*sell_quantity)
                total_sell_q += g.sell_quote_quantity
                totalq += g.quote_step
                totalb += g.buy_base_quantity
            else:
                g.allocate(quote_step, sell_quantity, "buy", 0, (g.ticker-last_step)*sell_quantity)
                total_buy_b += g.quote_step
                totalq += g.quote_step
                totalb += g.buy_base_quantity
            logger.info(">%d %s %.2f (%.2f) <%d/%d> buybase %.8f sellbase %.8f [take %.2f/%.2f] %.2f" % (g.step, g.mode, g.ticker, g.quote_step, 
                                    g.buy_count, g.sell_count, g.buy_base_quantity, g.sell_quote_quantity, g.take, g.step_take, g.sell_base_quantity))
            # reset next step
            last_step = g.ticker
        logger.info("Theoretical: totalq %.2f totalb %.8f @ %.2f = %.2f" % (totalq, totalb, self.gbot.start_ticker, self.gbot.start_ticker*totalb)) 
        logger.info("Actual, based on current price in grid: total_buy_b %.2f total_sell_q %.8f" % (total_buy_b, total_sell_q)) 
        logger.info("start_quote %.2f start_base: %.8f @ %.2f = %.2f" % (self.gbot.start_quote, self.gbot.start_base, 
                                                self.gbot.last_ticker, self.gbot.start_quote + (self.gbot.start_base*self.gbot.last_ticker)))
        
        extra_q = 0
        extra_b = 0
        #### Check here if we have enough, total_buy_b is the total of all grids that are tagged as buy (in quote currency)
        if (total_buy_b > self.gbot.start_quote):
            # Not enough available quote currency (e.g. USD)
            need_quote = total_buy_b - self.gbot.start_quote
            logger.info("Need more: %.2f quote" % need_quote)
            ### Check here if we have enough base for all grids tagged as sell
            if (total_sell_q < self.gbot.start_base):
                logger.info("There is enough extra base: %f, which is about %f quote. Sell some base." % (start_base - total_sell_q, (start_base - total_sell_q)*start_ticker))
                ## Sell base for more quote
                extra_q = need_quote
                #This is the amount of base we need to meet the quote requirement
                extra_b = -need_quote/self.gbot.start_ticker
                logger.info("**Sell some base (%f)**" % extra_b)
                #This exit should only matter if we are live, in the future we can do a market sell
                #exit()
            else:
                # There is NOT enough, stop
                logger.info("There is NOT enough base! %f base" % ((self.gbot.start_base - total_sell_q)*self.gbot.start_ticker))
                exit()
        else:
            #Plenty of base currency available
            logger.info("There is enough base, in fact some extra: %f base" % (self.gbot.start_quote - total_buy_b))
            ### Check here if we have enough quote
            if (total_sell_q > self.gbot.start_base):
                # Not enough quote
                need_base = total_sell_q - self.gbot.start_base
                logger.info("but, Need: %f base, about %f quote" %(need_base, (total_sell_q - self.gbot.start_base)*self.gbot.start_ticker))
                if ((self.gbot.start_quote - total_buy_b) > (total_sell_q - self.gbot.start_base)*self.gbot.start_ticker):
                    # Buy more base
                    extra_b = need_base
                    extra_q = -need_base*self.gbot.start_ticker
                    logger.info("**Buy some base (%f)**" % extra_b)
                    #This exit should only matter if we are live, in the future we can do a market buy
                    #exit()
                else:
                    # There is NOT enough, stop
                    logger.info("NOT enough base to make up for quote shortage!")
                    exit()
            else:
                # OK, do nothing. Plenty of quote too
                logger.info("Extra: %f quote, about %f base" % (self.gbot.start_base - total_sell_q,  (self.gbot.start_base - total_sell_q)*self.gbot.start_ticker))
            
        self.gbot.quote_balance = extra_q + self.gbot.start_quote - total_buy_b
        self.gbot.base_balance = extra_b + self.gbot.start_base - total_sell_q
        logger.info("base_balance %.8f quote_balance %.2f" % (self.gbot.base_balance, self.gbot.quote_balance))
        self.gbot.grid = jsonpickle.encode(self.grid_array)
        self.gbot.original_grid = self.gbot.grid
        ##TODO
        #self.start_timestamp = NumberAttribute(null=True)
        #self.start = UnicodeAttribute(null=True)
        #self.last_timestamp = NumberAttribute(null=True)
        #self.last = UnicodeAttribute(null=True)
        
        #exit()
    
    def totals(self):
        total_b = self.gbot.base_balance
        total_q = self.gbot.quote_balance
    
        for g in self.grid_array:
            logger.info(">%d %s %.2f (%.2f) <%d/%d> buybase %.8f sellbase %.8f [take %.2f/%.2f] %.2f %s" % (g.step, g.mode, g.ticker, g.quote_step, 
                                    g.buy_count, g.sell_count, g.buy_base_quantity, g.sell_quote_quantity, g.take, g.step_take, g.sell_base_quantity, g.ex_orderid))
            if g.mode == 'buy':
                # add up the quote
                total_q += g.quote_step
            elif g.mode == 'sell':
                # add up the base
                total_b += g.sell_quote_quantity
        
        logger.info("Total Quote: %.2f Total Base: %.8f @ %.2f (%.2f) = %.2f" % (total_q, total_b, self.gbot.last_ticker, (total_b*self.gbot.last_ticker), 
                                                                            total_q + (total_b*self.gbot.last_ticker)))
        logger.info("Transactions %d (fees: %.2f) Profit %.2f/%.2f" % (self.gbot.transactions, self.gbot.total_fees, self.gbot.profit, self.gbot.step_profit))
