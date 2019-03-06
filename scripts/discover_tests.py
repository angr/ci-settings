#!/usr/bin/env python3

# this script transforms the output of the testcase grep into [repo] [testcase].[function] and does the attribute filters!
# also filters tests by the dependency graph

import os
import sys
import subprocess
import nose2.plugins.attrib
from importlib import reload

sys.path.append('.')
sys.path.append(os.path.dirname(os.path.basename(__file__)))
from repos import load_config

class MockSuite:
    def __init__(self):
        self.tests = []

    def addTest(self, test):
        self.tests.append(test)

    def __iter__(self):
        return iter(self.tests)

class MockSession:
    def __init__(self):
        self.suite = None

    @property
    def pluginargs(self):
        return self

    def add_argument(self, *args, **kwargs):
        pass

def main():
    args = iter(sys.argv[1:])
    session = MockSession()
    attrfilter = nose2.plugins.attrib.AttributeSelector(session=session)
    suite = MockSuite()
    base_cwd = os.getcwd()
    target_repo = None
    config_dir = None
    src_dir = None

    for arg in args:
        if arg in ('-A', '--attribute'):
            attrfilter.attribs.append(next(args))
        elif arg in ('-E', '--eval-attribute'):
            attrfilter.eval_attribs.append(next(args))
        elif arg in ('--repo',):
            target_repo = next(args)
        elif arg in ('--config',):
            config_dir = next(args)
        elif arg in ('--src',):
            src_dir = next(args)
        else:
            raise ValueError("Bad argument: %s" % arg)

    targets = None
    if config_dir is not None:
        targets = load_config(os.path.join(config_dir, 'repo-list.txt'))

    if target_repo is not None:
        if targets is None:
            raise ValueError("provided --repo without --config")

        if target_repo.endswith('.git'):
            target_repo = target_repo[:-4]
        target_repo = target_repo.split('/')[-1]

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

    proc = subprocess.Popen("find %s/*/tests -name test_*.py | xargs grep '^def test_' | sed 's/def //' | cut -d '(' -f 1" % src_dir, shell=True, stdout=subprocess.PIPE)

    while True:
        line = proc.stdout.readline().strip().decode()
        if not line:
            break

        if whitelist is not None:
            for repo in whitelist:
                if '/%s/tests/' % repo in line:
                    break
            else:
                continue

        path, function_name = line.split(':')
        assert path.endswith('.py')
        assert '/' in path

        pathkeys = path.split('/')
        assert pathkeys[-2] == 'tests'
        repo = pathkeys[-3]
        directory = '/'.join(pathkeys[:-1])
        os.chdir(base_cwd)
        os.chdir(directory)
        module_name = pathkeys[-1][:-3]

        module = __import__(module_name)
        module = reload(module)
        function = getattr(module, function_name)
        function._path = '%s %s.%s' % (repo, module_name, function_name)

        suite.addTest(function)

    event = session
    event.suite = suite
    attrfilter.moduleLoadedSuite(event)

    for function in event.suite.tests:
        print(function._path)

if __name__ == '__main__':
    main()
