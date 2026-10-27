# spec: PLS-315 13.3, 16.1
# description: Programs on argument binding, each with the output CPython 3.15 gives.
from harness import *

check_program('''
class Name(str): pass
a = Name('a')
def named(a): return a
def extra(**kw): return kw
print(named(**{a: 42}))
kw = extra(**{a: 43})
print(next(iter(kw)) is a, kw[a])
print(1, 2, **{Name('sep'): ':'})
print(sorted([3, 1, 2], **{Name('reverse'): True}))
print(pow(**{Name('base'): 2, Name('exp'): 3}))
print(int('10', **{Name('base'): 2}))
class Alias(str):
    def __eq__(self, other): return other == 'a'
    __hash__ = str.__hash__
print(named(**{Alias('alias'): 44}))
class Broken(str):
    def __eq__(self, other): raise ValueError('keyword comparison')
    __hash__ = str.__hash__
try: named(**{Broken('a'): 1})
except ValueError as error: print(error)
class NoIteration: pass
class Disabled:
    __iter__ = None
class Raises:
    def __iter__(self): raise TypeError('iterator error')
for value in [NoIteration(), Disabled(), Raises()]:
    try: extra(*value)
    except TypeError as error: print(type(error).__name__, 'iterator error' in str(error))
def mapping(): pass
mapping.keys = lambda: ['a']
try: named(**mapping)
except TypeError: print('keys alone do not make an object subscriptable')
class BrokenKeys:
    def keys(self): raise ValueError('keys error')
try: named(**BrokenKeys())
except ValueError as error: print(error)
''',
              '''42
True 43
1:2
[3, 2, 1]
8
2
44
keyword comparison
TypeError False
TypeError False
TypeError True
keys alone do not make an object subscriptable
keys error
''')

check_program('''def f(): return ()
for args in [(), (0,), (0, 1), (0, 1, 2), (0, 1, 2, 3), (0, 1, 2, 3, 4), (0, 1, 2, 3, 4, 5)]:
    for kwargs in [{}, {'a': 11}, {'b': 22}, {'a': 11, 'b': 22}, {'zebra': 99}, {'zebra': 99, 'a': 11}, {'a': 11, 'zebra': 99}, {'c': 33, 'd': 44}]:
        try: print(f(*args, **kwargs))
        except TypeError as error: print(type(error).__name__, str(error))
''',
              '''()
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes 0 positional arguments but 1 was given
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes 0 positional arguments but 2 were given
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes 0 positional arguments but 3 were given
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes 0 positional arguments but 4 were given
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes 0 positional arguments but 5 were given
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes 0 positional arguments but 6 were given
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'c'
''')

check_program('''def f(a): return (a,)
for args in [(), (0,), (0, 1), (0, 1, 2), (0, 1, 2, 3), (0, 1, 2, 3, 4), (0, 1, 2, 3, 4, 5)]:
    for kwargs in [{}, {'a': 11}, {'b': 22}, {'a': 11, 'b': 22}, {'zebra': 99}, {'zebra': 99, 'a': 11}, {'a': 11, 'zebra': 99}, {'c': 33, 'd': 44}]:
        try: print(f(*args, **kwargs))
        except TypeError as error: print(type(error).__name__, str(error))
''',
              '''TypeError f() missing 1 required positional argument: 'a'
(11,)
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'c'
(0,)
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes 1 positional argument but 2 were given
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes 1 positional argument but 3 were given
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes 1 positional argument but 4 were given
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes 1 positional argument but 5 were given
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes 1 positional argument but 6 were given
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'c'
''')

check_program('''def f(a, b, c): return (a, b, c)
for args in [(), (0,), (0, 1), (0, 1, 2), (0, 1, 2, 3), (0, 1, 2, 3, 4), (0, 1, 2, 3, 4, 5)]:
    for kwargs in [{}, {'a': 11}, {'b': 22}, {'a': 11, 'b': 22}, {'zebra': 99}, {'zebra': 99, 'a': 11}, {'a': 11, 'zebra': 99}, {'c': 33, 'd': 44}]:
        try: print(f(*args, **kwargs))
        except TypeError as error: print(type(error).__name__, str(error))
''',
              '''TypeError f() missing 3 required positional arguments: 'a', 'b', and 'c'
TypeError f() missing 2 required positional arguments: 'b' and 'c'
TypeError f() missing 2 required positional arguments: 'a' and 'c'
TypeError f() missing 1 required positional argument: 'c'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'd'
TypeError f() missing 2 required positional arguments: 'b' and 'c'
TypeError f() got multiple values for argument 'a'
TypeError f() missing 1 required positional argument: 'c'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'd'
TypeError f() missing 1 required positional argument: 'c'
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'b'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'd'
(0, 1, 2)
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'b'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'c'
TypeError f() takes 3 positional arguments but 4 were given
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'b'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'c'
TypeError f() takes 3 positional arguments but 5 were given
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'b'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'c'
TypeError f() takes 3 positional arguments but 6 were given
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'b'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'c'
''')

check_program('''def f(a=1, b=2): return (a, b)
for args in [(), (0,), (0, 1), (0, 1, 2), (0, 1, 2, 3), (0, 1, 2, 3, 4), (0, 1, 2, 3, 4, 5)]:
    for kwargs in [{}, {'a': 11}, {'b': 22}, {'a': 11, 'b': 22}, {'zebra': 99}, {'zebra': 99, 'a': 11}, {'a': 11, 'zebra': 99}, {'c': 33, 'd': 44}]:
        try: print(f(*args, **kwargs))
        except TypeError as error: print(type(error).__name__, str(error))
''',
              '''(1, 2)
(11, 2)
(1, 22)
(11, 22)
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'c'
(0, 2)
TypeError f() got multiple values for argument 'a'
(0, 22)
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'c'
(0, 1)
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'b'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes from 0 to 2 positional arguments but 3 were given
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'b'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes from 0 to 2 positional arguments but 4 were given
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'b'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes from 0 to 2 positional arguments but 5 were given
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'b'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes from 0 to 2 positional arguments but 6 were given
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'b'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got multiple values for argument 'a'
TypeError f() got an unexpected keyword argument 'c'
''')

check_program('''def f(a, /, b=2): return (a, b)
for args in [(), (0,), (0, 1), (0, 1, 2), (0, 1, 2, 3), (0, 1, 2, 3, 4), (0, 1, 2, 3, 4, 5)]:
    for kwargs in [{}, {'a': 11}, {'b': 22}, {'a': 11, 'b': 22}, {'zebra': 99}, {'zebra': 99, 'a': 11}, {'a': 11, 'zebra': 99}, {'c': 33, 'd': 44}]:
        try: print(f(*args, **kwargs))
        except TypeError as error: print(type(error).__name__, str(error))
''',
              '''TypeError f() missing 1 required positional argument: 'a'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() missing 1 required positional argument: 'a'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got an unexpected keyword argument 'c'
(0, 2)
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
(0, 22)
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got an unexpected keyword argument 'c'
(0, 1)
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got multiple values for argument 'b'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes from 1 to 2 positional arguments but 3 were given
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got multiple values for argument 'b'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes from 1 to 2 positional arguments but 4 were given
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got multiple values for argument 'b'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes from 1 to 2 positional arguments but 5 were given
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got multiple values for argument 'b'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes from 1 to 2 positional arguments but 6 were given
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got multiple values for argument 'b'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got some positional-only arguments passed as keyword arguments: 'a'
TypeError f() got an unexpected keyword argument 'c'
''')

check_program('''def f(a, /, **kw): return (a, kw)
for args in [(), (0,), (0, 1), (0, 1, 2), (0, 1, 2, 3), (0, 1, 2, 3, 4), (0, 1, 2, 3, 4, 5)]:
    for kwargs in [{}, {'a': 11}, {'b': 22}, {'a': 11, 'b': 22}, {'zebra': 99}, {'zebra': 99, 'a': 11}, {'a': 11, 'zebra': 99}, {'c': 33, 'd': 44}]:
        try: print(f(*args, **kwargs))
        except TypeError as error: print(type(error).__name__, str(error))
''',
              '''TypeError f() missing 1 required positional argument: 'a'
TypeError f() missing 1 required positional argument: 'a'
TypeError f() missing 1 required positional argument: 'a'
TypeError f() missing 1 required positional argument: 'a'
TypeError f() missing 1 required positional argument: 'a'
TypeError f() missing 1 required positional argument: 'a'
TypeError f() missing 1 required positional argument: 'a'
TypeError f() missing 1 required positional argument: 'a'
(0, {})
(0, {'a': 11})
(0, {'b': 22})
(0, {'a': 11, 'b': 22})
(0, {'zebra': 99})
(0, {'zebra': 99, 'a': 11})
(0, {'a': 11, 'zebra': 99})
(0, {'c': 33, 'd': 44})
TypeError f() takes 1 positional argument but 2 were given
TypeError f() takes 1 positional argument but 2 were given
TypeError f() takes 1 positional argument but 2 were given
TypeError f() takes 1 positional argument but 2 were given
TypeError f() takes 1 positional argument but 2 were given
TypeError f() takes 1 positional argument but 2 were given
TypeError f() takes 1 positional argument but 2 were given
TypeError f() takes 1 positional argument but 2 were given
TypeError f() takes 1 positional argument but 3 were given
TypeError f() takes 1 positional argument but 3 were given
TypeError f() takes 1 positional argument but 3 were given
TypeError f() takes 1 positional argument but 3 were given
TypeError f() takes 1 positional argument but 3 were given
TypeError f() takes 1 positional argument but 3 were given
TypeError f() takes 1 positional argument but 3 were given
TypeError f() takes 1 positional argument but 3 were given
TypeError f() takes 1 positional argument but 4 were given
TypeError f() takes 1 positional argument but 4 were given
TypeError f() takes 1 positional argument but 4 were given
TypeError f() takes 1 positional argument but 4 were given
TypeError f() takes 1 positional argument but 4 were given
TypeError f() takes 1 positional argument but 4 were given
TypeError f() takes 1 positional argument but 4 were given
TypeError f() takes 1 positional argument but 4 were given
TypeError f() takes 1 positional argument but 5 were given
TypeError f() takes 1 positional argument but 5 were given
TypeError f() takes 1 positional argument but 5 were given
TypeError f() takes 1 positional argument but 5 were given
TypeError f() takes 1 positional argument but 5 were given
TypeError f() takes 1 positional argument but 5 were given
TypeError f() takes 1 positional argument but 5 were given
TypeError f() takes 1 positional argument but 5 were given
TypeError f() takes 1 positional argument but 6 were given
TypeError f() takes 1 positional argument but 6 were given
TypeError f() takes 1 positional argument but 6 were given
TypeError f() takes 1 positional argument but 6 were given
TypeError f() takes 1 positional argument but 6 were given
TypeError f() takes 1 positional argument but 6 were given
TypeError f() takes 1 positional argument but 6 were given
TypeError f() takes 1 positional argument but 6 were given
''')

check_program('''def f(*args): return args
for args in [(), (0,), (0, 1), (0, 1, 2), (0, 1, 2, 3), (0, 1, 2, 3, 4), (0, 1, 2, 3, 4, 5)]:
    for kwargs in [{}, {'a': 11}, {'b': 22}, {'a': 11, 'b': 22}, {'zebra': 99}, {'zebra': 99, 'a': 11}, {'a': 11, 'zebra': 99}, {'c': 33, 'd': 44}]:
        try: print(f(*args, **kwargs))
        except TypeError as error: print(type(error).__name__, str(error))
''',
              '''()
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'c'
(0,)
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'c'
(0, 1)
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'c'
(0, 1, 2)
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'c'
(0, 1, 2, 3)
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'c'
(0, 1, 2, 3, 4)
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'c'
(0, 1, 2, 3, 4, 5)
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'b'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'a'
TypeError f() got an unexpected keyword argument 'c'
''')

check_program('''def f(*, a, b): return (a, b)
for args in [(), (0,), (0, 1), (0, 1, 2), (0, 1, 2, 3), (0, 1, 2, 3, 4), (0, 1, 2, 3, 4, 5)]:
    for kwargs in [{}, {'a': 11}, {'b': 22}, {'a': 11, 'b': 22}, {'zebra': 99}, {'zebra': 99, 'a': 11}, {'a': 11, 'zebra': 99}, {'c': 33, 'd': 44}]:
        try: print(f(*args, **kwargs))
        except TypeError as error: print(type(error).__name__, str(error))
''',
              '''TypeError f() missing 2 required keyword-only arguments: 'a' and 'b'
TypeError f() missing 1 required keyword-only argument: 'b'
TypeError f() missing 1 required keyword-only argument: 'a'
(11, 22)
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes 0 positional arguments but 1 was given
TypeError f() takes 0 positional arguments but 1 positional argument (and 1 keyword-only argument) were given
TypeError f() takes 0 positional arguments but 1 positional argument (and 1 keyword-only argument) were given
TypeError f() takes 0 positional arguments but 1 positional argument (and 2 keyword-only arguments) were given
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes 0 positional arguments but 2 were given
TypeError f() takes 0 positional arguments but 2 positional arguments (and 1 keyword-only argument) were given
TypeError f() takes 0 positional arguments but 2 positional arguments (and 1 keyword-only argument) were given
TypeError f() takes 0 positional arguments but 2 positional arguments (and 2 keyword-only arguments) were given
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes 0 positional arguments but 3 were given
TypeError f() takes 0 positional arguments but 3 positional arguments (and 1 keyword-only argument) were given
TypeError f() takes 0 positional arguments but 3 positional arguments (and 1 keyword-only argument) were given
TypeError f() takes 0 positional arguments but 3 positional arguments (and 2 keyword-only arguments) were given
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes 0 positional arguments but 4 were given
TypeError f() takes 0 positional arguments but 4 positional arguments (and 1 keyword-only argument) were given
TypeError f() takes 0 positional arguments but 4 positional arguments (and 1 keyword-only argument) were given
TypeError f() takes 0 positional arguments but 4 positional arguments (and 2 keyword-only arguments) were given
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes 0 positional arguments but 5 were given
TypeError f() takes 0 positional arguments but 5 positional arguments (and 1 keyword-only argument) were given
TypeError f() takes 0 positional arguments but 5 positional arguments (and 1 keyword-only argument) were given
TypeError f() takes 0 positional arguments but 5 positional arguments (and 2 keyword-only arguments) were given
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'c'
TypeError f() takes 0 positional arguments but 6 were given
TypeError f() takes 0 positional arguments but 6 positional arguments (and 1 keyword-only argument) were given
TypeError f() takes 0 positional arguments but 6 positional arguments (and 1 keyword-only argument) were given
TypeError f() takes 0 positional arguments but 6 positional arguments (and 2 keyword-only arguments) were given
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'zebra'
TypeError f() got an unexpected keyword argument 'c'
''')

check_program('''def f(a, *args, b=2, **kw): return (a, args, b, kw)
for args in [(), (0,), (0, 1), (0, 1, 2), (0, 1, 2, 3), (0, 1, 2, 3, 4), (0, 1, 2, 3, 4, 5)]:
    for kwargs in [{}, {'a': 11}, {'b': 22}, {'a': 11, 'b': 22}, {'zebra': 99}, {'zebra': 99, 'a': 11}, {'a': 11, 'zebra': 99}, {'c': 33, 'd': 44}]:
        try: print(f(*args, **kwargs))
        except TypeError as error: print(type(error).__name__, str(error))
''',
              '''TypeError f() missing 1 required positional argument: 'a'
(11, (), 2, {})
TypeError f() missing 1 required positional argument: 'a'
(11, (), 22, {})
TypeError f() missing 1 required positional argument: 'a'
(11, (), 2, {'zebra': 99})
(11, (), 2, {'zebra': 99})
TypeError f() missing 1 required positional argument: 'a'
(0, (), 2, {})
TypeError f() got multiple values for argument 'a'
(0, (), 22, {})
TypeError f() got multiple values for argument 'a'
(0, (), 2, {'zebra': 99})
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'a'
(0, (), 2, {'c': 33, 'd': 44})
(0, (1,), 2, {})
TypeError f() got multiple values for argument 'a'
(0, (1,), 22, {})
TypeError f() got multiple values for argument 'a'
(0, (1,), 2, {'zebra': 99})
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'a'
(0, (1,), 2, {'c': 33, 'd': 44})
(0, (1, 2), 2, {})
TypeError f() got multiple values for argument 'a'
(0, (1, 2), 22, {})
TypeError f() got multiple values for argument 'a'
(0, (1, 2), 2, {'zebra': 99})
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'a'
(0, (1, 2), 2, {'c': 33, 'd': 44})
(0, (1, 2, 3), 2, {})
TypeError f() got multiple values for argument 'a'
(0, (1, 2, 3), 22, {})
TypeError f() got multiple values for argument 'a'
(0, (1, 2, 3), 2, {'zebra': 99})
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'a'
(0, (1, 2, 3), 2, {'c': 33, 'd': 44})
(0, (1, 2, 3, 4), 2, {})
TypeError f() got multiple values for argument 'a'
(0, (1, 2, 3, 4), 22, {})
TypeError f() got multiple values for argument 'a'
(0, (1, 2, 3, 4), 2, {'zebra': 99})
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'a'
(0, (1, 2, 3, 4), 2, {'c': 33, 'd': 44})
(0, (1, 2, 3, 4, 5), 2, {})
TypeError f() got multiple values for argument 'a'
(0, (1, 2, 3, 4, 5), 22, {})
TypeError f() got multiple values for argument 'a'
(0, (1, 2, 3, 4, 5), 2, {'zebra': 99})
TypeError f() got multiple values for argument 'a'
TypeError f() got multiple values for argument 'a'
(0, (1, 2, 3, 4, 5), 2, {'c': 33, 'd': 44})
''')

check_program('''def f(a, /, b, *args, c, d=4, **kw): return (a, b, args, c, d, kw)
for args in [(), (0,), (0, 1), (0, 1, 2), (0, 1, 2, 3), (0, 1, 2, 3, 4), (0, 1, 2, 3, 4, 5)]:
    for kwargs in [{}, {'a': 11}, {'b': 22}, {'a': 11, 'b': 22}, {'zebra': 99}, {'zebra': 99, 'a': 11}, {'a': 11, 'zebra': 99}, {'c': 33, 'd': 44}]:
        try: print(f(*args, **kwargs))
        except TypeError as error: print(type(error).__name__, str(error))
''',
              '''TypeError f() missing 2 required positional arguments: 'a' and 'b'
TypeError f() missing 2 required positional arguments: 'a' and 'b'
TypeError f() missing 1 required positional argument: 'a'
TypeError f() missing 1 required positional argument: 'a'
TypeError f() missing 2 required positional arguments: 'a' and 'b'
TypeError f() missing 2 required positional arguments: 'a' and 'b'
TypeError f() missing 2 required positional arguments: 'a' and 'b'
TypeError f() missing 2 required positional arguments: 'a' and 'b'
TypeError f() missing 1 required positional argument: 'b'
TypeError f() missing 1 required positional argument: 'b'
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() missing 1 required positional argument: 'b'
TypeError f() missing 1 required positional argument: 'b'
TypeError f() missing 1 required positional argument: 'b'
TypeError f() missing 1 required positional argument: 'b'
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() got multiple values for argument 'b'
TypeError f() got multiple values for argument 'b'
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() missing 1 required keyword-only argument: 'c'
(0, 1, (), 33, 44, {})
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() got multiple values for argument 'b'
TypeError f() got multiple values for argument 'b'
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() missing 1 required keyword-only argument: 'c'
(0, 1, (2,), 33, 44, {})
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() got multiple values for argument 'b'
TypeError f() got multiple values for argument 'b'
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() missing 1 required keyword-only argument: 'c'
(0, 1, (2, 3), 33, 44, {})
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() got multiple values for argument 'b'
TypeError f() got multiple values for argument 'b'
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() missing 1 required keyword-only argument: 'c'
(0, 1, (2, 3, 4), 33, 44, {})
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() got multiple values for argument 'b'
TypeError f() got multiple values for argument 'b'
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() missing 1 required keyword-only argument: 'c'
TypeError f() missing 1 required keyword-only argument: 'c'
(0, 1, (2, 3, 4, 5), 33, 44, {})
''')
