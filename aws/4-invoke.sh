#!/bin/bash
set -eo pipefail

if [ -z "$2" ]; then
    echo "Parameters missing"
    echo "Usage: $0 <synctickers|backtest|liveinit|liverun> <event.json>"
    exit 1
fi

if [[ "$1" != "synctickers" && "$1" != "backtest" && "$1" != "liveinit"  && "$1" != "liverun" ]]; then
    echo "Unknown function name: $1"
    echo "Usage: $0 <synctickers|backtest|liveinit|liverun> <event.json>"
    exit 1
fi

FUNCTION=$(aws cloudformation describe-stack-resource --stack-name yacgb --logical-resource-id $1 --query 'StackResourceDetail.PhysicalResourceId' --output text)

#This assumes aws-cli v2
aws lambda invoke --function-name $FUNCTION --payload fileb://$2 invoke-out.json --log-type Tail --query 'LogResult' --output text |  base64 -d
#aws-cli v1 (not tested)
#aws lambda invoke --function-name $FUNCTION --payload file://$2 invoke-out.json --log-type Tail --query 'LogResult' --output text
echo ""
cat invoke-out.json
echo ""
#sed -i'' -e 's/"//g' invoke-out.json
#sleep 15
#aws logs get-log-events --log-group-name /aws/lambda/$1 --log-stream-name $(cat invoke-out.json) --limit 5
