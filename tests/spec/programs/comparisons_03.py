# spec: PLS-315 13.10
# description: Programs on comparisons, each with the output CPython 3.15 gives.
from harness import *

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
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
['Left__eq__', 'Left__eq__']
True
['Right__ne__', 'Left__eq__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
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
['Left__eq__', 'Left__eq__']
['value']
['Right__ne__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
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
['Left__eq__', 'Right__eq__']
True
['Left__eq__', 'Right__ne__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
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
['Left__eq__', 'Right__eq__']
['value']
['Left__eq__', 'Right__ne__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
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
['Right__eq__', 'Left__eq__']
True
['Right__ne__', 'Left__eq__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
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
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
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
['Left__eq__']
True
['Left__eq__']
TypeError
['Right__lt__']
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
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
['Left__eq__']
True
['Left__eq__']
['value']
['Right__lt__']
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
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
['Left__eq__', 'Left__eq__']
True
['Left__eq__', 'Left__eq__']
TypeError
['Right__lt__']
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
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
['Left__eq__', 'Left__eq__']
True
['Left__eq__', 'Left__eq__']
['value']
['Right__lt__']
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
class Right(object):
    def __gt__(self, other):
        calls.append('Right__gt__')
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
['Right__gt__']
TypeError
[]
False
['Left__eq__']
True
['Left__eq__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
class Right(object):
    def __gt__(self, other):
        calls.append('Right__gt__')
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
              '''['value']
['Right__gt__']
TypeError
[]
False
['Left__eq__']
True
['Left__eq__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
class Right(Left):
    def __gt__(self, other):
        calls.append('Right__gt__')
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
['Right__gt__']
TypeError
[]
False
['Left__eq__', 'Left__eq__']
True
['Left__eq__', 'Left__eq__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
class Right(Left):
    def __gt__(self, other):
        calls.append('Right__gt__')
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
              '''['value']
['Right__gt__']
TypeError
[]
False
['Left__eq__', 'Left__eq__']
True
['Left__eq__', 'Left__eq__']
TypeError
[]
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
class Right(object):
    def __le__(self, other):
        calls.append('Right__le__')
        return NotImplemented
    def __ge__(self, other):
        calls.append('Right__ge__')
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
['Right__ge__']
False
['Left__eq__']
True
['Left__eq__']
TypeError
[]
TypeError
['Right__le__']
''')

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
class Right(object):
    def __le__(self, other):
        calls.append('Right__le__')
        return ['value']
    def __ge__(self, other):
        calls.append('Right__ge__')
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
['value']
['Right__ge__']
False
['Left__eq__']
True
['Left__eq__']
TypeError
[]
['value']
['Right__le__']
''')

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
class Right(Left):
    def __le__(self, other):
        calls.append('Right__le__')
        return NotImplemented
    def __ge__(self, other):
        calls.append('Right__ge__')
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
['Right__ge__']
False
['Left__eq__', 'Left__eq__']
True
['Left__eq__', 'Left__eq__']
TypeError
[]
TypeError
['Right__le__']
''')

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
class Right(Left):
    def __le__(self, other):
        calls.append('Right__le__')
        return ['value']
    def __ge__(self, other):
        calls.append('Right__ge__')
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
['value']
['Right__ge__']
False
['Left__eq__', 'Left__eq__']
True
['Left__eq__', 'Left__eq__']
TypeError
[]
['value']
['Right__le__']
''')

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
class Right(object):
    def __lt__(self, other):
        calls.append('Right__lt__')
        return NotImplemented
    def __le__(self, other):
        calls.append('Right__le__')
        return NotImplemented
    def __eq__(self, other):
        calls.append('Right__eq__')
        return NotImplemented
    def __ne__(self, other):
        calls.append('Right__ne__')
        return NotImplemented
    def __gt__(self, other):
        calls.append('Right__gt__')
        return NotImplemented
    def __ge__(self, other):
        calls.append('Right__ge__')
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
['Right__gt__']
TypeError
['Right__ge__']
False
['Left__eq__', 'Right__eq__']
True
['Left__eq__', 'Right__ne__']
TypeError
['Right__lt__']
TypeError
['Right__le__']
''')

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
class Right(object):
    def __lt__(self, other):
        calls.append('Right__lt__')
        return ['value']
    def __le__(self, other):
        calls.append('Right__le__')
        return ['value']
    def __eq__(self, other):
        calls.append('Right__eq__')
        return ['value']
    def __ne__(self, other):
        calls.append('Right__ne__')
        return ['value']
    def __gt__(self, other):
        calls.append('Right__gt__')
        return ['value']
    def __ge__(self, other):
        calls.append('Right__ge__')
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
              '''['value']
['Right__gt__']
['value']
['Right__ge__']
['value']
['Left__eq__', 'Right__eq__']
['value']
['Left__eq__', 'Right__ne__']
['value']
['Right__lt__']
['value']
['Right__le__']
''')
