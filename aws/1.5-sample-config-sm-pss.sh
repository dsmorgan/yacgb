#!/bin/bash
set -eo pipefail

if ! command -v awsv2 &> /dev/null; then
    if ! command -v aws &> /dev/null; then
        echo "no aws cmd found"
        exit 1
    else
        AWSCMD="aws"
    fi
else
    AWSCMD="awsv2"
fi

ENV=prod

#global parameter settings
$AWSCMD ssm put-parameter --name "/yacgb/$ENV/gbotids" --value "<EDIT_AFTER_LIVEINIT>" --type StringList --tags "Key=app,Value=yacgb"


##Edit the below to match the configuration needed of exchanges and markets. You can add apikeys, secrets, and passwords manaully 
##  in the console
## The exchange names, markets, and parameter names are defined in the ccxt library
## The value set in the exchange name must be set to "true" in order to be used/available

#sample binanceus
$AWSCMD ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus" --value "true" --type String --tags "Key=app,Value=yacgb"
$AWSCMD ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus/markets" --value "XLM/USD,ONE/USD,ADA/USD,ALGO/USD,ATOM/USD,BNB/USD,UNI/USD" --type StringList --tags "Key=app,Value=yacgb"
$AWSCMD ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus/apikey" --value "<APIKEY_HERE>" --type SecureString --tags "Key=app,Value=yacgb"
$AWSCMD ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus/secret" --value "<SECRET_HERE>" --type SecureString --tags "Key=app,Value=yacgb"

#sample kraken
$AWSCMD ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken" --value "true" --type String --tags "Key=app,Value=yacgb"
$AWSCMD ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken/markets" --value "LTC/USD,FIL/USD" --type StringList --tags "Key=app,Value=yacgb"
$AWSCMD ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken/apikey" --value "<APIKEY_HERE>" --type SecureString --tags "Key=app,Value=yacgb"
$AWSCMD ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken/secret" --value "<SECRET_HERE>" --type SecureString --tags "Key=app,Value=yacgb"

#sample coinbasepro
$AWSCMD ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro" --value "false" --type String --tags "Key=app,Value=yacgb"
$AWSCMD ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro/markets" --value "BTC/USD,ETH/USD,LINK/USD,XLM/USD,STORJ/USD" --type StringList --tags "Key=app,Value=yacgb"
$AWSCMD ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro/apikey" --value "<APIKEY_HERE>" --type SecureString --tags "Key=app,Value=yacgb"
$AWSCMD ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro/secret" --value "<SECRET_HERE>" --type SecureString --tags "Key=app,Value=yacgb"
$AWSCMD ssm put-parameter --name "/yacgb/$ENV/exchanges/coinbasepro/password" --value "<PASSPHRASE_HERE>" --type SecureString --tags "Key=app,Value=yacgb"


echo "You'll need to goto the AWS console to the SSM Parameter Store to complete the configuration of markets, apikeys, secrets and passwords"