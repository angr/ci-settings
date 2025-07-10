#!/bin/bash
set -ex

source $(dirname $0)/vars.sh

python="$1"
dist_path="$2"
venv_path="$3"

"$python" -m venv "$venv_path"
source "$venv_path/bin/activate" &> /dev/null || source "$venv_path/Scripts/activate"
python -m pip install --upgrade pip wheel

export PIP_FIND_LINKS="$dist_path"
python -m pip install "$dist_path"/*
