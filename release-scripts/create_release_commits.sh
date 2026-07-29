#!/bin/bash
set -ex

pip install packaging

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

for i in $(ls $CHECKOUT_DIR); do
    pushd "$CHECKOUT_DIR/$i"

    if [ -f "VERSION" ]; then
        python $SCRIPT_DIR/versiontool.py undev $(cat VERSION) > "VERSION"
        VERSION=$(cat VERSION)

    elif [ -f "$i/VERSION" ]; then
        python $SCRIPT_DIR/versiontool.py undev $(cat $i/VERSION) > "$i/VERSION"
        VERSION=$(cat VERSION)

    elif [ -e pyproject.toml ]; then
        # Replace version in __init__.py
        project_name=$(sed 's/-//g' <<< "$i")
        init_file=$project_name/__init__.py
        old_version=$(cat $init_file | grep '__version__' | head -n 1 | cut -d'"' -f2)
        if [ -n "$RELEASE_VERSION" ]; then
            # Manual version: pin the angr dep to the manual version, other sibling deps to its base (last release)
            VERSION="$RELEASE_VERSION"
            PIN_VERSION=$(python $SCRIPT_DIR/versiontool.py undev "$VERSION")
            sed -i -E "s/\"angr(\[[^]]*\])?==$old_version/\"angr\1==$VERSION/g" pyproject.toml
            sed -i "s/==$old_version/==$PIN_VERSION/g" pyproject.toml
            [ -f setup.cfg ] && sed -i "s/==$old_version/==$PIN_VERSION/g" setup.cfg
            sed -i "s/$old_version/$VERSION/g" $init_file pyproject.toml
        else
            VERSION=$(python $SCRIPT_DIR/versiontool.py undev "$old_version")
            sed -i "s/$old_version/$VERSION/g" $init_file
            sed -i "s/$old_version/$VERSION/g" pyproject.toml
            [ -f setup.cfg ] && sed -i "s/$old_version/$VERSION/g" setup.cfg
        fi

    else
        popd
        continue
    fi

    # Commit
    git checkout -q -b "release/$VERSION"
    git add --all
    git commit -m "Update version to $VERSION"
    git tag -a "v$VERSION" -m "release version $VERSION"

    popd
done
