# spec: PLS-315 14.8
# description: Raising and catching an exception calls only what
# MakeException calls: no __str__ or __repr__ of the exception runs,
# inside functions as at module level, with a cause and when re-raised.
from harness import *

calls = []

class Loud(Exception):
    def __str__(self):
        calls.append("str")
        return "loud"
    def __repr__(self):
        calls.append("repr")
        return "Loud()"

def raise_and_catch():
    caught = []
    for make in (lambda: Loud(), lambda: Loud, lambda: ValueError("x")):
        try:
            try:
                raise make() from Loud()
            except Exception:
                raise
        except Exception as e:
            caught.append(type(e).__name__)
    return caught

assert_eq(raise_and_catch(), ["Loud", "Loud", "ValueError"])
try:
    raise Loud
except Loud as e:
    assert_eq(str(e), "loud")
assert_eq(calls, ["str"])
