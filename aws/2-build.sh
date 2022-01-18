#!/bin/bash
set -eo pipefail

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
  cd ../
  sam build
  exit 0
fi

if ! command -v pip3.8 &> /dev/null; then
    if ! command -v pip3 &> /dev/null; then
        echo "no pip3 cmd found"
        exit 1
    else
        PIPCMD="pip3"
    fi
else
    PIPCMD="pip3.8"
fi

rm -rf ../package
cd ../yacgb-layer
$PIPCMD install --target ../package/python -r requirements.txt
