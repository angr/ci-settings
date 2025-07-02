#!/bin/bash -ex

BASEDIR=$(dirname $(dirname $0))
SCRIPTS=$BASEDIR/scripts
CONF=$BASEDIR/conf


tar -I zstd -xf build.tar.zst
cd build

# Get the repository name without the owner part
REPO_NAME=$(echo $GITHUB_REPOSITORY | cut -d '/' -f 2)

source virtualenv/bin/activate

# If INCLUDE_SELF is not set, default to true
$SCRIPTS/test.py $REPO_NAME ${INCLUDE_SELF:-true}
