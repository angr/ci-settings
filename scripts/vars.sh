VERSION_ID="$BUILD_BUILDID"
REPOS="$("$python" scripts/get_repo_names.py)"
CHECKOUT_DIR=repos
DOC_REQUIREMENTS=(sphinx sphinx_rtd_theme)
