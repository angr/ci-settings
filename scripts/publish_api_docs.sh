#!/bin/bash
# Update gh-pages branch on the angr-doc repository for
# API doc publishing at https://api.angr.io via GitHub Pages
set -ex

git clone -b gh-pages git@github.com:angr/angr-doc.git
pushd angr-doc

git rm -rf *
cp -r ../apidocs/* .

echo "api.angr.io" > CNAME
touch .nojekyll

git add .
git commit --allow-empty \
           --author "angr release bot <angr-dev@asu.edu>" \
           --message "Update api-docs for version $angr_doc_version"

if [ "$DRY_RUN" == "false" ]; then
    git push -f origin gh-pages:gh-pages
fi
