#!/bin/bash
set -ex

python=python
source "$(dirname "$0")/vars.sh"


for i in $REPOS; do
    pushd "$CHECKOUT_DIR/$i"

    if [ -e setup.py ]; then
        # Replace version in setup.py
        sed -i -e "s/\\.gitrolling/.$VERSION_ID/g" setup.py
        # Replace version in __init__.py
        sed -i -e "s/\"gitrolling\"/$VERSION_ID/g" ./*/__init__.py

        VERSION=$(sed -n -e "s/.*version='\(.\+\)'.*/\1/p" setup.py)
    elif [ "$i" == "angr-doc" ]; then
        sed -i -e "s/\\.gitrolling/.$VERSION_ID/g" api-doc/source/conf.py
        VERSION=$(sed -n -e "s/.*version = u'\(.\+\)'.*/\1/p" api-doc/source/conf.py)
    elif [[ "$i" == "binaries" || "$i" == "vex" ]]; then
        sed -i -e "s/\\.gitrolling/.$VERSION_ID/g" VERSION
        VERSION=$(cat VERSION)
    else
        popd
        continue
    fi

    # Commit and push to github
    git checkout -q -b "release/$VERSION"
    git add --all
    git commit -m "Update version to $VERSION [ci skip]"
    git tag -a "v$VERSION" -m "release version $VERSION"

    if [ "$DRY_RUN" == "false" ]; then
        git push origin "v$VERSION"
    fi

    popd
done
