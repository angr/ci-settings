# This file is just some useful defaults for testing and running locally. It is
# not invoked on an actual CI server. It should be sourced, and will drop you in
# a folder with the minimum enviroment varibles set for basic function.

set -x

WORKDIR=/__w/1/s

mkdir -p $WORKDIR
cd $WORKDIR

export BUILD_REPOSITORY_URI=angr/angr
export BUILD_SOURCEBRANCH=refs/heads/master

export WORKER=0
export NUM_WORKERS=1

set +x
