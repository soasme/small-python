# spec: PLS-315 7.3.6, 7.3.4
# description: a class attribute read through a descriptor calls its
# __get__ with None and the class; one of the metaclass is called with the
# class and the metaclass, a data descriptor or property before the class's
# own attribute and a non-data descriptor after it; getattr() and hasattr()
# read the same way, an error from __get__ propagates, an AttributeError
# naming the attribute and class, and a metaclass __getattr__ follows it;
# a read follows changes to the classes; methods that loop are called
# inside functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class NonData:
    def __get__(self, obj, owner):
        spin(); log.append(("get", obj, owner.__name__))
        return "non-data"

class Data(NonData):
    def __set__(self, obj, value): pass

class Missing:
    def __get__(self, obj, owner):
        spin()
        raise AttributeError("inner")

class Meta(type):
    @property
    def prop(cls):
        spin(); log.append(("prop", cls.__name__))
        return "prop"
    data = Data()
    plain = NonData()
    shadowed = NonData()

class A(metaclass=Meta):
    nd = NonData()
    shadowed = "own"
    data = "hidden"
    missing = Missing()

class B(A): pass

class Plain:
    nd = NonData()

def reads():
    out = [A.nd, B.nd, Plain.nd, A.prop, B.data, A.plain, A.shadowed]
    out += [getattr(A, "nd"), getattr(B, "prop"), hasattr(A, "missing"), getattr(A, "missing", "dflt")]
    try: A.missing
    except AttributeError as e: out.append((str(e), e.name, e.obj is A))
    out.append(log[:]); log.clear()
    return out

expected = ["non-data", "non-data", "non-data", "prop", "non-data", "non-data", "own",
            "non-data", "prop", False, "dflt", ("inner", "missing", True),
            [("get", None, "A"), ("get", None, "B"), ("get", None, "Plain"), ("prop", "A"),
             ("get", B, "Meta"), ("get", A, "Meta"), ("get", None, "A"), ("prop", "B")]]
assert_eq(reads(), expected)
assert_eq(reads(), expected)
assert_eq([A.nd, A.prop, log], ["non-data", "prop", [("get", None, "A"), ("prop", "A")]])
log.clear()

# Other errors propagate; a metaclass __getattr__ follows an AttributeError.
class Failing:
    def __get__(self, obj, owner):
        spin()
        raise KeyError("failing")

class Fallback(type):
    def __getattr__(cls, name): return "fallback " + name

class F(metaclass=Fallback):
    missing = Missing()
    nd = NonData()
    fl = Failing()

def errors():
    out = [F.missing, F.nd, F.other]
    try: F.fl
    except KeyError as e: out.append(e.args)
    return out

assert_eq(errors(), ["fallback missing", "non-data", "fallback other", ("failing",)])

# A class attribute replaced by a descriptor, a descriptor whose type gains
# __get__, and a metaclass that gains a property are read through them at once.
class Later: pass

class LM(type): pass

class K(metaclass=LM):
    x = 1

def later_get(self, obj, owner):
    spin()
    return ("later", obj, owner.__name__)

def changing():
    out = []
    for i in range(6):
        v = K.x
        out.append("instance" if isinstance(v, Later) else v)
        if i == 0: K.x = Later()
        if i == 1: Later.__get__ = later_get
        if i == 2: del Later.__get__
        if i == 3:
            del K.x
            LM.x = property(lambda cls: ("meta", cls.__name__))
    return out

assert_eq(changing(), [1, "instance", ("later", None, "K"), "instance", ("meta", "K"), ("meta", "K")])
