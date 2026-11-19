# spec: PLS-315 7.3.2, 7.3.3, 7.5.1, 7.5.2, 7.5.5, 7.5.6, 7.5.7, 7.5.8
# description: A conversion builtin (repr, str, ascii, format, len, int,
# float, complex, bytes, hash, abs, round, reversed, next, dir, hex,
# bool), a %-format, an f-string, str.format, print, map, filter and a
# sort key read the special method a class holds as a descriptor once,
# then call what the read returns. A read's AttributeError makes the
# method absent where the operation has a fallback: repr's default text
# (str's too, without a __str__), bool's True, hash's and round's
# TypeError; elsewhere it propagates. Inside a generator as at module level.
from harness import *

log = []
class Reads:
    def __init__(self, value): self.value = value
    def __get__(self, obj, owner):
        for _ in range(2): pass
        log.append("get")
        value = self.value
        def method(*args):
            log.append("call")
            return value(obj, *args) if callable(value) else value
        return method
def fail(self): raise AttributeError("read")

VALUES = {"__repr__": "R", "__str__": "S", "__format__": lambda self, spec: "F" + spec, "__len__": 3, "__int__": 4, "__float__": 2.5,
          "__complex__": 1j, "__bytes__": b"b", "__hash__": 7, "__abs__": 8, "__round__": lambda self, *n: 9,
          "__reversed__": lambda self: iter([1]), "__next__": 5, "__dir__": ["b", "a"], "__index__": 10, "__bool__": False}
CALLS = [("__repr__", repr), ("__str__", str), ("__format__", lambda x: format(x, "x")), ("__len__", len), ("__int__", int),
         ("__float__", float), ("__complex__", complex), ("__bytes__", bytes), ("__hash__", hash), ("__abs__", abs),
         ("__round__", round), ("__reversed__", lambda x: list(reversed(x))), ("__next__", next), ("__dir__", dir),
         ("__index__", hex), ("__bool__", bool), ("__repr__", ascii), ("__repr__", lambda x: "%r" % (x,)),
         ("__str__", lambda x: "%s" % (x,)), ("__repr__", lambda x: f"{x!r}"), ("__str__", lambda x: f"{x}"),
         ("__repr__", lambda x: "{!r}".format(x)), ("__str__", lambda x: list(map(str, [x, x]))),
         ("__bool__", lambda x: list(filter(None, [x]))), ("__round__", lambda x: round(x, 2)), ("__next__", lambda x: next(x, "d")),
         ("__repr__", str), ("__str__", lambda x: sorted([x, x], key=str))]

def converted(name, convert, failing):
    del log[:]
    C = type("C", (), {name: property(fail) if failing else Reads(VALUES[name])})
    try: result = convert(C())
    except Exception as e: result = "%s: %s" % (type(e).__name__, e)
    result = str(result).replace("__main__.", "")
    if " object at 0x" in result: result = result[:result.index(" object at 0x")]
    return result, log[:]

def run():
    return [converted(name, convert, failing) for name, convert in CALLS for failing in (False, True)]

ONCE = ["get", "call"]
AE = ("AttributeError: read", [])
EXPECTED = [("R", ONCE), ("<C", []), ("S", ONCE), AE, ("Fx", ONCE), AE, ("3", ONCE), AE, ("4", ONCE), AE, ("2.5", ONCE), AE,
            ("1j", ONCE), AE, ("b'b'", ONCE), AE, ("7", ONCE), ("TypeError: unhashable type: 'C'", []), ("8", ONCE), AE,
            ("9", ONCE), ("TypeError: type C doesn't define __round__ method", []), ("[1]", ONCE), AE, ("5", ONCE), AE,
            ("['a', 'b']", ONCE), AE, ("0xa", ONCE), AE, ("False", ONCE), ("True", []), ("R", ONCE), ("<C", []),
            ("R", ONCE), ("<C", []), ("S", ONCE), AE, ("R", ONCE), ("<C", []), ("S", ONCE), AE, ("R", ONCE), ("<C", []),
            ("['S', 'S']", ["get", "call", "get", "call"]), AE, ("[]", ONCE), ("[<C", []),
            ("9", ONCE), ("TypeError: type C doesn't define __round__ method", []), ("5", ONCE), AE, ("R", ONCE), ("<C", []),
            ("[<C", ["get", "call", "get", "call"]), AE]

def paused():
    class C:
        __repr__ = Reads("R")
        __str__ = Reads("S")
        __len__ = Reads(3)
    def gen():
        yield repr(C())
        yield str(C())
        yield len(C())
        yield f"{C()!r}"
    del log[:]
    return list(gen()), len(log)

def main():
    return run(), paused()

assert_eq(main(), (EXPECTED, (["R", "S", 3, "R"], 8)))
assert_eq((run(), paused()), (EXPECTED, (["R", "S", 3, "R"], 8)))
