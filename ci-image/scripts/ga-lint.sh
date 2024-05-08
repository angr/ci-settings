#!/bin/bash -ex

BASEDIR=$(dirname $(dirname $0))
SCRIPTS=$BASEDIR/scripts
CONF=$BASEDIR/conf

if [ ! -z "$GITHUB_REPOSITORY" ]; then
    export BUILD_REPOSITORY_URI=$GITHUB_REPOSITORY
    export BUILD_SOURCEBRANCH=$GITHUB_REF
fi

tar -I zstd -xf build.tar.zst
cd build

source virtualenv/bin/activate

python $SCRIPTS/lint.py
