#!/bin/bash
# Fail the release if angr/binaries and angr/angr are not on the same version.
set -euo pipefail

binaries_version=$(tr -d '[:space:]' < "$CHECKOUT_DIR/binaries/VERSION")
angr_version=$(grep -m 1 '__version__' "$CHECKOUT_DIR/angr/angr/__init__.py" | cut -d'"' -f2)

echo "angr/binaries version: $binaries_version"
echo "angr/angr version: $angr_version"

if [ -z "$binaries_version" ] || [ -z "$angr_version" ]; then
    echo "::error::Could not read the angr/binaries or angr/angr version"
    exit 1
fi

if [ "$binaries_version" != "$angr_version" ]; then
    echo "::error::angr/binaries ($binaries_version) and angr/angr ($angr_version) versions are out of sync"
    exit 1
fi
