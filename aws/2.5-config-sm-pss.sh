#!/bin/bash
set -eo pipefail
ENV=prod

aws ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken" --value "true" --type String --tags "Key=app,Value=yacgb"
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken/markets" --value "LTC/USD,FIL/USD" --type StringList --tags "Key=app,Value=yacgb"
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken/apikey" --value "<APIKEY_HERE>" --type SecureString --tags "Key=app,Value=yacgb"
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken/secret" --value "<SECRET_HERE>" --type SecureString --tags "Key=app,Value=yacgb"

aws ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus" --value "true" --type String --tags "Key=app,Value=yacgb"
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus/markets" --value "XLM/USD,ONE/USD,ADA/USD,ALGO/USD,ATOM/USD,BNB/USD,UNI/USD" --type StringList --tags "Key=app,Value=yacgb"
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus/apikey" --value "<APIKEY_HERE>" --type SecureString --tags "Key=app,Value=yacgb"
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus/secret" --value "<SECRET_HERE>" --type SecureString --tags "Key=app,Value=yacgb"

aws ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro" --value "false" --type String --tags "Key=app,Value=yacgb"
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro/markets" --value "BTC/USD,ETH/USD,LINK/USD,XLM/USD,STORJ/USD" --type StringList --tags "Key=app,Value=yacgb"
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro/apikey" --value "<APIKEY_HERE>" --type SecureString --tags "Key=app,Value=yacgb"
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro/secret" --value "<SECRET_HERE>" --type SecureString --tags "Key=app,Value=yacgb"
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro/password" --value "<PASSPHRASE_HERE>" --type SecureString --tags "Key=app,Value=yacgb"

aws ssm put-parameter --name "/yacgb/$ENV/gbotids" --value "<EDIT_AFTER_LIVEINIT>" --type StringList --tags "Key=app,Value=yacgb"