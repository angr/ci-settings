#!/bin/bash -ex

BASEDIR=$(dirname $(dirname $0))
SCRIPTS=$BASEDIR/scripts
CONF=$BASEDIR/conf

tar -xf build.tar.gz
cd build

source virtualenv/bin/activate

python ../tests/lint.py
