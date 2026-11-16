# spec: PLS-315 7.4.3
# description: A keyword argument whose name is an instance of a str
# subclass binds the first positional-or-keyword or keyword-only
# parameter, in order, that its __eq__, which may loop, finds equal,
# whatever the spelling; one equal to none, or to a positional-only name
# only, goes to **kwargs or is an unexpected keyword, and an exception of
# __eq__ propagates from the call. NotImplemented from __eq__ leaves str's
# comparison, and the truth of what it returns is its __bool__'s or
# __len__'s; a bound method or a generator function binds alike, an
# exception from __bool__ propagating too. Inside functions as at module
# level.
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

class Truth:
    def __init__(self, value): self.value = value
    def __bool__(self):
        log.append(("bool", self.value))
        if self.value == "raise": raise KeyError(self.value)
        return self.value == "yes"

class Sized:
    def __len__(self):
        log.append("len")
        return 1

class Odd(str):
    def __eq__(self, other):
        log.append((str(self), other))
        if str(self) == "b": return NotImplemented
        if str(self) == "s": return Sized()
        return Truth("yes" if (str(self), other) == ("x", "b") else "raise" if str(self) == "r" else "no")
    __hash__ = str.__hash__

class C:
    def m(self, a, b=2, **rest): return a, b, [str(k) for k in rest]

def gen(a, b=2):
    yield a
    yield b

def more():
    del log[:]
    out = [g(1, **{Odd("x"): 3}), g(**{Odd("b"): 3, "a": 4}), error(lambda: g(1, **{Odd("r"): 3})), error(lambda: g(1, **{Odd("s"): 3})),
           C().m(1, **{Odd("x"): 5, Odd("q"): 6}), list(gen(1, **{Odd("x"): 7})), error(lambda: g(**{Odd("x"): 1, "b": 2})),
           error(lambda: g(1, 2, 3, **{Odd("x"): 4}))]
    return out + [list(log)]

expected_more = [(1, 3), (4, 3), ('KeyError', "'raise'"), ('TypeError', "g() got multiple values for argument 's'"), (1, 5, ['q']), [1, 7], ('TypeError', "g() got multiple values for argument 'b'"), ('TypeError', "g() got multiple values for argument 'x'"), [('x', 'a'), ('bool', 'no'), ('x', 'b'), ('bool', 'yes'), ('b', 'a'), ('b', 'b'), ('r', 'a'), ('bool', 'raise'), ('s', 'a'), 'len', ('x', 'self'), ('bool', 'no'), ('x', 'a'), ('bool', 'no'), ('x', 'b'), ('bool', 'yes'), ('q', 'self'), ('bool', 'no'), ('q', 'a'), ('bool', 'no'), ('q', 'b'), ('bool', 'no'), ('x', 'a'), ('bool', 'no'), ('x', 'b'), ('bool', 'yes'), ('x', 'a'), ('bool', 'no'), ('x', 'b'), ('bool', 'yes'), ('x', 'a'), ('bool', 'no'), ('x', 'b'), ('bool', 'yes')]]

def main():
    return calls(), more()

assert_eq(main(), (expected, expected_more))
assert_eq((calls(), more()), (expected, expected_more))
