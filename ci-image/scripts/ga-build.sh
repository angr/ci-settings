#!/bin/bash -ex

BASEDIR=$(dirname $(dirname $0))
SCRIPTS=$BASEDIR/scripts
CONF=$BASEDIR/conf
WHEELS=$BASEDIR/wheels

if [ ! -z "$GITHUB_REPOSITORY" ]; then
    export BUILD_REPOSITORY_URI=$GITHUB_REPOSITORY
    export BUILD_SOURCEBRANCH=$GITHUB_REF
fi

git config --global url.https://github.com/.insteadOf git@github.com:

export CI_DIRECTIVES=$($SCRIPTS/read_directives.py)

pip install uv

mkdir build
cd build
$SCRIPTS/resolve_refs.py $CONF . $BUILD_REPOSITORY_URI $BUILD_SOURCEBRANCH
./install.sh

source virtualenv/bin/activate
if [ "$1" == "nightly" ] || [ "$NIGHTLY" == "true" ]; then
    $SCRIPTS/discover_tests.py --repo $BUILD_REPOSITORY_URI --config $CONF --src ./src --skip-dependents > tests.txt
elif [[ "$CI_DIRECTIVES" =~ "include-nightly" ]]; then
    $SCRIPTS/discover_tests.py --repo $BUILD_REPOSITORY_URI --config $CONF --src ./src > tests.txt
else
    $SCRIPTS/discover_tests.py --repo $BUILD_REPOSITORY_URI --config $CONF --src ./src --eval-attribute 'speed != "slow"' > tests.txt
fi
cd ..

# remove some unneeded files to reduce bloat
find build \( \
	-type d -and \( \
		\( -name .git -and -not -wholename "*/$(echo $BUILD_REPOSITORY_URI | cut -d"/" -f2)/.git" \) \
		-or -name __pycache__ \
		-or -name "*.egg-info" \
		-or \( -wholename "*/sphinx/locale/*" -and -not -name LC_MESSAGES \) \
		-or \( -wholename "build/virtualenv/*" -and -name tests \) \
		-or -wholename "*/angr/build" \
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
tar -I zstd -cf build.tar.zst build/src build/virtualenv build/tests.txt
