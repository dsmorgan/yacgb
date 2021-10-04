#!/bin/bash
set -eo pipefail
ENV=test

aws ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken" --value "true" --type String  --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken/markets" --value "LTC/USD,FIL/USD" --type StringList --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken/apikey" --value "testapikey" --type SecureString --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken/secret" --value "testsecret" --type SecureString --overwrite

aws ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus" --value "true" --type String --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus/markets" --value "XLM/USD,ONE/USD,ADA/USD,ALGO/USD,ATOM/USD,BNB/USD,UNI/USD" --type StringList --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus/apikey" --value "testapikey" --type SecureString  --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus/secret" --value "testsecret" --type SecureString  --overwrite

aws ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro" --value "false" --type String  --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro/markets" --value "BTC/USD,ETH/USD,LINK/USD,XLM/USD,STORJ/USD" --type StringList  --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro/apikey" --value "testapikey" --type SecureString  --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro/secret" --value "testsecret" --type SecureString  --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro/password" --value "testpassword" --type SecureString  --overwrite

aws ssm put-parameter --name "/yacgb/$ENV/gbotids" --value "testgbotid" --type StringList  --overwrite

ENV=test2

aws ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken" --value "true" --type String  --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken/markets" --value "LTC/USD" --type StringList  --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken/apikey" --value "testapikey" --type SecureString  --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken/secret" --value "testsecret" --type SecureString --overwrite

aws ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus" --value "true" --type String  --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus/markets" --value "XLM/USD" --type StringList  --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus/apikey" --value "testapikey2" --type SecureString  --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus/secret" --value "testsecret2" --type SecureString --overwrite

aws ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro" --value "true" --type String  --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro/markets" --value "BTC/USD,ETH/USD" --type StringList  --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro/apikey" --value "testapikey" --type SecureString  --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro/secret" --value "testsecret" --type SecureString  --overwrite
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro/password" --value "testpassword" --type SecureString  --overwrite

aws ssm put-parameter --name "/yacgb/$ENV/gbotids" --value "testgbotid" --type StringList  --overwrite