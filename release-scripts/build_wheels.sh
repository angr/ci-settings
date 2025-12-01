set -ex

# Apple doesn't include realpath
function realpath() {
    [[ "$1" = /* ]] && echo "$1" || echo "$PWD/${1#./}"
}

sdist_path="$(realpath "$1")"

python -m pip install build cibuildwheel==3.0.1
if [ "$(uname)" == "Linux" ]; then
    pip install auditwheel
elif [ "$(uname)" == "Darwin" ]; then
    pip install delocate
fi

wheels=$(realpath wheels)
mkdir -p "$wheels" wheels_build
pushd wheels_build

for f in $(ls "$sdist_path"); do
    tar -xf "$sdist_path/$f"
done

export CIBW_BEFORE_ALL_LINUX="curl -sSf https://sh.rustup.rs | sh -s -- -y"
export CIBW_BEFORE_ALL_WINDOWS="rustup toolchain install stable-x86_64-pc-windows-msvc && rustup default stable-x86_64-pc-windows-msvc && del \"C:\\Program Files\\Git\\usr\\bin\\link.exe\""
export PIP_FIND_LINKS="$sdist_path"
export CIBW_ENVIRONMENT_LINUX="PATH=\$PATH:\$HOME/.cargo/bin PIP_FIND_LINKS=/host$PIP_FIND_LINKS"
export CIBW_BUILD="
    cp310-manylinux_x86_64
    cp310-manylinux_aarch64
    cp310-win_amd64
    cp310-macosx_x86_64
    cp310-macosx_arm64
    "
export CIBW_ARCHS_WINDOWS="AMD64"
export CIBW_ARCHS_LINUX="native"
export CIBW_REPAIR_WHEEL_COMMAND_LINUX="auditwheel repair --exclude libpyvex.so -w {dest_dir} {wheel}"
export CIBW_REPAIR_WHEEL_COMMAND_MACOS="delocate-wheel --require-archs {delocate_archs} --ignore-missing-dependencies -w {dest_dir} -v {wheel}"
export MACOSX_DEPLOYMENT_TARGET="10.12"
for dist in $(ls); do
    package=$(cat $dist/PKG-INFO | grep '^Name: [a-zA-Z0-9-]\+$' | head -n 1 | cut -d' ' -f2)
    if [ "$package" = "pyvex" ] || [ "$package" = "angr" ]; then
        python -m cibuildwheel --output-dir "$wheels" $dist
    elif [ "$(uname)" == "Linux" ]; then
        python -m build --wheel --outdir "$wheels" $dist
    fi
done

popd
