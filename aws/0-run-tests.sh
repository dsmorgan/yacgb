#!/bin/bash
set -eo pipefail
cd ..
pip3 install -r tests/requirements.txt
pip3 install -r yacgb-layer/requirements.txt
pytest function/tests/unit/
