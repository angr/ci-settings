set -ex

source $(dirname $0)/vars.sh

mkdir sdist

export PIP_FIND_LINKS="sdist"
for i in $(ls $CHECKOUT_DIR); do
    if [ -e "$CHECKOUT_DIR/$i/setup.py" ]; then
        python -m build --sdist --outdir=sdist $CHECKOUT_DIR/$i
    fi
done
