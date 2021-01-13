#!/bin/bash
set -ex

source "$(dirname "$0")/vars.sh"

OUTPUT=release.yml

for i in $REPOS; do
    echo "$i: $(git -C "$CHECKOUT_DIR/$i" rev-parse HEAD)" >> "$OUTPUT"
done
