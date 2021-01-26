set -ex

source $(dirname $0)/vars.sh

python="$1"
dist_path="$2"
venv_path="$3"

"$python" -m venv "$venv_path"
source "$venv_path/bin/activate" &> /dev/null || source "$venv_path/Scripts/activate"
python -m pip install --upgrade pip wheel

# Filter out linux-only packages on non-linux
install_list=""
if [ $(uname) == "Linux" ]; then
    install_list="$dist_path/*"
else
    for f in $(ls $dist_path); do
        if ! is_linux_only $f; then
            install_list="$install_list $dist_path/$f"
        fi
    done
fi
python -m pip install $install_list
