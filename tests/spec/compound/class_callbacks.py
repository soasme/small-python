# spec: PLS-315 16.4.2, 16.4.3
# description: A new class calls __set_name__ on each namespace value whose
# type defines it, in definition order over a snapshot of the namespace, and
# then the base's __init_subclass__ with the header keywords; a __set_name__
# exception gains a note and stops the rest, and the __class__ cell is
# checked after both. Methods that loop run in function statements as at
# module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Named:
    def __init__(self, tag): self.tag = tag
    def __set_name__(self, owner, name):
        spin()
        log.append(("set", self.tag, owner.__name__, name))
        if self.tag == "drop":
            del owner.later
        if self.tag == "fail":
            raise KeyError(name)

class Plain:
    def __set_name__(self, owner, name):
        log.append(("plain", name))

class Stamp:
    __set_name__ = staticmethod(lambda owner, name: log.append(("static", name)))

class Arity:
    def __set_name__(self):
        spin()

class Base:
    def __init_subclass__(cls, **kwds):
        spin()
        log.append(("init_subclass", cls.__name__, kwds, sorted(k for k in vars(cls) if not k.startswith("__"))))
        if kwds.get("fail"):
            raise ValueError("subclass")

def error(make):
    try:
        make()
    except Exception as e:
        return type(e).__name__, str(e), getattr(e, "__notes__", None)

def classes():
    del log[:]
    class A(Base, tag=1):
        x = Named("x")
        p = property(lambda self: 1)
        y = Named("drop")
        later = Named("later")
        z = Plain()
        s = Stamp()
    out = [A.p.__name__, "later" in vars(A)]
    class B(A):
        w = Named("w")
    def fail():
        class Fail(Base):
            a = Named("fail")
            b = Named("never")
    def arity():
        class Wrong:
            a = Arity()
    def subclass_fails():
        class Sub(Base, fail=True):
            a = Named("a")
    def no_keywords():
        class Kw(object, tag=2):
            a = Named("kw")
    def cell():
        class Cell(Base):
            def f(self): return __class__
            class Swap:
                def __set_name__(self, owner, name):
                    spin()
                    owner.f.__closure__[0].cell_contents = 7
            swap = Swap()
    out += [error(fail), error(arity), error(subclass_fails), error(no_keywords), error(cell)[:2]]
    out.append(list(log))
    return out

expected = ["p", False,
            ("KeyError", "'a'", ["Error calling __set_name__ on 'Named' instance 'a' in 'Fail'"]),
            ("TypeError", "Arity.__set_name__() takes 1 positional argument but 3 were given",
             ["Error calling __set_name__ on 'Arity' instance 'a' in 'Wrong'"]),
            ("ValueError", "subclass", None),
            ("TypeError", "classes.<locals>.no_keywords.<locals>.Kw.__init_subclass__() takes no keyword arguments", None),
            ("TypeError", "__class__ set to 7 defining 'Cell' as <class 'class_callbacks.classes.<locals>.cell.<locals>.Cell'>"),
            [("set", "x", "A", "x"), ("set", "drop", "A", "y"), ("set", "later", "A", "later"),
             ("plain", "z"), ("static", "s"), ("init_subclass", "A", {"tag": 1}, ["p", "s", "x", "y", "z"]),
             ("set", "w", "B", "w"), ("init_subclass", "B", {}, ["w"]),
             ("set", "fail", "Fail", "a"),
             ("set", "a", "Sub", "a"), ("init_subclass", "Sub", {"fail": True}, ["a"]),
             ("set", "kw", "Kw", "a"), ("init_subclass", "Cell", {}, ["Swap", "f", "swap"])]]

def names(out):
    # The module's name differs by runner; compare from the class's qualname.
    text = out[6][1]
    out[6] = (out[6][0], text.replace(text[text.index("<class '") + 8:text.index("classes.<locals>")], "class_callbacks."))
    return out

assert_eq(names(classes()), expected)
assert_eq(names(classes()), expected)
del log[:]
class Top(Base, top=1):
    t = Named("t")
assert_eq(log, [("set", "t", "Top", "t"), ("init_subclass", "Top", {"top": 1}, ["t"])])
