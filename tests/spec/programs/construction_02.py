# spec: PLS-315 10.2
# description: Programs on instance creation through __new__ and __init__, each with the output CPython 3.15 gives.
from harness import *

check_program('''class C:
    def __new__(cls, *args, **kw): return 42
    pass

for args, kw in [((), {}), ((1,), {}), ((), {'x': 2}), ((1,), {'x': 2})]:
    for action in ['call', 'allocate', 'initialize']:
        try:
            if action == 'call':
                value = C(*args, **kw)
                print(type(value).__name__, getattr(value, 'seen', None))
            elif action == 'allocate':
                value = object.__new__(C, *args, **kw)
                print(type(value).__name__, getattr(value, 'seen', None))
            else:
                value = object.__new__(C)
                print(object.__init__(value, *args, **kw))
        except Exception as error: print(type(error).__name__)
''',
              '''int None
C None
None
int None
TypeError
None
int None
TypeError
None
int None
TypeError
None
''')

check_program('''class C:
    def __new__(cls, *args, **kw): return 42
    __init__ = object.__init__

for args, kw in [((), {}), ((1,), {}), ((), {'x': 2}), ((1,), {'x': 2})]:
    for action in ['call', 'allocate', 'initialize']:
        try:
            if action == 'call':
                value = C(*args, **kw)
                print(type(value).__name__, getattr(value, 'seen', None))
            elif action == 'allocate':
                value = object.__new__(C, *args, **kw)
                print(type(value).__name__, getattr(value, 'seen', None))
            else:
                value = object.__new__(C)
                print(object.__init__(value, *args, **kw))
        except Exception as error: print(type(error).__name__)
''',
              '''int None
C None
None
int None
TypeError
None
int None
TypeError
None
int None
TypeError
None
''')

check_program('''class C:
    def __new__(cls, *args, **kw): return 42
    def __init__(self, *args, **kw): self.seen = args, kw

for args, kw in [((), {}), ((1,), {}), ((), {'x': 2}), ((1,), {'x': 2})]:
    for action in ['call', 'allocate', 'initialize']:
        try:
            if action == 'call':
                value = C(*args, **kw)
                print(type(value).__name__, getattr(value, 'seen', None))
            elif action == 'allocate':
                value = object.__new__(C, *args, **kw)
                print(type(value).__name__, getattr(value, 'seen', None))
            else:
                value = object.__new__(C)
                print(object.__init__(value, *args, **kw))
        except Exception as error: print(type(error).__name__)
''',
              '''int None
C None
None
int None
TypeError
TypeError
int None
TypeError
TypeError
int None
TypeError
TypeError
''')

check_program('''class C:
    def __new__(cls, *args, **kw): return 42
    def __init__(self, *args, **kw): return 1

for args, kw in [((), {}), ((1,), {}), ((), {'x': 2}), ((1,), {'x': 2})]:
    for action in ['call', 'allocate', 'initialize']:
        try:
            if action == 'call':
                value = C(*args, **kw)
                print(type(value).__name__, getattr(value, 'seen', None))
            elif action == 'allocate':
                value = object.__new__(C, *args, **kw)
                print(type(value).__name__, getattr(value, 'seen', None))
            else:
                value = object.__new__(C)
                print(object.__init__(value, *args, **kw))
        except Exception as error: print(type(error).__name__)
''',
              '''int None
C None
None
int None
TypeError
TypeError
int None
TypeError
TypeError
int None
TypeError
TypeError
''')
