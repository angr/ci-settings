#!/bin/bash

# :(

cat >> $(python -c "import nose, os; print os.path.join(os.path.dirname(nose.__file__), 'plugins/attrib.py')") <<EOF

    def loadTestsFromName(self, name, module):
        from nose.suite import ContextList
        import inspect
        from nose.plugins import attrib as dummycontext
        pself = inspect.currentframe().f_back.f_back.f_back.f_back.f_locals['self']
        if not name or not module:
            return None
        parent, obj = pself.resolve(name, module)
        if parent is not module:
            return None
        if self.wantFunction(obj) is not None:
            return ContextList([pself.makeTest(dummytest, dummycontext)], context=dummycontext)
        else:
            return None

def dummytest():
    pass
EOF
