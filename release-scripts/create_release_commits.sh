#!/bin/bash
set -ex

pip install packaging

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# ---------------------------------------------------------------------------
# angr-data carries the same version as angr (its __version__ is kept in lockstep
# with the shared version line by bump_versions.sh), but it is only re-published
# when one of its bundled .json data files has changed since its last release.
# When nothing changed we reuse the most recently released angr-data version and
# do not build/publish a new one. So `undev` of angr-data's current version
# yields the current angr release version. Either way, angr is pinned to the
# resolved angr-data version below.
# ---------------------------------------------------------------------------
ANGR_DATA_VERSION=""
ANGR_DATA_RELEASED=false
ANGR_DATA_DIR="$CHECKOUT_DIR/angr-data"
if [ -d "$ANGR_DATA_DIR" ]; then
    pushd "$ANGR_DATA_DIR"

    # We need full history + tags to diff against the last release (the repo is
    # cloned shallow by the workflow).
    git fetch --tags --quiet
    git fetch --unshallow --quiet 2>/dev/null || true

    init_file=angr_data/__init__.py
    old_version=$(grep '__version__' $init_file | head -n 1 | cut -d'"' -f2)

    last_tag=$(git tag --list 'v*' --sort=-v:refname | head -n 1)
    if [ -n "$last_tag" ]; then
        changed_json=$(git diff --name-only "$last_tag"..HEAD -- '*.json')
    else
        # No prior release: release for the first time.
        changed_json="initial-release"
    fi

    if [ -n "$changed_json" ]; then
        ANGR_DATA_VERSION=$(python $SCRIPT_DIR/versiontool.py undev "$old_version")
        sed -i "s/$old_version/$ANGR_DATA_VERSION/g" $init_file
        [ -f pyproject.toml ] && sed -i "s/$old_version/$ANGR_DATA_VERSION/g" pyproject.toml

        git checkout -q -b "release/$ANGR_DATA_VERSION"
        git add --all
        git commit -m "Update version to $ANGR_DATA_VERSION"
        git tag -a "v$ANGR_DATA_VERSION" -m "release version $ANGR_DATA_VERSION"
        ANGR_DATA_RELEASED=true
    else
        # No data changed since the last release; reuse it.
        ANGR_DATA_VERSION=${last_tag#v}
        ANGR_DATA_RELEASED=false
    fi

    popd

    # Persist the decision for later steps (same job, via $GITHUB_ENV) and for
    # the publish job (via the uploaded repos artifact).
    {
        echo "ANGR_DATA_VERSION=$ANGR_DATA_VERSION"
        echo "ANGR_DATA_RELEASED=$ANGR_DATA_RELEASED"
    } > "$CHECKOUT_DIR/.release-meta"
    if [ -n "$GITHUB_ENV" ]; then
        cat "$CHECKOUT_DIR/.release-meta" >> "$GITHUB_ENV"
    fi
fi

for i in $(ls $CHECKOUT_DIR); do
    pushd "$CHECKOUT_DIR/$i"

    # angr-data is handled above.
    if [ "$i" == "angr-data" ]; then
        popd
        continue
    fi

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

        # Pin angr to the resolved angr-data version for this release.
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
