#!/bin/bash -ex

BASEDIR=$(dirname $(dirname $0))
SCRIPTS=$BASEDIR/scripts

tar -I zstd -xf build.tar.zst
cd build

source virtualenv/bin/activate
uv pip install pyright

cd src/${GITHUB_REPOSITORY##*/}
HEAD_REV="$(git rev-parse HEAD)"
if [[ $GITHUB_REF == "master" ]]; then
    BASE_REV="$(git rev-parse --abbrev-ref HEAD~)"
else
    BASE_REV="$(git rev-parse --abbrev-ref master)"
fi

python $SCRIPTS/typecheck.py $BASE_REV $HEAD_REV
