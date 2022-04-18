#!/bin/bash
set -ex

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $SCRIPT_DIR/vars.sh

for i in $(ls $CHECKOUT_DIR); do
    pushd "$CHECKOUT_DIR/$i"

    if [ -f "$i/VERSION" ]; then
        python $SCRIPT_DIR/versiontool.py undev <<< "$i/VERSION" > "$i/VERSION"
        VERSION=$(cat VERSION)

    elif [ -e pyproject.toml ]; then
        # Replace version in __init__.py
        project_name=$(sed 's/-//g' <<< "$i")
        init_file=$project_name/__init__.py
        old_version=$(cat $init_file | grep '__version__' | cut -d'"' -f2)
        VERSION=$(python $SCRIPT_DIR/versiontool.py undev "$old_version")
        sed -i "s/$old_version/$VERSION/g" $init_file

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
