#!/bin/bash
set -ex

BASEDIR=$(dirname $(dirname $0))
SCRIPTS=$BASEDIR/scripts
CONF=$BASEDIR/conf

git config --global url.https://github.com/.insteadOf git@github.com:


mkdir build
pushd build

$SCRIPTS/resolve_refs.py $CONF . $GITHUB_REPOSITORY $GITHUB_REF
echo "snapshot_branch=$(cat ./snapshot_branch.txt)" >> "${GITHUB_OUTPUT:-/dev/null}"

uv venv ./virtualenv --relocatable
source ./virtualenv/bin/activate

uv pip install --no-cache --requirement /root/conf/requirements.txt

venv_install() {
    uv pip install --no-sources "$@"
}

venv_install ./src/archinfo
uv build ./src/pyvex  # angr will need the wheel
venv_install ./src/pyvex
venv_install ./src/claripy
venv_install ./src/cle
venv_install -f ./src/pyvex/dist ./src/angr[angrdb,llm,unicorn]
venv_install ./src/angr-platforms
venv_install ./src/pysoot
venv_install ./src/tracer
venv_install ./src/archr[qtrace]
venv_install ./src/angr-management
venv_install ./src/angrop
venv_install ./src/phuzzer
venv_install ./src/povsim
venv_install -e ./src/compilerex --config-settings editable_mode=compat
venv_install ./src/patcherex
venv_install ./src/heaphopper
venv_install ./src/driller
venv_install ./src/rex
venv_install ./src/colorguard


# discover corpus tests
IFS=';' CORPUS_TEST_PATHS_LIST=( ${CORPUS_TEST_PATHS-decompiler_corpus} )
(cd ./src/binaries && find "${CORPUS_TEST_PATHS_LIST[@]}" -xtype f | sort -u) >corpus-tests.txt

popd

# remove some unneeded files to reduce bloat
find build \( \
	-type d -and \( \
		\( -name .git -and -not \( \
		    -wholename "*/$(echo $GITHUB_REPOSITORY | cut -d"/" -f2)/.git" \
		    -or -wholename "*/dec-snapshots/.git" \
		\) \) \
		-or -name __pycache__ \
		-or -name "*.egg-info" \
		-or \( -wholename "*/sphinx/locale/*" -and -not -name LC_MESSAGES \) \
		-or \( -wholename "build/virtualenv/*" -and -name tests \) \
		-or -wholename "*/angr/build" \
		-or -wholename "*/angr/target" \
		-or -wholename "*/pyvex/build" \
	\) \
	-or -type f -and \( \
		-wholename "build/virtualenv/*" -and \( \
			-name "*.dylib" \
			-or -name libunicorn.a \
			-or -name libcapstone.a \
			-or -wholename "*/babel/locale-data/*" \
			-or -wholename "*/bin/z3" \
		\) \
		-or -wholename "build/src/pyvex/*.a" \
		-or -wholename "build/src/pyvex/*.o" \
	\) \
\) -exec rm -rf {} +

# export
tar -I zstd -cf build.tar.zst build/src build/virtualenv build/corpus-tests.txt
