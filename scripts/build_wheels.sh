set -ex

source $(dirname $0)/vars.sh

# Apple doesn't include realpath
function realpath() {
    [[ "$1" = /* ]] && echo "$1" || echo "$PWD/${1#./}"
}

python="$1"
sdist_path="$(realpath "$2")"
venv_path="$(realpath "$3")"

source "$venv_path/bin/activate" &> /dev/null || source "$venv_path/Scripts/activate"

wheels=$(realpath wheels)
mkdir -p "$wheels" wheels_build
pushd wheels_build

for f in $(ls "$sdist_path"); do
    # Filter out linux-specific on non-linux
    if [ $(uname) == "Linux" ] || ! is_linux_only $f; then
        tar -xf "$sdist_path/$f"
    fi
done

export PIP_FIND_LINKS="$sdist_path"
for dist in $(ls); do
    package=$(cat $dist/PKG-INFO | grep Name | cut -d' ' -f2)
    # Only add platform tag for linux when dist is pyvex or angr
    if [ "$(uname)" == "Linux" ] && is_native_package $package; then
        platform_tag_arg="--platform=manylinux2010_x86_64"
        python -m build --wheel --outdir "$wheels" -C$platform_tag_arg $dist
    else
        python -m build --wheel --outdir "$wheels" $dist
    fi
done

popd
