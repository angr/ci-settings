#!/bin/bash -ex

BASEDIR=$(dirname $(dirname $0))
SCRIPTS=$BASEDIR/scripts
CONF=$BASEDIR/conf


tar -I zstd -xf build.tar.zst
source build/virtualenv/bin/activate
uv pip install "pylint>=2.14.0"

cd build/src/${GITHUB_REPOSITORY##*/}

python $SCRIPTS/lint.py
