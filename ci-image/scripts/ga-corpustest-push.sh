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

cd dec-snapshots
git apply ../results/*.diff

if [[ "$BUILD_SOURCEBRANCH" == "refs/heads/master" ]]; then
    git commit -a -m "Update master corpus snapshot"
    git push
else
    git switch -c "$SNAPSHOT_BRANCH"
    git commit -a -m "Corpus diff vs master for $BUILD_SOURCEBRANCH"
    git push -fu origin "$SNAPSHOT_BRANCH"
fi
