# spec: PLS-315 20.8.2, 29.5.1
# description: A sentinel is a union member: s | x and x | s, x a class,
# None, a sentinel or a union, make a union of both, s | 1 and 1 | s are
# TypeErrors, and the first union a program makes may be one; inside
# functions and generators as at module level.
from harness import *

S = sentinel("S")
T = sentinel("T")

def cases():
    out = [(S | int).__args__, (int | S).__args__, (S | None).__args__, (None | S).__args__, (S | T).__args__,
           (S | S) is S, (S | (int | str)).__args__, ((int | str) | S).__args__]
    for f in (lambda: S | 1, lambda: 1 | S):
        try: f()
        except TypeError as e: out.append(str(e))
    return out

expected = [(S, int), (int, S), (S, type(None)), (type(None), S), (S, T), True, (S, int, str), (int, str, S),
            "unsupported operand type(s) for |: 'sentinel' and 'int'", "unsupported operand type(s) for |: 'int' and 'sentinel'"]

assert_eq(cases(), expected)
def gen():
    yield cases()
assert_eq(next(gen()), expected)
def main(): return cases()
assert_eq(main(), expected)
