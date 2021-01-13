set -ex

python="$1"
dist_path="$2"
venv_path="$3"

"$python" -m venv "$venv_path"
source "$venv_path/bin/activate" &> /dev/null || source "$venv_path/Scripts/activate"
python -m pip install --upgrade pip wheel
python -m pip install $dist_path/*
