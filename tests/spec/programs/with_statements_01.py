# spec: PLS-315 15.5
# description: Programs on with statements, each with the output CPython 3.15 gives.
from harness import *

check_program('''log = []
class Manager:
    def __init__(self, name, suppress=False):
        self.name = name
        self.suppress = suppress
    def __enter__(self):
        log.append(self.name)
        return 42
    def __exit__(self, kind, value, traceback):
        log.append((self.name, kind is ValueError))
        return self.suppress
with Manager('outer'), Manager('inner', True) as value:
    print(value)
    raise ValueError('detail')
print(log)
def f():
    with Manager('return'):
        return 3
print(f())
''',
              '''42
['outer', 'inner', ('inner', True), ('outer', False)]
3
''')

check_program('''with 1:
    pass
''',
              '''TypeError: 'int' object does not support the context manager protocol (missed __exit__ method)
''')
