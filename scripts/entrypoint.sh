#!/bin/bash -e

if grep '^https://' <<<"$1" >/dev/null 2>/dev/null; then
    wget -Obuild.tar.gz "$(python3 /root/scripts/archive_url.py "$1")"
    tar -xf build.tar.gz
    rm build.tar.gz
    EXPECTED_DIR="$(dirname $(dirname $(grep 'VIRTUAL_ENV=' build/virtualenv/bin/activate | cut -d'"' -f2)))"
    mkdir -p "$EXPECTED_DIR"
    mv build $EXPECTED_DIR
    cd "$EXPECTED_DIR/build"
    source virtualenv/bin/activate
    shift
fi

if [ -z "$1" ]; then
    exec bash
else
    exec "$@"
fi
