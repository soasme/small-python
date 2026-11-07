# spec: PLS-315 19.3.11, 7.3.4
# description: getattr() with a default and hasattr() of an instance
# answer from its own attributes, its class's, a __getattr__ that may
# raise AttributeError, a __getattribute__ override, a property whose
# getter raises AttributeError or another error, and a str subclass name;
# a class or attribute added later is seen at once.
from harness import *

class A:
    k = "class"
    def __init__(self): self.x = 1
    @property
    def gone(self): raise AttributeError("gone")
    @property
    def broken(self): raise KeyError("broken")

class Fallback(A):
    def __getattr__(self, name):
        if name == "secret": return 42
        raise AttributeError(name)

class Override:
    def __getattribute__(self, name):
        if name == "magic": return "m"
        return object.__getattribute__(self, name)

class Name(str): pass

def run():
    a, f, o = A(), Fallback(), Override()
    out = [getattr(a, "x", 0), getattr(a, "y", 0), hasattr(a, "x"), hasattr(a, "y"), getattr(a, "k", 0),
           hasattr(a, "gone"), getattr(a, "gone", "default"), getattr(f, "secret", 0), getattr(f, "y", 0),
           hasattr(f, "secret"), getattr(o, "magic", 0), getattr(o, "y", 0), hasattr(o, "magic"),
           getattr(a, Name("x"), 0), hasattr(a, Name("y"))]
    try: hasattr(a, "broken")
    except KeyError as e: out.append(e.args)
    try: getattr(a, "broken", 0)
    except KeyError as e: out.append(e.args)
    out.append(getattr(a, "later", 0))
    A.later = "added"
    out.append(getattr(a, "later", 0))
    a.y = 2
    out.append((getattr(a, "y", 0), hasattr(a, "y")))
    del a.y
    out.append((getattr(a, "y", 0), hasattr(a, "y")))
    return out

assert_eq(run(), [1, 0, True, False, "class", False, "default", 42, 0, True, "m", 0, True, 1, False,
                  ("broken",), ("broken",), 0, "added", (2, True), (0, False)])
