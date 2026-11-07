# spec: PLS-315 16.4.1, 16.4.2
# description: A class statement calls its metaclass with the name, bases
# and namespace, after storing __orig_bases__ for replaced bases: a Python
# __new__ and then the metaclass's __init__ when the result is an instance
# of it, the statement's value whatever __new__ returns; its exception
# propagates, and a __class__ cell left empty or set to another object is
# an error once the class is made. Methods that loop run in function
# statements as at module level, with and without header keywords.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Meta(type):
    def __new__(meta, name, bases, ns, **kwds):
        spin()
        log.append(("new", name, [b.__name__ for b in bases], sorted(k for k in ns if not k.startswith("__")), kwds))
        if name == "Fail": raise KeyError("fail")
        if name == "Number": return 42
        if name == "Dropped": ns = {k: v for k, v in ns.items() if k != "__classcell__"}
        made = super().__new__(meta, name, bases, ns)
        if name == "Twice": super().__new__(meta, name, bases, ns)
        return made
    def __init__(cls, name, bases, ns, **kwds):
        spin()
        log.append(("init", name))

class Base(metaclass=Meta): pass

class Entry:
    def __mro_entries__(self, bases): return (Base,)

def error(make):
    try:
        make()
    except Exception as e:
        return type(e).__name__, str(e)

def classes():
    del log[:]
    class A(Base):
        x = 1
        def who(self): return super().who() if False else __class__.__name__
    class B(A, tag=1): pass
    class C(Entry()): pass
    class Number(Base): pass
    out = [A().who(), type(A).__name__, B.__mro__[1] is A, C.__orig_bases__[0].__class__.__name__, C.__bases__ == (Base,), Number]
    def fail():
        class Fail(Base): pass
    def dropped():
        class Dropped(Base):
            def f(self): return __class__
    def twice():
        class Twice(Base):
            def f(self): return __class__
    out += [error(fail), error(dropped), error(twice)[0]]
    out.append(list(log))
    return out

expected = ["A", "Meta", True, "Entry", True, 42, ("KeyError", "'fail'"),
            ("RuntimeError", "__class__ not set defining 'Dropped' as <class 'metaclass_calls.classes.<locals>.dropped.<locals>.Dropped'>. "
             "Was __classcell__ propagated to type.__new__?"), "TypeError",
            [("new", "A", ["Base"], ["who", "x"], {}), ("init", "A"),
             ("new", "B", ["A"], [], {"tag": 1}), ("init", "B"),
             ("new", "C", ["Base"], [], {}), ("init", "C"),
             ("new", "Number", ["Base"], [], {}),
             ("new", "Fail", ["Base"], [], {}),
             ("new", "Dropped", ["Base"], ["f"], {}), ("init", "Dropped"),
             ("new", "Twice", ["Base"], ["f"], {}), ("init", "Twice")]]

def names(out):
    # The module's name differs by runner; compare from the class's qualname.
    text = out[7][1]
    out[7] = (out[7][0], text.replace(text[text.index("<class '") + 8:text.index("classes.<locals>")], "metaclass_calls."))
    return out

assert_eq(names(classes()), expected)
assert_eq(names(classes()), expected)
del log[:]
class Top(Base): pass
assert_eq([type(Top), log], [Meta, [("new", "Top", ["Base"], [], {}), ("init", "Top")]])
