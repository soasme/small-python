# spec: PLS-315 13.10
# description: Programs on comparisons, each with the output CPython 3.15 gives.
from harness import *

check_program('''calls = []
class Left(object):
    def __lt__(self, other):
        calls.append('Left__lt__')
        return NotImplemented
    def __le__(self, other):
        calls.append('Left__le__')
        return NotImplemented
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
    def __ne__(self, other):
        calls.append('Left__ne__')
        return NotImplemented
    def __gt__(self, other):
        calls.append('Left__gt__')
        return NotImplemented
    def __ge__(self, other):
        calls.append('Left__ge__')
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
['Right__gt__', 'Left__lt__']
TypeError
['Right__ge__', 'Left__le__']
False
['Right__eq__', 'Left__eq__']
True
['Right__ne__', 'Left__ne__']
TypeError
['Right__lt__', 'Left__gt__']
TypeError
['Right__le__', 'Left__ge__']
''')

check_program('''calls = []
class Left(object):
    def __lt__(self, other):
        calls.append('Left__lt__')
        return NotImplemented
    def __le__(self, other):
        calls.append('Left__le__')
        return NotImplemented
    def __eq__(self, other):
        calls.append('Left__eq__')
        return NotImplemented
    def __ne__(self, other):
        calls.append('Left__ne__')
        return NotImplemented
    def __gt__(self, other):
        calls.append('Left__gt__')
        return NotImplemented
    def __ge__(self, other):
        calls.append('Left__ge__')
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

check_program('''
nan = float('nan')
values = [slice(1), slice(1, 2), slice(1, 2, 3), slice(1, 2, 4), slice(None),
          slice(nan), slice(nan), slice(float('nan')), slice([], []), slice([1], [2])]
for a in values:
    for b in values:
        try: print(a < b)
        except TypeError: print('TypeError')
        try: print(a <= b)
        except TypeError: print('TypeError')
        try: print(a == b)
        except TypeError: print('TypeError')
        try: print(a != b)
        except TypeError: print('TypeError')
        try: print(a > b)
        except TypeError: print('TypeError')
        try: print(a >= b)
        except TypeError: print('TypeError')
''',
              '''False
True
True
False
False
True
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
False
False
False
True
False
False
False
False
False
True
False
False
False
False
False
True
False
False
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
False
True
True
False
False
True
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
False
True
True
False
False
True
True
True
False
True
False
False
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
False
False
False
True
True
True
False
True
True
False
False
True
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
False
True
True
False
False
True
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
False
False
False
True
False
False
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
False
True
True
False
False
True
False
True
True
False
False
True
False
False
False
True
False
False
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
False
False
False
True
False
False
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
False
True
True
False
False
True
False
True
True
False
False
True
False
False
False
True
False
False
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
False
False
False
True
False
False
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
False
False
False
True
False
False
False
False
False
True
False
False
False
True
True
False
False
True
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
False
True
True
False
False
True
True
True
False
True
False
False
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
TypeError
TypeError
False
True
TypeError
TypeError
False
False
False
True
True
True
False
True
True
False
False
True
''')
