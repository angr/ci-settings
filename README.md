# ci-settings

This is our repo containing the docker image used for our azure CI. Most people
won't need to touch this, and instead should use our regular images. This is
mostly useful if you are either hacking on CI, or super confused why tests are
failing for your pull request.

## Manual instructions

To get a shell in the virtualenv associated with a given build (locally!), run:

```sh
docker run -it --rm angr/ci:1 <build url>
```

where `<build url>` is where you paste the url for a build page from azure, for
example, `https://dev.azure.com/angr/angr/_build/results?buildId=757`. The
exact page you use isn't all that important. As long as it's associated with
the build it'll have the metadata in it for the script to work.

The download will generally be about 700mb. If you don't have it, the docker
container will also be about 700mb.

### Manual builds

To perform a build manually:

```sh
docker run -it --rm angr/ci:1
```

And the, in the container:

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

## Versioning

`angr/ci:1` refers to version 1 of the container. Version 2 is in development.
