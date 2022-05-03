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


def test_project(project, tests, coverage=False):
    coverage_flags = "--with-coverage --coverage ./src/{}".format(project)

    command = "nose2 -v -s ./src/{}/tests -c /root/conf/nose2.cfg --log-level 100 {} {}".format(
        project, coverage_flags if coverage else '', ' '.join(tests))

    print("Running nose2 command:\n{}".format(command), flush=True)
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

    with open(test_file) as f:
        test_dict = parse_tests(f)
        for k in test_dict:
            rc = test_project(k, test_dict[k], coverage=coverage)
            error_count += rc
            with open("results/%s.returncode" % k, 'w') as rcf:
                rcf.write(str(rc))
                rcf.close()

            if os.path.exists('/tmp/tests.xml'):
                shutil.move('/tmp/tests.xml', "results/%s.tests.xml" % k)

            if os.path.exists("coverage.xml"):
                shutil.move("coverage.xml", "results/%s.coverage.xml" % k)

    sys.exit(error_count)


if __name__ == '__main__':
    main()
