#!/bin/bash -ex

BASEDIR=$(dirname $(dirname $0))
SCRIPTS=$BASEDIR/scripts
CONF=$BASEDIR/conf

cd build
cp $CONF/nose2.cfg .

cat tests.txt | awk "NR % $NUM_WORKERS == $WORKER" > todo.txt
source virtualenv/bin/activate
if [ "$1" == "nightly" ]; then
    $SCRIPTS/test.py --tests todo.txt --coverage
else
    $SCRIPTS/test.py --tests todo.txt
fi
