# spec: PLS-315 10.3
# description: Programs on descriptors and properties, each with the output CPython 3.15 gives.
from harness import *

check_program('''calls = []
class Descriptor:
    def __delete__(self, instance): calls.append('descriptor')
class C:
    field = Descriptor()
    @property
    def value(self): return 42
    @value.deleter
    def value(self): calls.append('property')
c = C()
delattr(c, 'field')
del c.field
delattr(c, 'value')
del c.value
c.extra = 1
print(delattr(c, 'extra'), calls)
''',
              '''None ['descriptor', 'descriptor', 'property', 'property']
''')

check_program('''class C:
    @property
    def x(self):
        'the value'
        return self._x
    @x.setter
    def x(self, value):
        self._x = value
    @x.deleter
    def x(self):
        del self._x
c = C()
c.x = 13
print(c.x, C.x.__doc__, C.x.fget.__name__, C.x.fset.__name__)
del c.x
print(hasattr(c, 'x'), C.x.fdel.__name__)
''',
              '''13 the value x x
False x
''')

check_program('''class Descriptor:
    def __get__(self, obj, owner):
        if obj is None:
            return owner.__name__
        return obj._value
    def __set__(self, obj, value):
        obj._value = value + 1
    def __delete__(self, obj):
        del obj._value
class C:
    x = Descriptor()
c = C()
c.x = 20
print(C.x, c.x)
del c.x
print(hasattr(c, 'x'))
''',
              '''C 21
False
''')

check_program('''class Descriptor:
    def __get__(self, obj, owner):
        return 10
class C:
    x = Descriptor()
c = C()
print(c.x)
c.x = 12
print(c.x, C.x)
del c.x
print(c.x)
''',
              '''10
12 10
10
''')

check_program('''class C:
    def __getattr__(self, name): return 'missing:' + name
    @property
    def x(self): raise AttributeError('unavailable')
print(C().x, C().y)
print(list(map(lambda x, y: x+y, [1, 2, 3], [4, 5])))
def stop(x):
    if x == 1: raise StopIteration
    return x
m = map(stop, [1, 2])
print(next(m, 'stop'), next(m))
''',
              '''missing:x missing:y
[5, 7]
stop 2
''')

check_program('''class C:
    @property
    def x(self): return 1
c = C(); c.x = 2
''',
              '''AttributeError: property 'x' of 'C' object has no setter
''')

check_program('''class C:
    @property
    def x(self): return 1
c = C(); del c.x
''',
              '''AttributeError: property 'x' of 'C' object has no deleter
''')
