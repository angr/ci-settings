set -ex

python=python
source $(dirname $0)/vars.sh

source angr_venv/bin/activate
pip install -r etc/doc_requirements.txt

mkdir -p $CHECKOUT_DIR
pushd $CHECKOUT_DIR

git clone git@github.com:angr/angr-doc.git angr-doc
git clone git@github.com:angr/angr.github.io.git angr.github.io

# In a real deployment, checkout the correct version
# This is not doable in other conditions because we don't push to github
angr_doc_rev="$(cat release.yml/release.yml | grep angr-doc | cut -d ' ' -f2)"
if [ "$DRY_RUN" == "false" ]; then
    git -C angr-doc fetch $angr_doc_rev
    git -C angr-doc reset --hard $angr_doc_rev
fi
angr_doc_version=$(sed -n -e "s/.*version = u'\(.\+\)'.*/\1/p" angr-doc/api-doc/source/conf.py)

# Congifure path for sphinx
modules="$(cd angr-doc/api-doc/source; ls *.rst | sed -r "s/\.rst//g; s/(\s|^)index(\s|$)//g")"
for module in $modules; do
    module_path=$($python -c "import os; import $module; print(os.path.realpath(os.path.join(os.path.dirname($module.__file__), '..')))")
    export PATH="$module_path:$PATH"
done

# Build docs and copy to website
make -C angr-doc/api-doc html
rm -rf angr.github.io/api-doc
cp -r angr-doc/api-doc/build/html angr.github.io/api-doc

# Push to website
pushd angr.github.io
git commit --author "angr release bot <angr-dev@asu.edu>" -m "update api-docs for version $angr_doc_version" api-doc
if [ "$DRY_RUN" == "false" ]; then
    git push origin master
fi
popd
popd
