# spec: PLS-315 19.3.5, 19.3.33, 7.5.3, 7.5.6
# description: ascii() of an instance calls its class's Python __repr__,
# which may loop, and escapes the str it returns; a non-str result is a
# TypeError. round(x, ndigits) of an int or float x and an instance
# ndigits calls the ndigits' Python __index__ and rounds by the int it
# returns, a bool as its int; a non-int result is a TypeError naming the
# class, and an exception from it propagates. Inside functions as at
# module level.
from harness import *

log = []

class Shown:
    def __init__(self, t): self.t = t
    def __repr__(self):
        for _ in (): pass
        log.append("repr")
        return self.t

class Digits:
    def __init__(self, n): self.n = n
    def __index__(self):
        for _ in (): pass
        log.append("index")
        if self.n == "raise": raise LookupError("d")
        return self.n

def calls():
    return [ascii(Shown("\xe9t€")), ascii(Shown("plain")), ascii([Shown("x")]),
            round(2.25, Digits(1)), round(1234, Digits(-2)), round(7, Digits(True)),
            round(True, Digits(3)), round(-0.5, Digits(0)), round(1.5, ndigits=Digits(0))]

expected = ["\\xe9t\\u20ac", "plain", "[x]", 2.2, 1200, 7, 1, -0.0, 2.0]
assert_eq(calls(), expected)
assert_eq(log, ["repr", "repr", "repr", "index", "index", "index", "index", "index", "index"])
log.clear()

assert_eq([ascii(Shown("\xe9")), round(2.25, Digits(1))], ["'\\xe9'"[1:-1], 2.2])
assert_eq(log, ["repr", "index"])

def errors():
    out = []
    try: ascii(Shown(3))
    except TypeError as e: out.append(str(e))
    try: round(2.5, Digits("1"))
    except TypeError as e: out.append(str(e))
    try: round(2, Digits("raise"))
    except LookupError as e: out.append(e.args)
    return out

assert_eq(errors(), ["Shown.__repr__() must return a str, not int",
                     "Digits.__index__() must return an int, not str", ("d",)])
