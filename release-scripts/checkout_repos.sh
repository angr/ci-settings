#!/bin/bash
set -e

mkdir -p "repos"
echo "!.git" > repos/.artifactignore

for r in $REPOS; do
    git clone git@github.com:angr/$r.git $CHECKOUT_DIR/$r --depth=1 --recursive
done
