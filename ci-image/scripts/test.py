#!/usr/bin/env python3

import os
import pathlib
import shutil
import subprocess
import sys


def parse_tests(path):
    with open(path) as f:
        res = []
        for l in f.readlines():
            split = l.strip().split()
            split[0] += "_tests"
            res.append(".".join(split))
        return res


def test_all_projects(tests):
    # Create directories
    if os.path.exists("src/tests"):
        os.remove("src/tests")
    os.makedirs("src/tests")
    # Link tests
    for project in os.listdir("src"):
        if os.path.exists("src/{}/tests".format(project)):
            shutil.copytree("src/%s/tests" % project, "src/tests/%s_tests" % project)
            pathlib.Path("src/tests/%s_tests/__init__.py" % project).touch()

    command = "nose2 -v -s ./src/tests -c /root/config/nose2.cfg --log-level 100 {}".format(' '.join(tests))

    print("Running nose2 command:\n{}".format(command), flush=True)
    return subprocess.run(command, shell=True).returncode


def main():
    test_file = None

    args = iter(sys.argv[1:])

    for arg in args:
        if arg in ('--tests'):
            test_file = next(args)
        else:
            raise ValueError("Bad argument: %s" % arg)

        if test_file is None:
            raise ValueError('Missing --tests')

    os.makedirs('results')

    tests = parse_tests(test_file)
    rc = test_all_projects(tests)

    if os.path.exists('/tmp/tests.xml'):
        shutil.move('/tmp/tests.xml', "results/tests.xml")

    sys.exit(rc)


if __name__ == '__main__':
    main()
