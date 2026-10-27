# spec: PLS-315 13.14
# description: Programs on lambdas, each with the output CPython 3.15 gives.
from harness import *

check_program('''print(eval("-" * 3001 + "1"), eval("not " * 3000 + "1"))
f = eval("lambda: " * 1000 + "1")
for i in range(1000): f = f()
print(f)
print(len(eval("[" * 199 + "]" * 199)))
x = eval("[" * 199 + "]" * 199)
print(repr(x)[:10])
''',
              '''-1 True
1
1
[[[[[[[[[[
''')

check_program('''from __future__ import annotations
def f(x: int, *a: List[ int ], y: "q" = 1, **k: (a, b)) -> lambda: 1: pass
print(f.__annotations__, callable(f.__annotate__))
class A:
    y: List[int]
    z: int = 3
    if 1:
        w: {1: 2, **d}
print(A.__annotations__, A.__annotate__, A.__dict__.get("__annotations__"))
x: 1 + 2 * 3
print(__annotations__, "__annotate__" in globals())

print(__annotate__ if "__annotate__" in globals() else None)
''',
              '''{'x': 'int', 'a': 'List[int]', 'y': "'q'", 'k': '(a, b)', 'return': 'lambda: 1'} True
{'y': 'List[int]', 'z': 'int', 'w': '{1: 2, **d}'} None {'y': 'List[int]', 'z': 'int', 'w': '{1: 2, **d}'}
{'x': '1 + 2 * 3'} False
None
''')

check_program('''def f(a, /, b=2, *args, c=3, **kw):
    return a, b, args, c, kw
print(f(1, 4, 5, 6, c=7, a=8, d=9))
print(f(*(1,), **{'b': 4, 'c': 5}))
def remember(x, items=[]):
    items.append(x)
    return items
print(remember(1), remember(2))
print((lambda a, *, b=2: a+b)(3, b=4))
''',
              '''(1, 4, (5, 6), 7, {'a': 8, 'd': 9})
(1, 4, (), 5, {})
[1, 2] [1, 2]
7
''')

check_program('''class Base:
    @classmethod
    def cls(cls, x=4):
        return cls.__name__, x
    @staticmethod
    def stat(x=5):
        return x
    def instance(self):
        return self
class Child(Base):
    pass
b = Base()
c = Child()
print(Base.cls(), b.cls(x=7), Child.cls(), c.cls())
print(Base.stat(), b.stat(x=2), Child.stat(9), c.stat())
print(c.cls.__self__ is Child, c.instance.__self__ is c)
sm = staticmethod(lambda x: x + 1)
print(sm(10), sm.__func__ is sm.__wrapped__, callable(sm), callable(classmethod(lambda x: x)))
''',
              '''('Base', 4) ('Base', 7) ('Child', 4) ('Child', 4)
5 2 9 5
True True
11 True True False
''')
