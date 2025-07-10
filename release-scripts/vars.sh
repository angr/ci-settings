VERSION_ID="$BUILD_BUILDID"
REPOS="binaries archinfo pyvex cle claripy angr angr-management"
CHECKOUT_DIR=repos
NATIVE_PACKAGES="pyvex angr"


function is_native_package() {
    package=$1
    for p in $NATIVE_PACKAGES; do
        if [[ "$package" == "$p" ]]; then
            return 0
        fi
    done
    return 1
}
