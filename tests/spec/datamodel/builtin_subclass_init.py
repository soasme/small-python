# spec: PLS-315 10.2.1, 20.2.5, 21.1.5
# description: Calling a subclass of a builtin type or of an exception
# whose __init__ is a Python function makes the instance with the builtin
# __new__ and the arguments, then calls that __init__ with them, by
# position, by keyword and unpacked; a value other than None from
# __init__ is a TypeError, and an error from __new__ or __init__ reaches
# the caller, inside functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Failure(Exception):
    def __init__(self, message, code=0):
        spin()
        super().__init__(message)
        self.code = code
        log.append(("failure", message, code))

class Items(list):
    def __init__(self, *items):
        spin()
        super().__init__(items)

class Options(dict):
    def __init__(self, **options):
        spin()
        super().__init__(options)

class Count(int):
    def __init__(self, value):
        spin()
        self.doubled = value * 2

class Quiet(dict):
    def __init__(self): self.tag = 1

class Returns(Exception):
    def __init__(self): return 5

class Raises(Exception):
    def __init__(self): raise KeyError("init")

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    out = []
    try:
        raise Failure("m", code=3)
    except Failure as e:
        out.append((e.args, e.code))
    e = Failure("x")
    out.append((e.args, e.code, str(e)))
    out += [Items(1, 2, 3), Options(a=1), type(Items()).__name__]
    args, keywords = ("y",), {"code": 9}
    out.append(Failure(*args, **keywords).code)
    n = Count(21)
    out += [n + 0, n.doubled]
    q = Quiet()
    q["k"] = 2
    out.append((q["k"], q.tag, len(q)))
    out += [error(Returns), error(Raises), error(Failure), error(lambda: Count("z"))]
    out.append(list(log))
    return out

expected = [(("m",), 3), (("x",), 0, "x"), [1, 2, 3], {"a": 1}, "Items", 9, 21, 42, (2, 1, 1),
            ("TypeError", "__init__() should return None, not 'int'"), ("KeyError", "'init'"),
            ("TypeError", "Failure.__init__() missing 1 required positional argument: 'message'"),
            ("ValueError", "invalid literal for int() with base 10: 'z'"),
            [("failure", "m", 3), ("failure", "x", 0), ("failure", "y", 9)]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
