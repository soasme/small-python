# spec: PLS-315 27.1.5, 26.10.1
# description: map(property, getters) makes each property as a call of
# property does, reading each getter's __doc__ when it is made: by a
# Python __getattribute__, or a __getattr__ after its AttributeError, or
# a __doc__ property, each of which may loop, in the order the map is
# consumed; an exception from the read other than AttributeError
# propagates.
from harness import *

log = []
def spin():
    for _ in range(2): pass
class Reading:
    def __init__(self, tag): self.tag = tag
    def __call__(self, obj): return self.tag
    def __getattribute__(self, name):
        spin()
        tag = object.__getattribute__(self, "tag")
        if name == "__doc__":
            log.append(("get", tag))
            if tag == "fail": raise LookupError("doc")
            if tag == "fall": raise AttributeError(name)
            return "doc " + tag
        return object.__getattribute__(self, name)
    def __getattr__(self, name):
        spin(); log.append(("fallback", name)); return "fallen"
class Prop:
    def __call__(self, obj): return 0
    @property
    def __doc__(self): spin(); log.append("prop"); return "prop doc"

def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def cases():
    return [run(lambda: [p.__doc__ for p in map(property, [Reading("a"), Reading("b")])]),
            run(lambda: [p.__doc__ for p in map(property, [Reading("fall"), Prop()])]),
            run(lambda: next(map(property, [Reading("fail")]))), run(lambda: list(map(property, [])))]
expected = [(["doc a", "doc b"], [("get", "a"), ("get", "b")]), (["fallen", "prop doc"], [("get", "fall"), ("fallback", "__doc__"), "prop"]),
            (("LookupError", "doc"), [("get", "fail")]), ([], [])]
assert_eq(cases(), expected)
assert_eq(cases(), expected)
