# spec: PLS-315 13.10
# description: Programs on comparisons, each with the output CPython 3.15 gives.
from harness import *

check_program('''print(1 < 2 < 3, 1 < 2 > 3, 3 > 2 >= 2, 1 == True, None is None)
''',
              '''True False True True True
''')

check_program('''if False:
    print('no')
elif 2 > 1:
    print('yes')
else:
    print('no')
''',
              '''yes
''')

check_program('''calls = []
class Left(object):
    pass
class Right(object):
    pass
a = Left(); b = Right()
calls = []
try: print(a < b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a <= b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a == b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a != b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a > b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a >= b)
except TypeError: print('TypeError')
print(calls)
''',
              '''TypeError
[]
TypeError
[]
False
[]
True
[]
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    pass
class Right(Left):
    pass
a = Left(); b = Right()
calls = []
try: print(a < b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a <= b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a == b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a != b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a > b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a >= b)
except TypeError: print('TypeError')
print(calls)
''',
              '''TypeError
[]
TypeError
[]
False
[]
True
[]
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    pass
class Right(object):
    def __eq__(self, other):
        calls.append('Right__eq__')
        return NotImplemented
a = Left(); b = Right()
calls = []
try: print(a < b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a <= b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a == b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a != b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a > b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a >= b)
except TypeError: print('TypeError')
print(calls)
''',
              '''TypeError
[]
TypeError
[]
False
['Right__eq__']
True
['Right__eq__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    pass
class Right(object):
    def __eq__(self, other):
        calls.append('Right__eq__')
        return ['value']
a = Left(); b = Right()
calls = []
try: print(a < b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a <= b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a == b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a != b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a > b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a >= b)
except TypeError: print('TypeError')
print(calls)
''',
              '''TypeError
[]
TypeError
[]
['value']
['Right__eq__']
False
['Right__eq__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    pass
class Right(Left):
    def __eq__(self, other):
        calls.append('Right__eq__')
        return NotImplemented
a = Left(); b = Right()
calls = []
try: print(a < b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a <= b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a == b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a != b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a > b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a >= b)
except TypeError: print('TypeError')
print(calls)
''',
              '''TypeError
[]
TypeError
[]
False
['Right__eq__']
True
['Right__eq__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    pass
class Right(Left):
    def __eq__(self, other):
        calls.append('Right__eq__')
        return ['value']
a = Left(); b = Right()
calls = []
try: print(a < b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a <= b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a == b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a != b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a > b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a >= b)
except TypeError: print('TypeError')
print(calls)
''',
              '''TypeError
[]
TypeError
[]
['value']
['Right__eq__']
False
['Right__eq__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    pass
class Right(object):
    def __ne__(self, other):
        calls.append('Right__ne__')
        return NotImplemented
a = Left(); b = Right()
calls = []
try: print(a < b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a <= b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a == b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a != b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a > b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a >= b)
except TypeError: print('TypeError')
print(calls)
''',
              '''TypeError
[]
TypeError
[]
False
[]
True
['Right__ne__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    pass
class Right(object):
    def __ne__(self, other):
        calls.append('Right__ne__')
        return ['value']
a = Left(); b = Right()
calls = []
try: print(a < b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a <= b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a == b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a != b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a > b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a >= b)
except TypeError: print('TypeError')
print(calls)
''',
              '''TypeError
[]
TypeError
[]
False
[]
['value']
['Right__ne__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    pass
class Right(Left):
    def __ne__(self, other):
        calls.append('Right__ne__')
        return NotImplemented
a = Left(); b = Right()
calls = []
try: print(a < b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a <= b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a == b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a != b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a > b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a >= b)
except TypeError: print('TypeError')
print(calls)
''',
              '''TypeError
[]
TypeError
[]
False
[]
True
['Right__ne__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    pass
class Right(Left):
    def __ne__(self, other):
        calls.append('Right__ne__')
        return ['value']
a = Left(); b = Right()
calls = []
try: print(a < b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a <= b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a == b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a != b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a > b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a >= b)
except TypeError: print('TypeError')
print(calls)
''',
              '''TypeError
[]
TypeError
[]
False
[]
['value']
['Right__ne__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    pass
class Right(object):
    def __eq__(self, other):
        calls.append('Right__eq__')
        return NotImplemented
    def __ne__(self, other):
        calls.append('Right__ne__')
        return NotImplemented
a = Left(); b = Right()
calls = []
try: print(a < b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a <= b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a == b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a != b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a > b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a >= b)
except TypeError: print('TypeError')
print(calls)
''',
              '''TypeError
[]
TypeError
[]
False
['Right__eq__']
True
['Right__ne__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    pass
class Right(object):
    def __eq__(self, other):
        calls.append('Right__eq__')
        return ['value']
    def __ne__(self, other):
        calls.append('Right__ne__')
        return ['value']
a = Left(); b = Right()
calls = []
try: print(a < b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a <= b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a == b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a != b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a > b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a >= b)
except TypeError: print('TypeError')
print(calls)
''',
              '''TypeError
[]
TypeError
[]
['value']
['Right__eq__']
['value']
['Right__ne__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    pass
class Right(Left):
    def __eq__(self, other):
        calls.append('Right__eq__')
        return NotImplemented
    def __ne__(self, other):
        calls.append('Right__ne__')
        return NotImplemented
a = Left(); b = Right()
calls = []
try: print(a < b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a <= b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a == b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a != b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a > b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a >= b)
except TypeError: print('TypeError')
print(calls)
''',
              '''TypeError
[]
TypeError
[]
False
['Right__eq__']
True
['Right__ne__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    pass
class Right(Left):
    def __eq__(self, other):
        calls.append('Right__eq__')
        return ['value']
    def __ne__(self, other):
        calls.append('Right__ne__')
        return ['value']
a = Left(); b = Right()
calls = []
try: print(a < b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a <= b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a == b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a != b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a > b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a >= b)
except TypeError: print('TypeError')
print(calls)
''',
              '''TypeError
[]
TypeError
[]
['value']
['Right__eq__']
['value']
['Right__ne__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    pass
class Right(object):
    def __lt__(self, other):
        calls.append('Right__lt__')
        return NotImplemented
a = Left(); b = Right()
calls = []
try: print(a < b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a <= b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a == b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a != b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a > b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a >= b)
except TypeError: print('TypeError')
print(calls)
''',
              '''TypeError
[]
TypeError
[]
False
[]
True
[]
TypeError
['Right__lt__']
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    pass
class Right(object):
    def __lt__(self, other):
        calls.append('Right__lt__')
        return ['value']
a = Left(); b = Right()
calls = []
try: print(a < b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a <= b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a == b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a != b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a > b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a >= b)
except TypeError: print('TypeError')
print(calls)
''',
              '''TypeError
[]
TypeError
[]
False
[]
True
[]
['value']
['Right__lt__']
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    pass
class Right(Left):
    def __lt__(self, other):
        calls.append('Right__lt__')
        return NotImplemented
a = Left(); b = Right()
calls = []
try: print(a < b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a <= b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a == b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a != b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a > b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a >= b)
except TypeError: print('TypeError')
print(calls)
''',
              '''TypeError
[]
TypeError
[]
False
[]
True
[]
TypeError
['Right__lt__']
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    pass
class Right(Left):
    def __lt__(self, other):
        calls.append('Right__lt__')
        return ['value']
a = Left(); b = Right()
calls = []
try: print(a < b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a <= b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a == b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a != b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a > b)
except TypeError: print('TypeError')
print(calls)
calls = []
try: print(a >= b)
except TypeError: print('TypeError')
print(calls)
''',
              '''TypeError
[]
TypeError
[]
False
[]
True
[]
['value']
['Right__lt__']
TypeError
[]
''')
