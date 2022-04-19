#!/bin/bash
set -ex

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $SCRIPT_DIR/vars.sh

for i in $(ls $CHECKOUT_DIR); do
    pushd "$CHECKOUT_DIR/$i"

    if [ -f "$i/VERSION" ]; then
        python $SCRIPT_DIR/versiontool.py bumpmicro <<< "$i/VERSION" > "$i/VERSION"
        VERSION=$(cat VERSION)

    elif [ -e pyproject.toml ]; then
        # Replace version in __init__.py
        project_name=$(sed -n 's/-//g' <<< "$i")
        init_file=$project_name/__init__.py
        old_version =$(cat $init_file | grep '__version__' | cut -d'"' -f2)
        VERSION=$(python $SCRIPT_DIR/versiontool.py bumpmicro "$old_version")
        sed -i "s/$old_version/$VERSION/g" $init_file

    else
        popd
        continue
    fi

    # Commit
    git add --all
    git commit -m "Update version to $VERSION [ci skip]"

    # Push
    if [ "$DRY_RUN" == "false" ]; then
        git push
        push_successful=$?
        if [ $push_successful -neq 0 ]; then
            git pull --rebase
            git push
            push_2_successful=$?
            if [ $push_2_successful -neq 0 ]; then
                git checkout -b bump/$VERSION
                git push origin bump/$VERSION
                gh pr create \
                    --project angr/$CHECKOUT_DIR \
                    --assignees "@twizmwazin" \
                    --title "Bump version to $VERSION" \
                    --body "Release pipeline failed to automatically push commit" \
                    --head "bump/$VERSION" \
                    --base "master"
            fi
        fi
    fi

    popd
done
