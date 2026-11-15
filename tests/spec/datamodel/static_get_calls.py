# spec: PLS-315 7.5.2, 7.5.3
# description: A descriptor whose class's __get__ is a staticmethod has
# the wrapped function called unbound, with the descriptor, the instance
# (None for its class) and the owner, as a plain function __get__ is: for
# an instance's attribute, a non-data descriptor only when the instance
# has no entry of the name, a class's attribute and super()'s, the
# function may loop and its exception propagates. Inside functions as at
# module level.
from harness import *

log = []

def got(descriptor, instance, owner):
    for _ in range(2): pass
    log.append(type(descriptor).__name__)
    if instance == "bad": raise LookupError("bad")
    return instance, owner

class Plain:
    __get__ = staticmethod(got)

class Data:
    __get__ = staticmethod(got)
    def __set__(self, instance, value): pass

class Base:
    plain = Plain()
    data = Data()

class Owner(Base):
    def through_super(self): return super().plain

def reads(o):
    del log[:]
    out = [o.plain, Owner.plain, o.data, o.through_super()]
    o.__dict__.update(plain="own", data="own")
    out += [o.plain, o.data]
    try:
        Plain.__get__(Plain(), "bad", Owner)
    except LookupError as e:
        out.append(str(e))
    del o.__dict__["plain"], o.__dict__["data"]
    return out + [list(log)]

def main(o):
    return reads(o)

o = Owner()
expected = [(o, Owner), (None, Owner), (o, Owner), (o, Owner), "own", (o, Owner), "bad",
            ["Plain", "Plain", "Data", "Plain", "Data", "Plain"]]
assert_eq(main(o), expected)
assert_eq(reads(o), expected)
