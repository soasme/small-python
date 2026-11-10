# spec: PLS-315 20.2.5, 10.2.1, 13.3.4, 7.4.1
# description: Calling a class runs its metaclass's __call__, then
# __init__ with the new instance; a bound method passes its self first.
# A metaclass's __call__, which may loop and call type's, receives the class
# first, a subclass's too. Each holds whatever form the call takes inside a
# function.
from harness import *

class Meta(type):
    def __call__(cls, *args, **kwargs):
        return ('made', args, kwargs)

class Made(metaclass=Meta):
    def __init__(self, x=0):
        for i in range(2): pass

def made():
    args = [1]
    return Made(1), Made(*args), Made(1 + 1), Made(x=3), Made()

assert made() == (('made', (1,), {}), ('made', (1,), {}), ('made', (2,), {}),
                  ('made', (), {'x': 3}), ('made', (), {})), made()

class Point:
    def __init__(self, x, y):
        self.total = 0
        for v in (x, y): self.total += v

class Point3(Point):
    pass

def points():
    xs = [1, 2]
    return Point(1, 2).total, Point(*xs).total, Point(1 + 1, 3).total, Point3(4, 5).total

assert points() == (3, 3, 5, 9)

class Returning:
    def __init__(self, n):
        for i in range(n): pass
        return n

def returning(n):
    try:
        Returning(n)
    except TypeError as e:
        return str(e)

assert returning(1) == "__init__() should return None, not 'int'"

class Failing:
    def __init__(self):
        for i in range(1): pass
        raise KeyError('init')

def failing():
    try:
        Failing()
    except KeyError as e:
        return e.args

assert failing() == ('init',)

class Base:
    def name(self, suffix):
        for i in range(1): pass
        return 'base' + suffix
    @classmethod
    def kind(cls, n):
        for i in range(1): pass
        return cls.__name__ * n
    @staticmethod
    def plain(n):
        for i in range(1): pass
        return n + 1

class Derived(Base):
    def name(self, suffix):
        return 'derived/' + super().name(suffix)

def methods():
    d = Derived()
    bound = d.name
    kind = Derived.kind
    return bound('!'), kind(2), d.kind(1), Derived.plain(1), d.plain(2), (lambda: super(Derived, d).name('?'))()

assert methods() == ('derived/base!', 'DerivedDerived', 'Derived', 2, 3, 'base?'), methods()

# Keyword arguments to a class, a bound method and a metaclass's __call__.
class Keyed:
    def __init__(self, x=0, *, y=1):
        for i in range(1): pass
        self.v = (x, y)
    def m(self, a, b=2):
        for i in range(1): pass
        return (a, b)

def keyed():
    k = Keyed(1, y=5)
    bound = k.m
    return k.v, Keyed(x=3).v, bound(1, b=4), k.m(a=7), Made(z=1)

assert keyed() == ((1, 5), (3, 1), (1, 4), (7, 2), ('made', (), {'z': 1})), keyed()

def unexpected():
    try:
        Keyed(1, zz=2)
    except TypeError as e:
        return str(e)

assert unexpected() == "Keyed.__init__() got an unexpected keyword argument 'zz'", unexpected()

# An instance's class __call__, and never one the instance holds.
class Callable:
    def __init__(self, k): self.k = k
    def __call__(self, x=1, *, y=2):
        for i in range(1): pass
        return (self.k, x, y)

class CallableChild(Callable):
    pass

def instances():
    a = Callable('a')
    args = [5]
    out = [a(), a(3), a(*args), a(y=9), a(4, y=8), CallableChild('b')(7), (lambda: a(1))()]
    try:
        a(1, 2)
    except TypeError as e:
        out.append(str(e))
    a.__call__ = lambda: 'held'
    out.append(a(0))
    return out

assert instances() == [('a', 1, 2), ('a', 3, 2), ('a', 5, 2), ('a', 1, 9), ('a', 4, 8), ('b', 7, 2), ('a', 1, 2),
                       'Callable.__call__() takes from 1 to 2 positional arguments but 3 were given', ('a', 0, 2)], instances()

# A metaclass's __call__ that loops and calls type's, for a subclass too.
log = []

class Single(type):
    def __call__(cls, *args, **kwargs):
        for i in range(2): pass
        log.append((cls.__name__, args, kwargs))
        if "made" not in cls.__dict__:
            cls.made = super().__call__(*args, **kwargs)
        return cls.made

class Once(metaclass=Single):
    def __init__(self, x=0):
        for i in range(1): pass
        log.append(("init", x))

class Twice(Once):
    pass

class Narrow(type):
    def __call__(cls): return "narrow"

class Strict(metaclass=Narrow):
    pass

def singles():
    del log[:]
    args = [3]
    a, b, c = Once(1), Once(x=2), Twice(*args)
    out = [a is b, c is Twice.made, type(c).__name__, list(map(Twice, [4]))[0] is c, Strict()]
    try:
        Strict(1)
    except TypeError as e:
        out.append(str(e))
    return out + [list(log)]

expected = [True, True, "Twice", True, "narrow", "Narrow.__call__() takes 1 positional argument but 2 were given",
            [("Once", (1,), {}), ("init", 1), ("Once", (), {"x": 2}), ("Twice", (3,), {}), ("init", 3), ("Twice", (4,), {})]]
assert singles() == expected, singles()
del Once.made, Twice.made
assert singles() == expected, singles()
