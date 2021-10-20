#!/usr/bin/env python3

import collections
from concurrent.futures import as_completed, CancelledError
import io
import os
import shlex
import sys
import threading

from loky import get_reusable_executor
import nose2


class RedirectFileDescriptor:
    def __init__(self, fd: int, buffer: io.BytesIO):
        self.fd = fd
        self.buffer = buffer

    def __enter__(self):
        self.pipe_read, self.pipe_write = os.pipe()

        self.original = os.dup(self.fd)
        os.close(self.fd)
        os.dup2(self.pipe_write, self.fd)

        def pipe2buffer():
            while True:
                try:
                    data = os.read(self.pipe_read, 1024)
                    if not data:
                        break
                    self.buffer.write(data)
                except OSError:
                    break

        self.marshal_thread = threading.Thread(target=pipe2buffer)
        self.marshal_thread.start()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        os.close(self.fd)
        os.close(self.pipe_read)
        os.close(self.pipe_write)
        os.dup2(self.original, self.fd)
        self.marshal_thread.join()


# Reads tests file and returns a dict of project names to lists of tests
def parse_tests(f):
    res = collections.defaultdict(list)
    for l in f.readlines():
        split = l.strip().split()
        res[split[0]].append(split[1])
    return res


def run_single_test(project: str, test: str, coverage: bool = False):
    coverage_flags = "--with-coverage --coverage ./src/{}".format(project) if coverage else ""

    command = "nose2 -s ./src/{}/tests -c /root/config/nose2.cfg --log-level 100 --junit-xml-path {} {} {}".format(
        project, os.path.join("results", project, test), coverage_flags, test)

    print("Running nose2 command:\n{}".format(command), flush=True)
    stdout = io.BytesIO()
    stderr = io.BytesIO()
    with RedirectFileDescriptor(1, stdout), RedirectFileDescriptor(2, stderr):
        try:
            runner = nose2.discover(exit=False, argv=shlex.split(command))
        except Exception as e:
            print(e, file=stderr)
        finally:
            with open(os.path.join("results", project, test + ".stdout"), "wb") as f:
                f.write(stdout.getvalue())
            with open(os.path.join("results", project, test + ".stderr"), "wb") as f:
                f.write(stderr.getvalue())

        return (
            True if runner.result.wasSuccessful() else False,
            stdout.getvalue().decode(),
            stderr.getvalue().decode()
        )


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

    os.makedirs('results', exist_ok=True)

    error_count = 0

    with open(test_file) as f:
        test_dict = parse_tests(f)

    with get_reusable_executor() as executor:
        futures = []
        futures_meta = {}
        for project, tests in test_dict.items():
            os.makedirs(os.path.join("results", project), exist_ok=True)
            for test in tests:
                fut = executor.submit(run_single_test, project, test, coverage)
                futures.append(fut)
                futures_meta[fut] = (project, test)

        completions = 0
        for future in as_completed(futures):
            completions += 1
            print("Completed: {}/{}, Errors: {}".format(completions, len(futures), error_count), flush=True)
            try:
                if not future.result()[0]:
                    error_count += 1
            except CancelledError:
                error_count += 1
            except Exception as e:
                error_count += 1
                print(e)
            project, test = futures_meta[future]
            print("stdout for", project, test, "\n", future.result()[1], flush=True)
            print("stderr for", project, test, "\n", future.result()[2], flush=True)

            if completions >= len(futures):
                break

    sys.exit(error_count)


if __name__ == '__main__':
    main()
