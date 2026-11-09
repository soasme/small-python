# spec: PLS-315 7.3.4, 13.3.1, 20.5.2
# description: Reading a property of an instance, plain or of a subclass
# of a builtin type or an exception, by reference or getattr(), calls its
# Python getter with the instance; the getter's value is the reference's.
# An AttributeError from a property's getter read by getattr(), or from
# a descriptor's __get__, names the attribute and object unless it already
# names one; other exceptions pass unchanged, inside functions as at
# module level. (Whether a reference names the error of a property's
# getter is left open: CPython's does until it specializes the reference.)
from harness import *

def spin():
    for _ in range(2): pass

class Gets:
    def __get__(self, instance, owner):
        spin()
        raise AttributeError("get")

class Plain:
    d = Gets()
    @property
    def p(self):
        spin()
        return "plain"
    @property
    def bad(self):
        spin()
        raise AttributeError("inner")
    @property
    def named(self):
        spin()
        raise AttributeError("named", name="other", obj=None)
    @property
    def key(self):
        spin()
        raise KeyError("key")

class Items(list):
    @property
    def p(self):
        spin()
        return len(self)
    @property
    def bad(self):
        spin()
        raise AttributeError("inner")

class Failure(Exception):
    @property
    def p(self):
        spin()
        return self.args

def error(f):
    try:
        return f()
    except AttributeError as e:
        return str(e), e.name, e.obj is None or type(e.obj).__name__
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    plain, items = Plain(), Items([1, 2])
    got = getattr(items, "p")
    return [plain.p, getattr(plain, "p"), items.p, got, Failure(3).p, getattr(Failure(4), "p"),
            error(lambda: getattr(plain, "bad")), error(lambda: getattr(items, "bad")), error(lambda: plain.d),
            error(lambda: getattr(plain, "d")), error(lambda: plain.named), error(lambda: plain.key)]

expected = ["plain", "plain", 2, 2, (3,), (4,), ("inner", "bad", "Plain"), ("inner", "bad", "Items"),
            ("get", "d", "Plain"), ("get", "d", "Plain"), ("named", "other", True), ("KeyError", "'key'")]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
plain, items = Plain(), Items([1])
try:
    plain.d
except AttributeError as e:
    assert_eq((e.name, e.obj is plain), ("d", True))
assert_eq((items.p, getattr(items, "p")), (1, 1))
