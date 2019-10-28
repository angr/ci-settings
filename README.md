# ci-settings

This is our repo containing the docker image used for our azure CI. Most people
won't need to touch this, and instead should use our regular images. This is
mostly useful if you are either hacking on CI, or super confused why tests are
failing for your pull request.

## Manual instructions

```sh
docker run -it angr/ci:1 bash
```

Also note that version 2 is in development and should hopefully be live soon.

```sh
# Change these to the relevant repo and branch
# Your pull request will be refs/pull/{id}
export BUILD_REPOSITORY_URI=angr/angr
export BUILD_SOURCEBRANCH=refs/heads/master

# We slice up our work among workers, 10 currently. You can play with these
# numbers to run only a subset of the tests. You can change these between
# running the azure-test.sh script, without rebuilding.
export WORKER=0
export NUM_WORKERS=10

# Build step
/root/scripts/azure-build.sh
# Lint step
/root/scripts/azure-lint.sh
# Test step
/root/scripts/azure-test.sh
```

After building, there will be a `build` directory you can `cd` into that has
everything of interest. Most importantly, the `virtualenv` and `src` directories
you can use if you need to run specific tests outside of the standard testing
scripts.
