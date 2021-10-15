#!/usr/bin/env python3

import collections
from concurrent.futures import ThreadPoolExecutor, as_completed, CancelledError
import multiprocessing
import os
import subprocess
import sys


# Reads tests file and returns a dict of project names to lists of tests
def parse_tests(f):
    res = collections.defaultdict(list)
    for l in f.readlines():
        split = l.strip().split()
        res[split[0]].append(split[1])
    return res


def run_single_test(project: str, test: str, coverage: bool = False):
    coverage_flags = "--with-coverage --coverage ./src/{}".format(project) if coverage else ""

    command = "nose2 -v -s ./src/{}/tests -c /root/config/nose2.cfg --log-level 100 --junit-xml-path {} {} {}".format(
        project, os.path.join("results", project, test), coverage_flags, test)

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

    with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = []
        for project, tests in test_dict.items():
            os.makedirs(os.path.join("results", project))
            for test in tests:
                futures.append(executor.submit(run_single_test, project, test, coverage))

        for future in as_completed(futures):
            try:
                error_count += future.result()
            except CancelledError:
                error_count += 1

    sys.exit(error_count)


if __name__ == '__main__':
    main()
