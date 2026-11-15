# spec: PLS-315 19.3.33, 7.5.3
# description: round(number, ndigits) given ndigits, or both, by keyword,
# in either order, calls an instance ndigits' Python __index__, which may
# loop, and rounds by the int it returns, as the positional call does; a
# non-int result is a TypeError, an exception from it propagates, and an
# unknown, repeated or missing argument is a TypeError before any call.
# Inside functions and generators as at module level.
from harness import *

log = []

class Digits:
    def __init__(self, n): self.n = n
    def __index__(self):
        for _ in (): pass
        log.append(self.n)
        if self.n == "raise": raise LookupError("d")
        return self.n

def calls():
    return [round(1.5, ndigits=Digits(0)), round(number=2.25, ndigits=Digits(1)), round(ndigits=Digits(-2), number=1234),
            round(2.5, ndigits=None)]

assert_eq(calls(), [2.0, 2.2, 1200, 2])
assert_eq(log, [0, 1, -2])
log.clear()
assert_eq(round(3.14159, ndigits=Digits(2)), 3.14)

def errors():
    out = []
    for bad in (lambda: round(2.5, ndigits=Digits("1")), lambda: round(2, ndigits=Digits("raise")),
                lambda: round(number=2, digits=Digits(1)), lambda: round(2, number=Digits(1)),
                lambda: round(ndigits=Digits(1)), lambda: round(2, 1, ndigits=Digits(1))):
        try: bad()
        except (TypeError, LookupError) as e: out.append(type(e).__name__)
    return out

assert_eq(errors(), ["TypeError", "LookupError", "TypeError", "TypeError", "TypeError", "TypeError"])

def gen(): yield round(number=2.675, ndigits=Digits(2))

assert_eq(list(gen()), [2.67])
assert_eq(log, [2, "1", "raise", 2])
