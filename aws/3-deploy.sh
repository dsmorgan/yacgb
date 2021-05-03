#!/bin/bash
set -eo pipefail
ARTIFACT_BUCKET=$(cat bucket-name.txt)
cd ../
aws cloudformation package --template-file template.yml --s3-bucket $ARTIFACT_BUCKET --output-template-file aws/out.yml
aws cloudformation deploy --template-file aws/out.yml --stack-name yacgb --capabilities CAPABILITY_NAMED_IAM
