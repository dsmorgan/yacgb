#!/bin/bash
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
else
  sam --version
  echo "sam command available, no need to create s3 buckets manually, skipping"
  exit 0
fi

BUCKET_ID=$(dd if=/dev/random bs=8 count=1 2>/dev/null | od -An -tx1 | tr -d ' \t\n')
BUCKET_NAME=yacgb-$BUCKET_ID
echo $BUCKET_NAME > bucket-name.txt
$AWSCMD s3 mb s3://$BUCKET_NAME
