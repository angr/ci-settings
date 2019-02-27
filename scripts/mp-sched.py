#!/usr/bin/env python3

# this file implements the LPT algorithm for the multiprocessor scheduling problem

import os
import sys
import json

def main():
    build_id = int(sys.argv[1])
    num_workers = int(sys.argv[2])
    worker_id = int(sys.argv[3])

    with open('timeinfo.json') as fp:
        data = json.load(fp)

    sortedtests = []
    for line in sys.stdin:
        suite, name = line.split()
        try:
            time = data[suite][name]
        except KeyError:
            print('No data for test', suite, name, file=sys.stderr)
            time = 20
        sortedtests.append((time, line.strip()))

    sortedtests.sort(reverse=True)
    workers = [[0, []] for _ in range(num_workers)]

    for time, line in sortedtests:
        nextworker = min(workers)
        nextworker[0] += time
        nextworker[1].append(line)

    for line in workers[worker_id][1]:
        print(line)


if __name__ == '__main__':
    main()
