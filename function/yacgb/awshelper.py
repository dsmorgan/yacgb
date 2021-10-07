## https://github.com/dsmorgan/yacgb

import boto3
import os
from base64 import b64decode
from ssm_cache import SSMParameterGroup
import logging
import random

logger = logging.getLogger(__name__)

def decrypt_environ(enc_environ):
    e = os.environ[enc_environ]
    # Decrypt code should run once and variables stored outside of the function
    # handler so that these are decrypted once per container
    de = boto3.client('kms').decrypt(
    CiphertextBlob=b64decode(e),
    EncryptionContext={'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME']})['Plaintext'].decode('utf-8')
    logger.info("Decrypted via KMS: " + enc_environ)
    return(de)
    
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


class yacgb_aws_ps:
    def __init__(self, env=None, with_decryption=True):
        self.bp='yacgb'
        self.with_decryption=with_decryption
        self.configgrp=None
        self.exch={}
        self.exch_apikey={}
        self.exch_secret={}
        self.exch_password={}
        self.exch_sandbox={}
        self.exch_config={}
        self.market_list=[]
        self.gbotids=[]
        self.ps = True
        self.init = False
        self.new_exch=[]
        self.del_exch=[]
        
        if env == None:
            env = os.environ.get('AWS_PS_GROUP')
            if env == None:
                env = 'prod' #default to prod
            else:
                logger.info("AWS_PS_GROUP found in environ, using:" + env)
        self.env=env
        
        ex = os.environ.get('EXCHANGE')
        mktsym = os.environ.get('MARKET_SYMBOL')
        if ex != None and mktsym != None:
            self.ps = False
            logger.info("EXCHANGE and MARKET_SYMBOL found in environ, ignoring AWS Parameter Store")
            self.exch[ex] = [mktsym]
            self.exch_apikey[ex] = os.environ.get('API_KEY')
            self.exch_secret[ex] = os.environ.get('SECRET')
            self.exch_password[ex] = os.environ.get('PASSWORD')
            self.exch_sandbox[ex] = better_bool(os.environ.get('SANDBOX', "False"))
            if self.exch_sandbox[ex] == True:
                logger.warning("Using Sandbox Mode for exchange: %s" % ex)
            #self.__build_market_list()
            gbotid = os.environ.get('GBOTID')
            if gbotid != None:
                self.gbotids.append(gbotid)
        #collect from AWS Parameter Store
        self.collect()
       
    def __build_market_list(self):
        self.market_list=[]
        for e in self.exch.keys():
            for m in self.exch[e]:
                self.market_list.append(e+':'+m)
        random.shuffle(self.market_list)
    
    @property
    def shuffled_gbotids(self):
        if self.ps == False:
            return self.gbotids
        try:
            self.gbotids = self.configgrp.parameter('/gbotids').value
        except:
            self.gbotids = []
            self.gbotids.append('not_set')
        random.shuffle(self.gbotids)
        return(self.gbotids)
        
    def collect(self):
        if self.ps:
            prev_exch=set([*self.exch])
            changed = []
            if not self.init:
                self.configgrp = SSMParameterGroup(base_path='/'+self.bp+'/'+self.env, 
                            max_age=int(os.environ.get('AWS_PS_MAX_AGE', 600)), 
                            with_decryption=self.with_decryption)
            try:
                self.gbotids = self.configgrp.parameter('/gbotids').value
            except:
                self.gbotids = []
                self.gbotids.append('not_set')
            
            exchanges= self.configgrp.parameters('/exchanges', recursive=False)
            for e in exchanges:
                exch_name = e.name.rsplit('/',1)[1]
                if better_bool(e.value):
                    self.exch[exch_name] = []
                    self.exch_apikey[exch_name] = 'not_set'
                    self.exch_secret[exch_name] = 'not_set'
                    #Most exchanges don't use password (or passphrase), but at least one (coinbasepro) requires it AND apikey + secret
                    self.exch_password[exch_name] = None
                    self.exch_sandbox[exch_name] = False
                    params = self.configgrp.parameters('/exchanges/' + exch_name, recursive=False)
                    for p in params:
                        pname = p.name.rsplit('/',1)[1]
                        if pname == 'markets':
                            self.exch[exch_name] = p.value
                        if pname == 'apikey':
                            self.exch_apikey[exch_name] = p.value
                        if pname == 'secret':
                            self.exch_secret[exch_name] = p.value
                        if pname == 'password':
                            self.exch_password[exch_name] = p.value
                        if pname == 'sandbox':
                            self.exch_sandbox[exch_name] = better_bool(p.value)
                    if self.exch_sandbox[exch_name] == True:      
                        logger.warning("Using Sandbox Mode for exchange: %s" % exch_name)
                    config = str(self.exch_apikey[exch_name]) + str(self.exch_secret[exch_name]) + str(self.exch_password[exch_name]) + str(self.exch_sandbox[exch_name])
                    if self.exch_config.get(exch_name) != None:
                        if config != self.exch_config[exch_name]:
                            logger.info("Exchange %s config change detected" % exch_name)
                            changed.append(exch_name)
                            self.exch_config[exch_name] = config
                    else:
                       self.exch_config[exch_name] = config 
                else:
                    #delete the exchange, if it is set to False
                    if self.exch.get(exch_name) != None: del(self.exch[exch_name])
            if self.init:
                now_exch = set([*self.exch])
                self.new_exch=list(now_exch - prev_exch)
                self.new_exch.extend(changed)
                self.del_exch=list(prev_exch - now_exch)
                self.del_exch.extend(changed)
            else:
                self.init = True
        self.__build_market_list()