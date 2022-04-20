set -ex

source $(dirname $0)/vars.sh

# Apple doesn't include realpath
function realpath() {
    [[ "$1" = /* ]] && echo "$1" || echo "$PWD/${1#./}"
}

python="$1"
sdist_path="$(realpath "$2")"

$python -m pip install build cibuildwheel==2.3.1

platform="$($python -c "import distutils.util; print(distutils.util.get_platform())" | sed s'/-/_/g')"
if [ "$(uname)" = "Linux" ]; then
    platform="$(sed 's/linux/manylinux2010/' <<< "$platform")"
fi

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
export CIBW_ENVIRONMENT_LINUX="/host$PIP_FIND_LINKS"
export CIBW_ARCHS=native
for dist in $(ls); do
    package=$(cat $dist/PKG-INFO | grep '^Name: [a-zA-Z0-9-]\+$' | head -n 1 | cut -d' ' -f2)
    if is_native_package "$package"; then
        $python -m cibuildwheel --output-dir "$wheels" $dist
    elif [ "$(uname)" == "Linux" ]; then
        $python -m build --wheel --outdir "$wheels" $dist
    fi
done

popd
