# spec: PLS-315 16.4.1, 16.4.2, 16.4.3
# description: A class body that loops and calls runs its statements in
# order in the class namespace, the mapping __prepare__ gave, before the
# metaclass makes the class; what the body raises propagates and makes no
# class; methods it defines see __class__; a comprehension in it sees the
# class's names only in its first iterable.
from harness import *

log = []

def note(x):
    log.append(x)
    return x

class Counted:
    n = 0
    while n < 5:
        n += 1
    items = [note(i) for i in range(3)]
    total = sum(items)
    doubled = [x * 2 for x in items]
    def method(self):
        return __class__
    def __eq__(self, other):
        return super().__eq__(other)

assert (Counted.n, Counted.items, Counted.total, Counted.doubled) == (5, [0, 1, 2], 3, [0, 2, 4])
assert log == [0, 1, 2]
assert Counted().method() is Counted
one = Counted()
assert (one == one, one == Counted()) == (True, False)

class Recording(dict):
    def __init__(self):
        super().__init__()
        self.order = []
    def __setitem__(self, key, value):
        self.order.append(key)
        super().__setitem__(key, value)

class Meta(type):
    @classmethod
    def __prepare__(mcs, name, bases):
        return Recording()
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, dict(namespace))
        cls.order = [k for k in namespace.order if not k.startswith('__')]
        return cls

class Ordered(metaclass=Meta):
    for i in range(2):
        note(i)
    a = note('a')
    b = len('bb')

assert Ordered.order == ['i', 'i', 'a', 'b'], Ordered.order
assert (Ordered.a, Ordered.b, Ordered.i) == ('a', 2, 1)

def failing():
    try:
        class Broken:
            for i in range(3):
                if i == 2:
                    raise KeyError(i)
    except KeyError as e:
        return e.args, 'Broken' in locals()

assert failing() == ((2,), False)

def inner(k):
    class Local:
        values = [k * j for j in range(k)]
        size = len(values)
    return Local.values, Local.size, Local.__qualname__

assert inner(3) == ([0, 3, 6], 3, 'inner.<locals>.Local')

class Scoped:
    base = 10
    firsts = [x for x in range(base)][:2]
    try:
        hidden = [base for _ in range(1)]
    except NameError as e:
        message = str(e)

assert Scoped.firsts == [0, 1]
assert Scoped.message == "name 'base' is not defined", Scoped.message

# A body with annotations loops over a Python iterator the same way.
class Countdown:
    def __init__(self, n): self.n = n
    def __iter__(self): return self
    def __next__(self):
        if not self.n: raise StopIteration
        self.n -= 1
        return self.n

class Annotated:
    total: int = 0
    for item in Countdown(3):
        total += item

assert (Annotated.total, Annotated.item, Annotated.__annotations__) == (3, 0, {"total": int})
