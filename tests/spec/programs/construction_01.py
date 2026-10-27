# spec: PLS-315 10.2
# description: Programs on instance creation through __new__ and __init__, each with the output CPython 3.15 gives.
from harness import *

check_program('''class C:
    pass
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
              '''C None
C None
None
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
''')

check_program('''class C:
    pass
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
              '''C None
C None
None
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
''')

check_program('''class C:
    pass
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
              '''C ((), {})
C None
None
C ((1,), {})
C None
TypeError
C ((), {'x': 2})
C None
TypeError
C ((1,), {'x': 2})
C None
TypeError
''')

check_program('''class C:
    pass
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
              '''TypeError
C None
None
TypeError
C None
TypeError
TypeError
C None
TypeError
TypeError
C None
TypeError
''')

check_program('''class C:
    __new__ = object.__new__
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
              '''C None
C None
None
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
''')

check_program('''class C:
    __new__ = object.__new__
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
              '''C None
C None
None
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
''')

check_program('''class C:
    __new__ = object.__new__
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
              '''C ((), {})
C None
None
C ((1,), {})
C None
TypeError
C ((), {'x': 2})
C None
TypeError
C ((1,), {'x': 2})
C None
TypeError
''')

check_program('''class C:
    __new__ = object.__new__
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
              '''TypeError
C None
None
TypeError
C None
TypeError
TypeError
C None
TypeError
TypeError
C None
TypeError
''')

check_program('''class C:
    def __new__(cls, *args, **kw): return object.__new__(cls)
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
              '''C None
C None
None
C None
TypeError
None
C None
TypeError
None
C None
TypeError
None
''')

check_program('''class C:
    def __new__(cls, *args, **kw): return object.__new__(cls)
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
              '''C None
C None
None
C None
TypeError
None
C None
TypeError
None
C None
TypeError
None
''')

check_program('''class C:
    def __new__(cls, *args, **kw): return object.__new__(cls)
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
              '''C ((), {})
C None
None
C ((1,), {})
TypeError
TypeError
C ((), {'x': 2})
TypeError
TypeError
C ((1,), {'x': 2})
TypeError
TypeError
''')

check_program('''class C:
    def __new__(cls, *args, **kw): return object.__new__(cls)
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
              '''TypeError
C None
None
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
''')

check_program('''class C:
    @staticmethod
    def __new__(cls, *args, **kw): return object.__new__(cls)
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
              '''C None
C None
None
C None
TypeError
None
C None
TypeError
None
C None
TypeError
None
''')

check_program('''class C:
    @staticmethod
    def __new__(cls, *args, **kw): return object.__new__(cls)
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
              '''C None
C None
None
C None
TypeError
None
C None
TypeError
None
C None
TypeError
None
''')

check_program('''class C:
    @staticmethod
    def __new__(cls, *args, **kw): return object.__new__(cls)
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
              '''C ((), {})
C None
None
C ((1,), {})
TypeError
TypeError
C ((), {'x': 2})
TypeError
TypeError
C ((1,), {'x': 2})
TypeError
TypeError
''')

check_program('''class C:
    @staticmethod
    def __new__(cls, *args, **kw): return object.__new__(cls)
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
              '''TypeError
C None
None
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
''')

check_program('''class C:
    @classmethod
    def __new__(owner, cls, *args, **kw): return object.__new__(cls)
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
              '''C None
C None
None
C None
TypeError
None
C None
TypeError
None
C None
TypeError
None
''')

check_program('''class C:
    @classmethod
    def __new__(owner, cls, *args, **kw): return object.__new__(cls)
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
              '''C None
C None
None
C None
TypeError
None
C None
TypeError
None
C None
TypeError
None
''')

check_program('''class C:
    @classmethod
    def __new__(owner, cls, *args, **kw): return object.__new__(cls)
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
              '''C ((), {})
C None
None
C ((1,), {})
TypeError
TypeError
C ((), {'x': 2})
TypeError
TypeError
C ((1,), {'x': 2})
TypeError
TypeError
''')

check_program('''class C:
    @classmethod
    def __new__(owner, cls, *args, **kw): return object.__new__(cls)
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
              '''TypeError
C None
None
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
TypeError
''')
