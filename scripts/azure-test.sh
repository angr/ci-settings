#!/bin/bash -ex

BASEDIR=$(dirname $(dirname $0))
SCRIPTS=$BASEDIR/scripts
CONF=$BASEDIR/conf

tar -xf build.tar.gz
cd build
cp $CONF/nose2.cfg .

cat tests.txt | awk "NR % $NUM_WORKERS == $WORKER" > todo.txt
$SCRIPTS/test.sh todo.txt
mv results
