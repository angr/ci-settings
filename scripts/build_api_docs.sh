set -ex

python=python
source $(dirname $0)/vars.sh

source angr_venv/bin/activate
pip install -r etc/doc_requirements.txt

starting_dir="$(pwd)"

mkdir -p $CHECKOUT_DIR
pushd $CHECKOUT_DIR

git clone git@github.com:angr/angr-doc.git angr-doc

# In a real deployment, checkout the correct version
# This is not doable in other conditions because we don't push to github
angr_doc_rev="$(cat $starting_dir/release.yml | grep angr-doc | cut -d ' ' -f2)"
if [ "$DRY_RUN" == "false" ]; then
    git -C angr-doc reset --hard $angr_doc_rev
fi
angr_doc_version=$(sed -n -e "s/.*version = u'\(.\+\)'.*/\1/p" angr-doc/api-doc/source/conf.py)

# Congifure path for sphinx
modules="$(cd angr-doc/api-doc/source; ls *.rst | sed -r "s/\.rst//g; s/(\s|^)index(\s|$)//g")"
for module in $modules; do
    module_path=$($python -c "import os; import $module; print(os.path.realpath(os.path.join(os.path.dirname($module.__file__), '..')))")
    export PATH="$module_path:$PATH"
done

# Build docs
make -C angr-doc/api-doc html

popd
