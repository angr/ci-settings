#!/bin/bash -ex

BASEDIR=$(dirname $(dirname $0))
SCRIPTS=$BASEDIR/scripts
CONF=$BASEDIR/conf


tar -I zstd -xf build.tar.zst
cd build
cp $CONF/nose2.cfg .

# Get the repository name without the owner part
REPO_NAME=$(echo $GITHUB_REPOSITORY | cut -d '/' -f 2)

# Filter tests based on INCLUDE_SELF parameter
if [ "$INCLUDE_SELF" == "false" ]; then
    # Exclude tests for the self repository
    grep -v "^$REPO_NAME " tests.txt > filtered_tests.txt
    mv filtered_tests.txt tests.txt
fi

cat tests.txt | awk "NR % $NUM_WORKERS == $WORKER" > todo.txt
source virtualenv/bin/activate
if [ "$1" == "nightly" ]; then
    $SCRIPTS/test.py --tests todo.txt --coverage
else
    $SCRIPTS/test.py --tests todo.txt
fi
