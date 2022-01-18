#!/bin/bash
set -eo pipefail
STACK=yacgb

if ! command -v sam &> /dev/null; then
    if ! command -v awsv2 &> /dev/null; then
        if ! command -v aws &> /dev/null; then
            echo "no sam or aws cmd found!"
            exit 1
        else
            AWSCMD="aws"
        fi
    else
        AWSCMD="awsv2"
    fi
    
    ARTIFACT_BUCKET=$(cat bucket-name.txt)
    cd ../
    $AWSCMD cloudformation package --template-file aws-template.yml --s3-bucket $ARTIFACT_BUCKET --output-template-file aws/out.yml
    $AWSCMD cloudformation deploy --template-file aws/out.yml --stack-name $STACK --capabilities CAPABILITY_NAMED_IAM
else
  cd ../
  
  if [ -f "samconfig.toml" ]; then
    echo "samconfig.toml already exists..."
    sam deploy
  else 
    echo "samconfig.toml does NOT exist, using guided..."
    sam deploy --stack-name $STACK --guided
  fi
  
fi
