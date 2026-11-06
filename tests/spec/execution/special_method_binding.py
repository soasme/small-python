# spec: PLS-315 7.4.3, 7.3.3, 10.2.1, 15.5, 16.5, 13.3.4
# description: A special method, initializer, allocator, decorator or bound
# method whose parameters do not fit the arguments its caller passes raises
# the TypeError of binding them, inside functions that call and loop as at
# module level; nothing of the failed call runs.
from harness import *

ran = []

def one():
    ran.append("one")
    return 1

class Narrow:
    def __add__(self): ran.append("add")
    def __lt__(self): ran.append("lt")
    def __getitem__(self): ran.append("getitem")
    def __contains__(self): ran.append("contains")
    def __bool__(self, extra): ran.append("bool")
    def __enter__(self, extra): ran.append("enter")
    def __exit__(self, *exc): ran.append("exit")
    def __iter__(self):
        for _ in range(1): pass
        return 1
    def __setitem__(self):
        for _ in range(1): pass
    def method(self): ran.append("method")
    def __repr__(self):
        for _ in range(2): pass
        return "narrow"
    @property
    def wide(self, extra): ran.append("wide")

class Init:
    def __init__(self): ran.append("init")

class Allocating:
    def __new__(cls): ran.append("new")

def nothing():
    ran.append("decorator")

def loop(n):
    for x in n: one()
    return []

def message(f):
    try:
        f()
    except TypeError as e:
        return str(e)
    return None

def checks():
    n = Narrow()
    bound = n.method
    results = [
        message(lambda: n + one()),
        message(lambda: n < one()),
        message(lambda: n[one()]),
        message(lambda: one() in n),
        message(lambda: [one() for x in loop(n)]),
        message(lambda: n.wide + one()),
        message(lambda: bound(one())),
        message(lambda: Narrow().method(1)),
        message(lambda: Init(one())),
        message(lambda: Allocating(1)),
        str(n) + str(one()),
    ]
    try:
        n[0] = one()
    except TypeError as e:
        results.append(str(e))
    try:
        if n: one()
    except TypeError as e:
        results.append(str(e))
    try:
        with n: one()
    except TypeError as e:
        results.append(str(e))
    try:
        @nothing
        def decorated(): one()
    except TypeError as e:
        results.append(str(e))
    return results

expected = [
    "Narrow.__add__() takes 1 positional argument but 2 were given",
    "Narrow.__lt__() takes 1 positional argument but 2 were given",
    "Narrow.__getitem__() takes 1 positional argument but 2 were given",
    "Narrow.__contains__() takes 1 positional argument but 2 were given",
    "Narrow.__iter__() must return an iterator, not int",
    "Narrow.wide() missing 1 required positional argument: 'extra'",
    "Narrow.method() takes 1 positional argument but 2 were given",
    "Narrow.method() takes 1 positional argument but 2 were given",
    "Init.__init__() takes 1 positional argument but 2 were given",
    "Allocating.__new__() takes 1 positional argument but 2 were given",
    "narrow1",
    "Narrow.__setitem__() takes 1 positional argument but 3 were given",
    "Narrow.__bool__() missing 1 required positional argument: 'extra'",
    "Narrow.__enter__() missing 1 required positional argument: 'extra'",
    "nothing() takes 0 positional arguments but 1 was given",
]
assert_eq(checks(), expected)
assert_eq([r for r in ran if r != "one"], [])

# A class header that fails makes no class.
def header():
    try:
        class Failing(Missing):
            for i in range(2): one()
    except NameError as e:
        return str(e)

assert_eq(header(), "name 'Missing' is not defined")
