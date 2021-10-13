#!/usr/bin/env python3

import collections
import os
import shutil
import subprocess
import sys


def parse_tests(f):
    res = collections.defaultdict(list)
    for l in f.readlines():
        split = l.strip().split()
        res[split[0]].append(split[1])
    return res


def test_all_projects():
    command = "pytest -n auto --junitxml /tmp/tests.xml ./src"
    return subprocess.run(command, shell=True).returncode


def main():
    test_file = None
    coverage = False

    args = iter(sys.argv[1:])

    for arg in args:
        if arg in ('--tests'):
            test_file = next(args)
        elif arg in ('--coverage',):
            coverage = True
        else:
            raise ValueError("Bad argument: %s" % arg)

        if test_file is None:
            raise ValueError('Missing --tests')

    os.makedirs('results')

    error_count = 0

    rc = test_all_projects()
    error_count += rc

    if os.path.exists('/tmp/tests.xml'):
        shutil.move('/tmp/tests.xml', "results/%s.tests.xml" % k)
    with open("results/all.returncode", 'w') as rcf:
        rcf.write(str(rc))
        rcf.close()

    sys.exit(error_count)


if __name__ == '__main__':
    main()
