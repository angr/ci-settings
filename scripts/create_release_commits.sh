#!/bin/bash
set -ex

source "$(dirname "$0")/vars.sh"

for i in $(ls $CHECKOUT_DIR); do
    pushd "$CHECKOUT_DIR/$i"

    if [[ -e VERSION ]]; then
        sed -i -e "s/\\.gitrolling/.$VERSION_ID/g" VERSION
        VERSION=$(cat VERSION)
    elif [ -e setup.py ]; then
        # Replace version in setup.py
        sed -i -e "s/\\.gitrolling/.$VERSION_ID/g" setup.py
        # Replace version in __init__.py
        sed -i -e "s/\"gitrolling\"/$VERSION_ID/g" ./*/__init__.py

        VERSION=$(sed -n -e "s/.*version='\(.\+\)'.*/\1/p" setup.py)
    elif [ "$i" == "angr-doc" ]; then
        sed -i -e "s/\\.gitrolling/.$VERSION_ID/g" api-doc/source/conf.py
        VERSION=$(sed -n -e "s/.*version = u'\(.\+\)'.*/\1/p" api-doc/source/conf.py)
    else
        popd
        continue
    fi

    # Commit
    git checkout -q -b "release/$VERSION"
    git add --all
    git commit -m "Update version to $VERSION [ci skip]"
    git tag -a "v$VERSION" -m "release version $VERSION"

    popd
done
