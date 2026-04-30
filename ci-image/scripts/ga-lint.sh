#!/bin/bash -ex

BASEDIR=$(dirname $(dirname $0))
SCRIPTS=$BASEDIR/scripts
CONF=$BASEDIR/conf


tar -I zstd -xf build.tar.zst
cd build

source virtualenv/bin/activate
uv pip install "pylint>=2.14.0"

python $SCRIPTS/lint.py
