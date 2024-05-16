#!/bin/bash
set -ex

source $(dirname $0)/vars.sh

mkdir sdist

python -m pip install build

export PIP_FIND_LINKS="sdist"
for i in $REPOS $REPOS_LINUX_ONLY; do
    if [ -e "$CHECKOUT_DIR/$i/pyproject.toml" ]; then
        python -m build --sdist --outdir=sdist $CHECKOUT_DIR/$i
    else
        echo "Skipping $i"
    fi
done
