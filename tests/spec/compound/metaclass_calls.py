# spec: PLS-315 16.4.1, 16.4.2
# description: A class statement calls its metaclass with the name, bases
# and namespace, after storing __orig_bases__ for replaced bases: a Python
# __new__ and then the metaclass's __init__ when the result is an instance
# of it, the statement's value whatever __new__ returns; its exception
# propagates, and a __class__ cell left empty or set to another object is
# an error once the class is made. Methods that loop run in function
# statements as at module level, with and without header keywords, which
# both __new__ and __init__ receive; a __new__ that takes none rejects them.
# A metaclass of type's __new__ and a Python __init__ initializes the class
# made, whose __init__ must return None.
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
        log.append(("init", name) + ((kwds,) if kwds else ()))

class Strict(type):
    def __new__(meta, name, bases, ns):
        spin()
        return super().__new__(meta, name, bases, ns)

class Init(type):
    def __init__(cls, name, bases, ns, **kwds):
        spin()
        log.append(("Init", name, cls.__mro__[1].__name__, kwds))
        if name == "Returning": return 5

class Keyed:
    def __init_subclass__(cls, **kwds): pass

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
    def strict():
        class S(metaclass=Strict, tag=2): pass
    class I(Keyed, metaclass=Init, tag=3):
        def f(self): return __class__
    class J(I): pass
    def returning():
        class Returning(metaclass=Init): pass
    out += [error(fail), error(dropped), error(twice)[0], error(strict), I().f() is I, type(J) is Init, error(returning)]
    out.append(list(log))
    return out

expected = ["A", "Meta", True, "Entry", True, 42, ("KeyError", "'fail'"),
            ("RuntimeError", "__class__ not set defining 'Dropped' as <class 'metaclass_calls.classes.<locals>.dropped.<locals>.Dropped'>. "
             "Was __classcell__ propagated to type.__new__?"), "TypeError",
            ("TypeError", "Strict.__new__() got an unexpected keyword argument 'tag'"), True, True,
            ("TypeError", "__init__() should return None, not 'int'"),
            [("new", "A", ["Base"], ["who", "x"], {}), ("init", "A"),
             ("new", "B", ["A"], [], {"tag": 1}), ("init", "B", {"tag": 1}),
             ("new", "C", ["Base"], [], {}), ("init", "C"),
             ("new", "Number", ["Base"], [], {}),
             ("Init", "I", "Keyed", {"tag": 3}), ("Init", "J", "I", {}),
             ("new", "Fail", ["Base"], [], {}),
             ("new", "Dropped", ["Base"], ["f"], {}), ("init", "Dropped"),
             ("new", "Twice", ["Base"], ["f"], {}), ("init", "Twice"),
             ("Init", "Returning", "object", {})]]

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
