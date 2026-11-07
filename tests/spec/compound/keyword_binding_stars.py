# spec: PLS-315 7.4.3
# description: With *args or **kwargs, keywords bind to the named
# parameters, the rest go to a new **kwargs in call order (a
# positional-only name among them), *args takes the positional arguments
# past the named ones or is a new empty tuple, and defaults fill the
# others; each call gets
# fresh containers, and unmatched, repeated or missing names still raise,
# on a function's first call as on later ones.
from harness import *

def full(a, b=2, *args, c, d=4, **kw): return (a, b, args, c, d, kw)
def posonly(p, /, q=0, **kw): return (p, q, kw)
def stars(*args, **kw): return (args, kw)
def no_rest(a, *args, b): return (a, args, b)
def mutate(**kw):
    kw["seen"] = True
    return kw

def calls():
    out = []
    for _ in range(2):
        out.append(full(1, c=3))
        out.append(full(1, 5, c=3, z=1, y=2))
        out.append(full(c=0, a=1, d=9, e=8))
        out.append(posonly(1, p=2, r=3))
        out.append(posonly(1, q=2))
        out.append(stars(x=1))
        out.append(stars())
        out.append(no_rest(1, b=2))
        out.append(mutate(x=1))
        out.append(full(1, 2, 3, 4, c=5, w=6))
        out.append(stars(1, 2, k=3))
        out.append(no_rest(1, 2, 3, b=4))
    for f in (lambda: full(1, a=2, c=3), lambda: full(1), lambda: no_rest(b=1),
              lambda: posonly(q=1), lambda: no_rest(1, c=2, b=3),
              lambda: no_rest(1, 2, a=3, b=4), lambda: no_rest(1, 2, 3)):
        try:
            f()
        except TypeError as e:
            out.append(str(e))
    return out

once = [(1, 2, (), 3, 4, {}), (1, 5, (), 3, 4, {"z": 1, "y": 2}), (1, 2, (), 0, 9, {"e": 8}),
        (1, 0, {"p": 2, "r": 3}), (1, 2, {}), ((), {"x": 1}), ((), {}), (1, (), 2),
        {"x": 1, "seen": True}, (1, 2, (3, 4), 5, 4, {"w": 6}), ((1, 2), {"k": 3}), (1, (2, 3), 4)]
expected = once + once + [
    "full() got multiple values for argument 'a'",
    "full() missing 1 required keyword-only argument: 'c'",
    "no_rest() missing 1 required positional argument: 'a'",
    "posonly() missing 1 required positional argument: 'p'",
    "no_rest() got an unexpected keyword argument 'c'",
    "no_rest() got multiple values for argument 'a'",
    "no_rest() missing 1 required keyword-only argument: 'b'"]
assert_eq(calls(), expected)
assert_eq(list(full(1, c=3, y=1, x=2)[5]), ["y", "x"])
assert_eq(stars(**{"b": 1, "a": 2}), ((), {"b": 1, "a": 2}))

def first(a="d_a", /, b="d_b", *args): return (a, b, args)
try:
    first("p1", "p2", "p3", b="k_b")
except TypeError as e:
    assert_eq(str(e), "first() got multiple values for argument 'b'")
else:
    raise AssertionError("first() bound 'b' twice")
