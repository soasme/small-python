# spec: PLS-315 16.6.1, 14.2.2
# description: a starred annotation's value is the single item its
# expression unpacks to; a wrong count or a non-iterable raises as an
# assignment to one target, reported at the def's line (not the
# decorator's, not the parameter's).
from harness import *
def deco(f): return f
def one(*b: *[7]): pass
def many(*b: *[1, 2]): pass
def none(a: int,
         *b: *[]): pass
@deco
def bad(
        *b: *1): pass
def outcome(f):
    try: return f.__annotations__
    except (TypeError, ValueError) as e:
        tb = e.__traceback__
        while tb.tb_next: tb = tb.tb_next
        return type(e).__name__, str(e), tb.tb_lineno - f.__code__.co_firstlineno
assert_eq(outcome(one), {"b": 7})
assert_eq(outcome(many), ("ValueError", "too many values to unpack (expected 1, got 2)", 0))
assert_eq(outcome(none), ("ValueError", "not enough values to unpack (expected 1, got 0)", 0))
assert_eq(outcome(bad), ("TypeError", "cannot unpack non-iterable int object", 1))
