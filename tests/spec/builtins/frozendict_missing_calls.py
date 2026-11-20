# spec: PLS-315 26.2, 26.1.2
# description: frozendict.__getitem__ called explicitly on a frozendict
# subclass's instance of an absent key calls the class's Python
# __missing__, its result or error the call's, as subscription does; a
# present key is found, a subclass with no __missing__ raises KeyError,
# an unhashable key TypeError, and a dict or a dict subclass's instance
# is refused by frozendict's method as a frozendict is by dict's; and so
# inside a generator.
from harness import assert_eq

log = []
class M(frozendict):
    def __missing__(self, key):
        for _ in (): pass
        log.append(key)
        if key == "bad": raise LookupError("no " + key)
        return ("missing", key)
class N(frozendict): pass
class D(dict):
    def __missing__(self, key):
        for _ in (): pass
        log.append(("D", key)); return 0
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
m = M(a=1)
CASES = [
    (lambda: frozendict.__getitem__(m, 7), (('missing', 7), [7])),
    (lambda: frozendict.__getitem__(m, 'a'), (1, [])),
    (lambda: frozendict.__getitem__(m, 'bad'), (('LookupError', 'no bad'), ['bad'])),
    (lambda: m.__getitem__(7), (('missing', 7), [7])),
    (lambda: m[7], (('missing', 7), [7])),
    (lambda: frozendict.__getitem__(N(), 7), (('KeyError', '7'), [])),
    (lambda: frozendict.__getitem__(D(), 7), (('TypeError', "descriptor '__getitem__' for 'frozendict' objects doesn't apply to a 'D' object"), [])),
    (lambda: dict.__getitem__(m, 7), (('TypeError', "descriptor '__getitem__' for 'dict' objects doesn't apply to a 'M' object"), [])),
    (lambda: dict.__getitem__(D(), 7), (0, [('D', 7)])),
    (lambda: frozendict.__getitem__(m, []), (('TypeError', "cannot use 'list' as a frozendict key (unhashable type: 'list')"), [])),
    (lambda: list(map(frozendict.__getitem__, [m, m], [1, 'a'])), ([('missing', 1), 1], [1])),
]
for i, (f, expected) in enumerate(CASES):
    assert_eq(run(f), expected, str(i))
def g(): yield frozendict.__getitem__(m, 8)
assert_eq(run(lambda: next(g())), (('missing', 8), [8]))
