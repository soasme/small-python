# spec: PLS-315 9.3.1, 9.3.2
# description: A name looked up in a namespace that is a dict subclass,
# as builtins, globals read as locals, or explicit locals, calls its
# Python __missing__, which may loop, once when the name is absent: its
# value is the name's, its KeyError makes the name undefined, another
# error propagates; in comprehensions, lambdas and functions too.
from harness import *

log = []
class Missing(dict):
    def __missing__(self, key):
        for _ in (): pass
        log.append(key)
        if key == "bad": raise ValueError(key)
        if key == "absent": raise KeyError(key)
        return "missing:" + key
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
b = Missing(len=len)
cases = [lambda: eval("abc", {"__builtins__": b}), lambda: eval("len('ab')", {"__builtins__": b}),
         lambda: eval("bad", {"__builtins__": b}), lambda: eval("absent", {"__builtins__": b}),
         lambda: eval("[abc for _ in [1]]", {"__builtins__": b}), lambda: eval("(lambda: xyz)()", {"__builtins__": b}),
         lambda: eval("abc", {"__builtins__": b}, {}), lambda: eval("abc", Missing()),
         lambda: eval("abc", {"__builtins__": b}, Missing())]
def module():
    g = {"__builtins__": b}
    exec("def f():\n    for _ in (): pass\n    return q\nr = f() + w", g)
    return g["r"]
cases.append(module)
assert_eq([run(f) for f in cases],
          [("missing:abc", ["abc"]), (2, []), (("ValueError", "bad"), ["bad"]),
           (("NameError", "name 'absent' is not defined"), ["absent"]), (["missing:abc"], ["abc"]),
           ("missing:xyz", ["xyz"]), ("missing:abc", ["abc"]), ("missing:abc", ["abc"]), ("missing:abc", ["abc"]),
           ("missing:qmissing:w", ["q", "w"])])
