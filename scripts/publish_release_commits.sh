#!/bin/bash
set -ex

source "$(dirname "$0")/vars.sh"

for i in $REPOS; do
    if [ "$DRY_RUN" == "false" ]; then
        git -C $CHECKOUT_DIR/$i push origin "v$VERSION"
    fi
done
