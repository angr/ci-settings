#!/bin/bash -x

TESTS_LIST=$1
TOTAL_CODE=0

if [ -z "$TESTS_LIST" ]; then
    echo "Usage: test.sh tests.txt"
    exit 1
fi

echo "Running tests:"
cat $TESTS_LIST
echo

mkdir -p results
echo "Saving results to $PWD/results"
echo

source virtualenv/bin/activate

# tests list should be a list of lines like:
# reponame test_foo.py.test_something
# we cut out the first part and then run one instance of nose2 per repo
for SUITE in $(cat $TESTS_LIST | cut -d ' ' -f 1 | sort -u); do
  nose2 -v -s "./src/$SUITE/tests" -c "/conf/nose2.cfg" \
    -N $(cat /proc/cpuinfo | grep processor | wc -l) \
    --log-level 100 \
    $(grep "^$SUITE " $TESTS_LIST | cut -d ' ' -f 2)
  CODE=$?
  TOTAL_CODE=$(($CODE + $TOTAL_CODE))
  echo $CODE > results/$SUITE.exitcode

  if [ -f /tmp/tests.xml ]; then
    mv /tmp/tests.xml results/$SUITE.xml
  else
    grep "^$SUITE " $TESTS_LIST >> results/missing.txt
  fi
done

echo $TOTAL_CODE > results/total.exitcode
exit $TOTAL_CODE
