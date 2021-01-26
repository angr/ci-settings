#!/bin/bash

source $(dirname $0)/vars.sh

mkdir -p "repos"
echo "!.git" > repos/.artifactignore

for r in $REPOS $REPOS_LINUX_ONLY; do
    git clone git@github.com:angr/$r.git $CHECKOUT_DIR/$r --depth=1
done
