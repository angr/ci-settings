#!/usr/bin/env python3

# this script transforms the output of the testcase grep into [repo] [testcase].[function] and does the attribute filters!
# also throws out rex tests

import os
import sys
import nose2.plugins.attrib
from importlib import reload

sys.path.append('.')

class MockSuite(object):
    def __init__(self):
        self.tests = []

    def addTest(self, test):
        self.tests.append(test)

    def __iter__(self):
        return iter(self.tests)

class MockSession(object):
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

    for arg in args:
        if arg in ('-A', '--attribute'):
            attrfilter.attribs.append(next(args))
        elif arg in ('-E', '--eval-attribute'):
            attrfilter.eval_attribs.append(next(args))
        else:
            raise ValueError("Bad argument: %s" % arg)

    try:
        while True:
            line = input()

            if '/rex/' in line:
                continue
            if '/povsim/' in line:
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
    except EOFError:
        pass

    event = session
    event.suite = suite
    attrfilter.moduleLoadedSuite(event)

    for function in event.suite.tests:
        print(function._path)

if __name__ == '__main__':
    main()
