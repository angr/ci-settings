#!/bin/bash
set -ex

for i in $(ls $CHECKOUT_DIR); do
    ref_to_push=$(git -C $CHECKOUT_DIR/$i describe --tags | head -n 1)
    if [ "$DRY_RUN" == "false" ]; then
        git -C $CHECKOUT_DIR/$i push origin "$ref_to_push"
    fi
done
