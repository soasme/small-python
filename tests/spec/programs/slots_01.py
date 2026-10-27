# spec: PLS-315 10.1
# description: Programs on slots, each with the output CPython 3.15 gives.
from harness import *

check_program('''class A:
    __slots__ = ("x", "y")
print(sorted(A.__dict__))
class B: pass
print(sorted(B.__dict__), "__name__" in dir(B), B().__weakref__)
''',
              '''['__doc__', '__firstlineno__', '__module__', '__slots__', '__static_attributes__', 'x', 'y']
['__dict__', '__doc__', '__firstlineno__', '__module__', '__static_attributes__', '__weakref__'] False None
''')
