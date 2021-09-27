#!/bin/bash
set -eo pipefail
rm -rf ../package
cd ../yacgb-layer
#pip3.8 install --target ../package/python -r requirements.txt
pip3 install --target ../package/python -r requirements.txt
