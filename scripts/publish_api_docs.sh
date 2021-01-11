set -ex

# Clone website repo
git clone git@github.com:angr/angr.github.io.git angr.github.io

# Replace api-doc with new version
rm -rf angr.github.io/api-doc
cp -r apidocs angr.github.io/api-doc

# Push to website
git -C angr.github.io commit api-doc \
    --author "angr release bot <angr-dev@asu.edu>" \
    --message "update api-docs for version $angr_doc_version"

if [ "$DRY_RUN" == "false" ]; then
    git -C angr.github.io push origin master
fi
