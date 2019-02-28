#!/bin/bash -ex

BASEDIR=$(dirname $(dirname $0))
SCRIPTS=$BASEDIR/scripts
CONF=$BASEDIR/conf
WHEELS=$BASEDIR/wheels

cd $WHEELS
git fetch
git reset --hard $(BUILD_SOURCEBRANCHNAME) || true
cd -

mkdir build
cd build
$SCRIPTS/resolve_refs.py $CONF_ROOT $WHEELS . $BUILD_REPOSITORY_URI $BUILD_SOURCEBRANCH
./install.sh

source virtualenv/bin/activate
grep '^def test_' ./src/*/tests/test_*.py | sed 's/def //' | cut -d '(' -f 1 | $SCRIPTS/filter-tests.py --eval-attribute 'speed != "slow"' > tests.txt
cd ..
tar -czf build.tar.gz build/src build/virtualenv build/tests.txt
