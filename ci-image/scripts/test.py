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


def test_project(project, tests):
    command = (
        "nose2 -v -s ./src/{}/tests -c /root/conf/nose2.cfg --log-level 100 {}".format(
            project, " ".join(tests)
        )
    )

    print("Running nose2 command:\n{}".format(command), flush=True)
    return subprocess.run(command, shell=True).returncode


def main():
    test_file = None

    args = iter(sys.argv[1:])

    for arg in args:
        if arg in ("--tests"):
            test_file = next(args)
        else:
            raise ValueError("Bad argument: %s" % arg)

        if test_file is None:
            raise ValueError("Missing --tests")

    os.makedirs("results")

    error_count = 0

    with open(test_file) as f:
        test_dict = parse_tests(f)
        for k in test_dict:
            rc = test_project(k, test_dict[k])
            error_count += rc
            with open("results/%s.returncode" % k, "w") as rcf:
                rcf.write(str(rc))
                rcf.close()

            if os.path.exists("/tmp/tests.xml"):
                shutil.move("/tmp/tests.xml", "results/%s.tests.xml" % k)

    sys.exit(error_count)


if __name__ == "__main__":
    main()
