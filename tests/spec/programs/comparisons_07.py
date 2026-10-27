# spec: PLS-315 13.10
# description: Programs on comparisons, each with the output CPython 3.15 gives.
from harness import *

check_program('''calls = []
class Left(object):
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
    def __ne__(self, other):
        calls.append('Left__ne__')
        return NotImplemented
class Right(Left):
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
['Right__eq__', 'Left__eq__']
True
['Right__ne__', 'Left__ne__']
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
    def __ne__(self, other):
        calls.append('Left__ne__')
        return NotImplemented
class Right(Left):
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
['Right__eq__']
['value']
['Right__ne__']
['value']
['Right__lt__']
['value']
['Right__le__']
''')

check_program('''calls = []
class Left(object):
    def __lt__(self, other):
        calls.append('Left__lt__')
        return NotImplemented
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
['Left__lt__']
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
    def __lt__(self, other):
        calls.append('Left__lt__')
        return NotImplemented
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
['Left__lt__']
TypeError
[]
False
[]
True
[]
TypeError
['Left__lt__']
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __lt__(self, other):
        calls.append('Left__lt__')
        return NotImplemented
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
['Left__lt__']
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
    def __lt__(self, other):
        calls.append('Left__lt__')
        return NotImplemented
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
['Left__lt__']
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
    def __lt__(self, other):
        calls.append('Left__lt__')
        return NotImplemented
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
['Left__lt__']
TypeError
[]
False
['Right__eq__']
True
['Right__eq__']
TypeError
['Left__lt__']
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __lt__(self, other):
        calls.append('Left__lt__')
        return NotImplemented
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
['Left__lt__']
TypeError
[]
['value']
['Right__eq__']
False
['Right__eq__']
TypeError
['Left__lt__']
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __lt__(self, other):
        calls.append('Left__lt__')
        return NotImplemented
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
['Left__lt__']
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
    def __lt__(self, other):
        calls.append('Left__lt__')
        return NotImplemented
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
['Left__lt__']
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
    def __lt__(self, other):
        calls.append('Left__lt__')
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
['Left__lt__']
TypeError
[]
False
[]
True
['Right__ne__']
TypeError
['Left__lt__']
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __lt__(self, other):
        calls.append('Left__lt__')
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
['Left__lt__']
TypeError
[]
False
[]
['value']
['Right__ne__']
TypeError
['Left__lt__']
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __lt__(self, other):
        calls.append('Left__lt__')
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
['Left__lt__']
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
    def __lt__(self, other):
        calls.append('Left__lt__')
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
['Left__lt__']
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
    def __lt__(self, other):
        calls.append('Left__lt__')
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
['Left__lt__']
TypeError
[]
False
['Right__eq__']
True
['Right__ne__']
TypeError
['Left__lt__']
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __lt__(self, other):
        calls.append('Left__lt__')
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
['Left__lt__']
TypeError
[]
['value']
['Right__eq__']
['value']
['Right__ne__']
TypeError
['Left__lt__']
TypeError
[]
''')

check_program('''calls = []
class Left(object):
    def __lt__(self, other):
        calls.append('Left__lt__')
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
['Left__lt__']
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
    def __lt__(self, other):
        calls.append('Left__lt__')
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
['Left__lt__']
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
    def __lt__(self, other):
        calls.append('Left__lt__')
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
['Left__lt__']
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
    def __lt__(self, other):
        calls.append('Left__lt__')
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
['Left__lt__']
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
