set -ex

source $(dirname $0)/vars.sh

source angr_venv/bin/activate
pip install ${DOC_REQUIREMENTS[@]}

# Congifure path for sphinx
modules="$(cd angr-doc/api-doc/source; ls *.rst | sed -r "s/\.rst//g; s/(\s|^)index(\s|$)//g")"
for module in $modules; do
    module_path=$($python -c "import os; import $module; print(os.path.realpath(os.path.join(os.path.dirname($module.__file__), '..')))")
    export PATH="$module_path:$PATH"
done

# Build docs
make -C repos/angr-doc/api-doc html
cp repos/angr-doc/VERSION angr-doc/api-doc/build/html/
