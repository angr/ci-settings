VERSION_ID="$BUILD_BUILDID"
REPOS="binaries archinfo pyvex cle claripy ailment angr angr-management"
REPOS_LINUX_ONLY="archr"
CHECKOUT_DIR=repos
NATIVE_PACKAGES="pyvex angr"

function is_linux_only() {
    for p in $REPOS_LINUX_ONLY; do
        if [[ $1 == *$p* ]]; then
            return 0
        fi
    done
    return 1
}

function is_native_package() {
    package=$1
    for p in $NATIVE_PACKAGES; do
        if [[ "$package" == "$p" ]]; then
            return 0
        fi
    done
    return 1
}
