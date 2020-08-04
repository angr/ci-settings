set -ex

python="$1"
sdist_path="$2"
venv_path="$3"

packages="$("$python" scripts/get_repo_names.py --python-only | sed -E "s#[_-]#*#g; s#([^[:space:]]+)#$sdist_path/\1-[0-9]*#g")"
"$python" -m venv "$venv_path"
source "$venv_path/bin/activate" &> /dev/null || source "$venv_path/Scripts/activate"
python -m pip install --upgrade pip wheel
python -m pip install $packages
