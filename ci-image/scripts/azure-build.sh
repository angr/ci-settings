#!/bin/bash -ex

BASEDIR=$(dirname $(dirname $0))
SCRIPTS=$BASEDIR/scripts
CONF=$BASEDIR/conf
WHEELS=$BASEDIR/wheels

if [ ! -z "$GITHUB_REPOSITORY" ]; then
    export BUILD_REPOSITORY_URI=$GITHUB_REPOSITORY
    export BUILD_SOURCEBRANCH=$GITHUB_REF
fi

git config --global url.https://github.com/.insteadOf git@github.com:

export CI_DIRECTIVES=$($SCRIPTS/read_directives.py)

mkdir build
cd build
$SCRIPTS/resolve_refs.py $CONF . $BUILD_REPOSITORY_URI $BUILD_SOURCEBRANCH
./install.sh

source virtualenv/bin/activate
if [ "$1" == "nightly" ] || [ "$NIGHTLY" == "true" ]; then
    $SCRIPTS/discover_tests.py --repo $BUILD_REPOSITORY_URI --config $CONF --src ./src --skip-dependents > tests.txt
elif [[ "$CI_DIRECTIVES" =~ "include-nightly" ]]; then
    $SCRIPTS/discover_tests.py --repo $BUILD_REPOSITORY_URI --config $CONF --src ./src > tests.txt
else
    $SCRIPTS/discover_tests.py --repo $BUILD_REPOSITORY_URI --config $CONF --src ./src --eval-attribute 'speed != "slow"' > tests.txt
fi
cd ..

# remove some unneeded files to reduce bloat
rm -rf build/src/angr/.eggs build/src/vex/priv/*.o build/src/vex/libvex.a build/src/pyvex/pyvex_c/*.o build/src/pyvex/.eggs build/virtualenv/lib/python3.6/lib/site-packages/unicorn/lib/libunicorn.a build/virtualenv/lib/python3.6/lib/site-packages/babel/locale-data build/virtualenv/lib/python3.6/bin/z3 build/src/binaries/.git **/__pycache__

# export
tar -czf build.tar.gz build/src build/virtualenv build/tests.txt
