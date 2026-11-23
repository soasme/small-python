# spec: PLS-315 13.3.4
# description: A call's duplicate keyword from ** raises TypeError naming the
# callee as "module.qualname()", "qualname()" for builtins or a missing
# __module__, str() of a callee with no __qualname__, and "function" when
# reading either raises another exception; from a dict or a mappingproxy.
from harness import *

Proxy = type(type.__dict__)
first = {"k": 1}

class Plain:
    def __call__(self, **kw): pass
    def __repr__(self): return "<plain>"

class Looked:
    def __init__(self, qualname): self.qualname = qualname
    def __call__(self, **kw): pass
    def __getattr__(self, name):
        if name != "__qualname__": raise AttributeError(name)
        if isinstance(self.qualname, type): raise self.qualname(name)
        return self.qualname

class BadModule(Looked):
    @property
    def __module__(self): raise LookupError

def message(f, second):
    return str(assert_raises(TypeError, lambda: f(**first, **second))).removesuffix(" got multiple values for keyword argument 'k'")

def names(second):
    return [message(Plain(), second), message(Looked(LookupError), second), message(Looked("Named"), second),
            message(BadModule("Named"), second), message(str.join, second), message(print, second)]

expected = ["<plain>", "function", "__main__.Named()", "function", "str.join()", "print()"]
assert_eq(names({"k": 2}), expected)
assert_eq(names(Proxy({"k": 2})), expected)
