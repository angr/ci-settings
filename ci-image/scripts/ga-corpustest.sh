#!/bin/bash -ex

BASEDIR=$(dirname $(dirname $0))
SCRIPTS=$BASEDIR/scripts
CONF=$BASEDIR/conf


tar -I zstd -xf build.tar.zst
cd build

cat corpus-tests.txt | awk "NR % $NUM_WORKERS == $WORKER" > todo.txt
source virtualenv/bin/activate

ln -sf $PWD/src/dec-snapshots $PWD/src/angr/corpus_tests/snapshots
pytest --insta=update $PWD/src/angr/corpus_tests/test_corpus.py --binaries $(cat todo.txt)

mkdir -p results
git -C $PWD/src/angr/corpus_tests/snapshots diff >results/$WORKER.diff
