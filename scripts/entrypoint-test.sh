#!/bin/bash -ex

# TODO: refactor so worker id is an explicit argument instead of defined by the filter mode

function usage () {
    set +x
    echo "Usage: run-process.sh [build id] [filter mode] [filter parameters]"
    echo
    echo "The filter mode picks which tests to run."
    echo
    echo "Filter modes:"
    echo " all - run all tests"
    echo " worker [n] [id] - run every nth test starting from offset id"
    echo " optworker [n] [id] - optimally pick the tests for worker id+1 of n"
    echo " repo [repo] - run tests from the given repo (just the name)"
    echo " explicit [testname] [...] - run the given tests"
    echo " debug - drop into a shell after downloading the build"

    exit 1
}

BUILD_ID=$1

if ! download-build.sh $BUILD_ID; then
    echo 'Error: download failed; bad build id'
    echo
    usage
fi

case $2 in
    all)
        cat tests.txt > todo.txt
        WORKER_ID="all"
        ;;
    worker)
        cat tests.txt | awk "NR % $3 == $4" > todo.txt
        WORKER_ID=$4
        ;;
    optworker)

        cat tests.txt | mp-sched.py $BUILD_ID $3 $4 > todo.txt
        WORKER_ID=$4
        ;;
    repo)
        cat tests.txt | grep "^$3 " > todo.txt
        WORKER_ID=$3
        ;;
    explicit)
        while [ -n "$3" ]; do
            echo $3 >> todo.txt
            shift
        done
        WORKER_ID="explicit"
        ;;
    debug)
        bash
        exit 0
        ;;
    *)
        usage
        ;;
esac

set +e
    test.sh todo.txt
    RESULT=$?
set -e
publish-results.sh $BUILD_ID $WORKER_ID
exit $RESULT
