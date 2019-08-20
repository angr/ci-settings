#!/usr/bin/env python3

# this script transforms the output of the testcase grep into [repo] [testcase].[function] and does the attribute filters!
# also filters tests by the dependency graph

import os
import sys
import subprocess
from importlib import reload

sys.path.append('.')
sys.path.append(os.path.dirname(os.path.basename(__file__)))
from repos import load_config


def main():
    args = iter(sys.argv[1:])
    a_str = None
    e_str = None
    target_repo = None
    config_dir = None
    src_dir = None

    for arg in args:
        if arg in ('-A', '--attribute'):
            a_str = next(args)
        elif arg in ('-E', '--eval-attribute'):
            e_str = next(args)
        elif arg in ('--repo',):
            target_repo = next(args)
        elif arg in ('--config',):
            config_dir = next(args)
        elif arg in ('--src',):
            src_dir = next(args)
        else:
            raise ValueError("Bad argument: %s" % arg)

    targets = None
    # Load repo configs
    if config_dir is not None:
        targets = load_config(os.path.join(config_dir, 'repo-list.txt'))

    if target_repo is not None:
        if targets is None:
            raise ValueError("provided --repo without --config")

        # clean target name
        if target_repo.endswith('.git'):
            target_repo = target_repo[:-4]
        target_repo = target_repo.split('/')[-1]

        # build queue of all repos that need to be searched for tests
        seen = set()
        queue = [target_repo]
        while queue:
            repo = queue.pop(0)
            if repo in seen:
                continue
            seen.add(repo)

            for target in targets:
                if repo in target.deps:
                    queue.append(target.repo)

        whitelist = list(seen)
    else:
        whitelist = None

    for target in whitelist:
        path = os.path.join(src_dir, target)
        arg_list = "nose2 -s {} --collect-only --plugin nose_skinny_report --plugin nose2.plugins.attrib --exclude-plugin nose2.plugins.result".format(path).split()
        if a_str != None:
            arg_list.append("-A")
            arg_list.append(a_str)
        if e_str != None:
            arg_list.append("-E")
            arg_list.append(e_str)
        proc = subprocess.Popen(arg_list, stdout=subprocess.PIPE)

        while True:
            line = proc.stdout.readline().strip().decode()
            if line:
                print(target, line)
            else:
                break


if __name__ == '__main__':
    main()
