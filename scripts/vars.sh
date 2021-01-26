VERSION_ID="$BUILD_BUILDID"
REPOS="binaries vex angr-doc archinfo pyvex cle claripy ailment angr angr-management angrop"
REPOS_LINUX_ONLY="archr"
CHECKOUT_DIR=repos
DOC_REQUIREMENTS="sphinx sphinx_rtd_theme"

function is_linux_only() {
    for p in $REPOS_LINUX_ONLY; do
        if [[ $1 == *$p* ]]; then
            return 0
        fi
    done
    return 1
}
