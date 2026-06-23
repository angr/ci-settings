#!/bin/bash
set -ex

pip install packaging

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# angr-data is released from its own separate pipeline (in the angr-data repo).
# Pin angr to the most recent angr-data version published on PyPI. Empty if it
# has never been published, in which case the existing pin is left untouched.
ANGR_DATA_VERSION=$(python $SCRIPT_DIR/latest_pypi_version.py angr-data)

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
        VERSION=$(python $SCRIPT_DIR/versiontool.py undev "$old_version")
        sed -i "s/$old_version/$VERSION/g" $init_file
        sed -i "s/$old_version/$VERSION/g" pyproject.toml
        [ -f setup.cfg ] && sed -i "s/$old_version/$VERSION/g" setup.cfg

        # Pin angr to the latest published angr-data version.
        if [ "$i" == "angr" ] && [ -n "$ANGR_DATA_VERSION" ]; then
            sed -i -E "s/angr-data~=[0-9][0-9.]*/angr-data~=$ANGR_DATA_VERSION/g" pyproject.toml
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
