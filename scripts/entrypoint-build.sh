#!/bin/bash -ex

if [ -z "$1" -o -z "$2" -o -z "$3" ]; then
    set +x
    echo "Usage: run-process.sh [build id] [repo name] [ref]"
    exit 1
fi

BUILD_ID=$1
REPO_NAME=$2
REF=$3

# generate requirements.txt and install.sh
resolve_refs.py /conf ./ $REPO_NAME $REF

# perform clones and installs
./install.sh

# testcase discovery
source virtualenv/bin/activate
grep '^def test_' ./src/*/tests/test_*.py | sed 's/def //' | cut -d '(' -f 1 | filter-tests.py --eval-attribute 'speed != "slow"' > tests.txt

# push installation to cloud
publish-build.sh $BUILD_ID
