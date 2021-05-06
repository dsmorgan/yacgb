#!/bin/bash
set -eo pipefail
ENV=prod

aws ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken" --value "true" --type String
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken/markets" --value "LTC/USD,ETH/USD" --type StringList
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken/apikey" --value "<APIKEY_HERE>" --type String
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/kraken/secret" --value "<SECRET_HERE>" --type SecureString

aws ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus" --value "false" --type String
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus/markets" --value "XLM/USD" --type StringList
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus/apikey" --value "<APIKEY_HERE>" --type String
aws ssm put-parameter --name "/yacgb/$ENV/exchanges/binanceus/secret" --value "<SECRET_HERE>" --type SecureString