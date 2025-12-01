#!/bin/bash
set -ex

mkdir sdist

python -m pip install build

export PIP_FIND_LINKS="sdist"
for i in $REPOS; do
    if [ -e "$CHECKOUT_DIR/$i/pyproject.toml" ]; then
        python -m build --sdist --outdir=sdist $CHECKOUT_DIR/$i
    else
        echo "Skipping $i"
    fi
done
