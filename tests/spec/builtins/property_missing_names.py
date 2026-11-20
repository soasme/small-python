# spec: PLS-315 20.5, 7.3.7
# description: a property with no setter or deleter that has no name of
# its own reads its getter's __name__ for the AttributeError, a Python
# property or __getattr__ called once, its AttributeError leaving the
# message unnamed and any other error propagating; the name's Python
# __repr__ shapes the message and must return a str. An attribute
# statement, del, setattr() and delattr() share it, inside functions as at
# module level. An instance's __name__ read through its class's property
# or descriptor is the property's value, not the class's name.
from harness import *

log = []
class S(str):
    def __repr__(self):
        log.append("repr")
        return "<S>"
class R:
    def __repr__(self): return 5
def getter(name):
    class G:
        def __call__(self, obj): return 0
        @property
        def __name__(self):
            log.append("name")
            if isinstance(name, BaseException): raise name
            return name
    return G()
class Hooked:
    def __call__(self, obj): return 0
    def __getattr__(self, key):
        log.append(key)
        raise AttributeError(key)

class C:
    pass
C.plain = property(getter("nm"))
C.sub = property(getter(S("s")))
C.bad = property(getter(R()))
C.gone = property(getter(AttributeError("x")))
C.fails = property(getter(LookupError("x")))
C.hooked = property(Hooked())

def store(c, name): setattr(c, name, 1)
def statement(c, name):
    if name == "plain": c.plain = 1
    elif name == "sub": c.sub = 1
    elif name == "bad": c.bad = 1
    elif name == "gone": c.gone = 1
    elif name == "fails": c.fails = 1
    else: c.hooked = 1
def deletion(c, name):
    if name == "plain": del c.plain
    elif name == "sub": del c.sub
    elif name == "bad": del c.bad
    elif name == "gone": del c.gone
    elif name == "fails": del c.fails
    else: del c.hooked
def remove(c, name): delattr(c, name)

def outcome(how, name):
    try:
        how(C(), name)
        result = "stored"
    except Exception as e:
        result = (type(e).__name__, str(e))
    taken = list(log); log.clear()
    return result, taken

for how, accessor in ((store, "setter"), (statement, "setter"), (deletion, "deleter"), (remove, "deleter")):
    assert_eq(outcome(how, "plain"), (("AttributeError", f"property 'nm' of 'C' object has no {accessor}"), ["name"]))
    assert_eq(outcome(how, "sub"), (("AttributeError", f"property <S> of 'C' object has no {accessor}"), ["name", "repr"]))
    assert_eq(outcome(how, "bad"), (("TypeError", "R.__repr__() must return a str, not int"), ["name"]))
    assert_eq(outcome(how, "gone"), (("AttributeError", f"property of 'C' object has no {accessor}"), ["name"]))
    assert_eq(outcome(how, "fails"), (("LookupError", "x"), ["name"]))
    assert_eq(outcome(how, "hooked"), (("AttributeError", f"property of 'C' object has no {accessor}"), ["__name__"]))
c = C()
try:
    c.plain = 1
except AttributeError as e:
    assert_eq(str(e), "property 'nm' of 'C' object has no setter")
log.clear()

class Named:
    @property
    def __name__(self):
        log.append("read")
        return "instance"
class Sub(Named):
    pass
class Described:
    class D:
        def __get__(self, obj, owner): return "instance" if obj is not None else "class"
    __name__ = D()
def read(o): return o.__name__
for o, owner in ((Named(), "Named"), (Sub(), "Sub")):
    assert_eq((read(o), getattr(o, "__name__"), o.__name__, type(o).__name__), ("instance",) * 3 + (owner,))
assert_eq(log, ["read"] * 6)
assert_eq((read(Described()), Described.__name__), ("instance", "Described"))
