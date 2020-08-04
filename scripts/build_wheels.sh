set -ex

# Apple doesn't incluide realpath
function realpath() {
    [[ "$1" = /* ]] && echo "$1" || echo "$PWD/${1#./}"
}

python="$1"
sdist_path="$(realpath "$2")"
venv_path="$(realpath "$3")"

packages=$($python scripts/get_repo_names.py --python-only)
source "$venv_path/bin/activate" &> /dev/null || source "$venv_path/Scripts/activate"

wheels=$(realpath wheels)
mkdir -p "$wheels" wheels_build
pushd wheels_build

for f in $(ls "$sdist_path"); do
    tar -xf "$sdist_path/$f"
done

for package in $packages; do
    pushd "$package"-[0-9]*
    python setup.py bdist_wheel
    mv dist/* "$wheels"
    popd
done

popd
