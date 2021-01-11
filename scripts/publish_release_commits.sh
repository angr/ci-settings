#!/bin/bash
set -ex

python=python
source "$(dirname "$0")/vars.sh"

for i in $REPOS; do
    if [ "$DRY_RUN" == "false" ]; then
        git -C $CEHCKOUT_DIR/$i push origin "v$VERSION"
    fi
done
