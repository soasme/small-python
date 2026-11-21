# spec: PLS-315 7.3.4
# description: When one object is both a class's __getattribute__ and its
# __getattr__, an AttributeError from the first call is followed by the
# second, for a function and for a descriptor whose Python __get__ gives
# a closure, through attribute reads and getattr with or without a
# default.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
def f(self, name):
    for _ in (): pass
    log.append(name)
    if len(log) < 2: raise AttributeError(name)
    return "second"
class P:
    __getattribute__ = __getattr__ = f
emit(P().x, log)
log.clear(); emit(getattr(P(), "y"), log)
class Descriptor(object):
    counter = 0
    def __get__(self, obj, objtype=None):
        def getter(name):
            self.counter += 1
            raise AttributeError(name)
        return getter
descr = Descriptor()
class C(object):
    __getattribute__ = descr
    __getattr__ = descr
for read in (lambda: C().attr, lambda: getattr(C(), "attr"), lambda: getattr(C(), "attr", 5)):
    try: emit(read())
    except AttributeError as e: emit("ae", e)
emit(descr.counter)
EXPECTED = [
    "second ['x', 'x']",
    "second ['y', 'y']",
    'ae attr',
    'ae attr',
    '5',
    '6',
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
