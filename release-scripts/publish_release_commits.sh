#!/bin/bash
set -ex

source "$(dirname "$0")/vars.sh"

for i in $(ls $CHECKOUT_DIR); do
    ref_to_push=$(git -C $CHECKOUT_DIR/$i describe --tags | head -n 1)
    git -C $CHECKOUT_DIR/$i remote set-url origin $(git -C $CHECKOUT_DIR/$i remote get-url origin | sed "s#https://#https://$GIT_USERNAME:$GIT_PASSWORD@#")
    if [ "$DRY_RUN" == "false" ]; then
        git -C $CHECKOUT_DIR/$i push origin "$ref_to_push"
    fi
done
