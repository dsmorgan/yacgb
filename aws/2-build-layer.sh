#!/bin/bash
set -eo pipefail
rm -rf ../package
cd ../function
#pip3.8 install --target ../package/python -r requirements.txt
pip3 install --target ../package/python -r requirements.txt
