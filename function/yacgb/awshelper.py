import boto3
import os
from base64 import b64decode
from ssm_cache import SSMParameterGroup
import logging

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
    if s.lower() in ['true', '1', 'y', 'yes']:
        return (True)
    else:
        return (False)


class yacgb_aws_ps:
    bp='yacgb'
    env=None
    configgrp=None
    exch={}
    exch_apikey={}
    exch_secret={}
    market_list=[]
    gbotids=[]
    
    def __init__(self, env=None):
        if env == None:
            env = os.environ.get('AWS_PS_GROUP')
            if env == None:
                env = 'prod' #default to prod
            else:
                logger.info("AWS_PS_GROUP found in ENV, using:" + env)
        self.env=env
        ex = os.environ.get('EXCHANGE')
        mktsym = os.environ.get('MARKET_SYMBOL')
        if ex != None and mktsym != None:
            logger.info("EXCHANGE and MARKET_SYMBOL found in ENV, ignoring AWS Parameter Store")
            self.exch[ex] = [mktsym]
            self.exch_apikey[ex] = os.environ.get('API_KEY')
            self.exch_secret[ex] = os.environ.get('SECRET')
            self.__build_market_list()
            gbotid = os.environ.get('GBOTID')
            if gbotid != None:
                self.gbotids.append(gbotid)
        else:
            self.collect()
       
    def __build_market_list(self):
        for e in self.exch.keys():
            for m in self.exch[e]:
                self.market_list.append(e+':'+m)
        
        
    def collect(self):
        self.configgrp = SSMParameterGroup(base_path='/'+self.bp+'/'+self.env)
        try:
            self.gbotids = self.configgrp.parameter('/gbotids').value
        except:
            self.gbotids.append('not_set')
        
        exchanges= self.configgrp.parameters('/exchanges', recursive=False)
        for e in exchanges:
            if better_bool(e.value):
                exch_name = e.name.rsplit('/',1)[1]
                mkts = self.configgrp.parameter('/exchanges/'+exch_name+'/markets')
                try:
                    self.exch[exch_name] = mkts.value
                except:
                    self.exch[exch_name] = []
                try:
                    self.exch_apikey[exch_name] = self.configgrp.parameter('/exchanges/'+exch_name+'/apikey').value
                    self.exch_secret[exch_name] = self.configgrp.parameter('/exchanges/'+exch_name+'/secret').value
                except:
                    self.exch_apikey[exch_name] = 'not_set'
                    self.exch_secret[exch_name] = 'not_set'
        self.__build_market_list()



