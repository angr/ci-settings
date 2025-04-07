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

# Get the repository name without the owner part
REPO_NAME=$(echo $GITHUB_REPOSITORY | cut -d '/' -f 2)

cat corpus-tests.txt | awk "NR % $NUM_WORKERS == $WORKER" > todo.txt
source virtualenv/bin/activate

ln -sf $PWD/dec-snapshots/snapshots angr/corpus_tests/snapshots
while read -r binary; do
    pytest --insta=update --binary="$binary" angr/corpus_tests/test_corpus.py || true
done <todo.txt

mkdir -p results
git -C dec-snapshots diff >results/$WORKER.diff
