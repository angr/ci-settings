set -ex

source $(dirname $0)/vars.sh

mkdir sdist

for i in $(ls $CHECKOUT_DIR); do
    if [ -e "$CHECKOUT_DIR/$i/setup.py" ]; then
        pushd "$CHECKOUT_DIR/$i"
        python setup.py sdist
        mv dist/* ../../sdist
        popd
    fi
done
