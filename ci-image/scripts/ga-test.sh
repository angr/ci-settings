#!/bin/bash -ex

BASEDIR=$(dirname $(dirname $0))
SCRIPTS=$BASEDIR/scripts
CONF=$BASEDIR/conf


tar -I zstd -xf build.tar.zst
cd build
cp $CONF/nose2.cfg .

# Get the repository name without the owner part
REPO_NAME=$(echo $GITHUB_REPOSITORY | cut -d '/' -f 2)

# Filter tests based on INCLUDE_SELF parameter
if [ "$INCLUDE_SELF" == "false" ]; then
    # Exclude tests for the self repository
    grep -v "^$REPO_NAME " tests.txt > filtered_tests.txt
    mv filtered_tests.txt tests.txt
fi

cat tests.txt | awk "NR % $NUM_WORKERS == $WORKER" > todo.txt
source virtualenv/bin/activate

# Create results directory
mkdir -p results
ERROR_COUNT=0

# Read test file line by line using readarray/mapfile
readarray -t TESTS < todo.txt

# Process each repo in a loop
for LINE in "${TESTS[@]}"; do
    PROJECT=$(echo $LINE | cut -d ' ' -f 1)
    TESTS=$(echo $LINE | cut -d ' ' -f 2)

    # Run the nose2 test command
    echo "Running nose2 command for project $PROJECT: nose2 -v -s ./src/$PROJECT/tests -c /root/conf/nose2.cfg --log-level 100 $TESTS"
    nose2 -v -s "./src/$PROJECT/tests" -c /root/conf/nose2.cfg --log-level 100 $TESTS
    RC=$?

    # Add to error count
    ERROR_COUNT=$((ERROR_COUNT + RC))

    # Save return code to results
    echo "$RC" > "results/$PROJECT.returncode"

    # Move test results if they exist
    if [ -f "/tmp/tests.xml" ]; then
        mv "/tmp/tests.xml" "results/$PROJECT.tests.xml"
    fi
done

exit $ERROR_COUNT
