set -ex

source $(dirname $0)/vars.sh

# Apple doesn't include realpath
function realpath() {
    [[ "$1" = /* ]] && echo "$1" || echo "$PWD/${1#./}"
}

platform_tag=""
if [ "$(uname)" == "Linux" ]; then
    platform_tag="--plat-name manylinux2010_x86_64"

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

for package in $(ls); do
    pushd "$package"
    python setup.py bdist_wheel $platform_tag
    mv dist/* "$wheels"
    popd
done

popd
