#!/bin/bash
set -eo pipefail

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

cd ..
$PIPCMD install -r tests/requirements.txt
$PIPCMD install -r yacgb-layer/requirements.txt
pytest function/tests/unit/
