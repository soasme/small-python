# spec: PLS-315 19.3.31, 7.3.4
# description: print reads its file's write before each write, and its
# flush once, as any attribute read does: through a Python __getattr__
# when the read fails, a property's getter, a Python __getattribute__,
# and a getter's AttributeError falling back to __getattr__, each of
# which may loop, with str, int and other builtin objects as with
# instances; the read's error propagates, the writes before it done, and
# a file with no write raises AttributeError. Inside functions as at
# module level.
from harness import *

log = []

def spin():
    for _ in (): pass

class Lookup:
    def __getattr__(self, name):
        spin()
        log.append("get " + name)
        return lambda *a: log.append((name,) + a)

class Prop:
    @property
    def write(self):
        spin()
        log.append("prop")
        return lambda text: log.append("p " + text)

class Hooked:
    def __getattribute__(self, name):
        spin()
        log.append("hook " + name)
        return lambda *a: log.append(a)

class Fallen:
    @property
    def write(self):
        spin()
        raise AttributeError("write")
    def __getattr__(self, name):
        spin()
        log.append("fallback " + name)
        return lambda text: log.append("f " + text)

class Failing:
    n = 0
    def __getattr__(self, name):
        spin()
        Failing.n += 1
        if Failing.n == 2: raise LookupError("read")
        return lambda text: log.append("x " + text)

class Nothing:
    pass

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    Failing.n = 0
    print("a", 1, file=Lookup(), flush=True)
    print(2.5, file=Prop())
    print("b", "c", sep="", file=Hooked(), flush=True)
    print("d", file=Fallen())
    out = [error(lambda: print("e", "f", file=Failing())), error(lambda: print("g", file=Nothing())), list(log)]
    return out

expected = [("LookupError", "read"), ("AttributeError", "'Nothing' object has no attribute 'write'"),
            ["get write", ("write", "a"), "get write", ("write", " "), "get write", ("write", "1"), "get write", ("write", "\n"),
             "get flush", ("flush",), "prop", "p 2.5", "prop", "p \n", "hook write", ("b",), "hook write", ("",), "hook write", ("c",),
             "hook write", ("\n",), "hook flush", (), "fallback write", "f d", "fallback write", "f \n", "x e"]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
