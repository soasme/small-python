# spec: PLS-315 7.4.3
# description: A keyword argument whose name is an instance of a str
# subclass binds the first positional-or-keyword or keyword-only
# parameter, in order, that its __eq__, which may loop, finds equal,
# whatever the spelling; one equal to none, or to a positional-only name
# only, goes to **kwargs or is an unexpected keyword, and an exception of
# __eq__ propagates from the call. Inside functions as at module level.
from harness import *

log = []

class Name(str):
    def __eq__(self, other):
        for _ in range(2): pass
        log.append((str(self), other))
        if str(self) == "bad": raise LookupError(other)
        return str.__eq__(self, other) or str(self) == other.upper()
    __hash__ = str.__hash__

def f(p, /, a, b=2, *, c=3, **rest): return p, a, b, c, sorted(rest)
def g(a, b=2): return a, b

def error(fn):
    try:
        return fn()
    except Exception as e:
        return type(e).__name__, str(e)

def calls():
    del log[:]
    out = [f(0, **{Name("a"): 1}), f(0, 1, **{Name("c"): 4}), f(0, 1, **{Name("B"): 5}), f(0, 1, **{Name("p"): 6}),
           f(0, **{Name("a"): 1, Name("z"): 7}), g(1, **{Name("b"): 8}), error(lambda: g(1, **{Name("a"): 9})),
           error(lambda: g(1, **{Name("q"): 9})), error(lambda: g(1, **{Name("bad"): 9}))]
    return out + [list(log)]

expected = [(0, 1, 2, 3, []), (0, 1, 2, 4, []), (0, 1, 5, 3, []), (0, 1, 2, 3, ["p"]), (0, 1, 2, 3, ["z"]), (1, 8),
            ("TypeError", "g() got multiple values for argument 'a'"), ("TypeError", "g() got an unexpected keyword argument 'q'"),
            ("LookupError", "a"),
            [("a", "a"), ("c", "a"), ("c", "b"), ("c", "c"), ("B", "a"), ("B", "b"), ("p", "a"), ("p", "b"), ("p", "c"), ("a", "a"),
             ("z", "a"), ("z", "b"), ("z", "c"), ("b", "a"), ("b", "b"), ("a", "a"), ("q", "a"), ("q", "b"), ("bad", "a")]]

def main():
    return calls()

assert_eq(main(), expected)
assert_eq(calls(), expected)
