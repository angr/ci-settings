#!/bin/bash -ex

BASEDIR=$(dirname $(dirname $0))
SCRIPTS=$BASEDIR/scripts
CONF=$BASEDIR/conf
WHEELS=$BASEDIR/wheels


git config --global url.https://github.com/.insteadOf git@github.com:

export CI_DIRECTIVES=$($SCRIPTS/read_directives.py)

pip install "uv~=0.9.30"

mkdir build
pushd build
$SCRIPTS/resolve_refs.py $CONF . $GITHUB_REPOSITORY $GITHUB_REF
echo "snapshot_branch=$(cat ./snapshot_branch.txt)" >> "$GITHUB_OUTPUT"
./install.sh

source virtualenv/bin/activate

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
		-wholename build/virtualenv -and \( \
			-name *.exe \
			-or -name *.dylib \
			-or -name libunicorn.a \
			-or -name libcapstone.a \
			-or -wholename "*/babel/locale-data" \
			-or -wholename "*/bin/z3" \
		\) \
		-or -wholename build/src/pyvex/*.a \
		-or -wholename build/src/pyvex/*.o \
	\) \
\) -exec rm -rf {} +

# export
tar -I zstd -cf build.tar.zst build/src build/virtualenv build/corpus-tests.txt
