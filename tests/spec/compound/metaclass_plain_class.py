# spec: PLS-315 16.4.2
# description: a class statement whose metaclass is a plain class, not a
# subclass of type, calls it as any class is called: object.__new__ makes
# an instance of it, and its Python __init__, which may loop or raise,
# receives the name, bases, namespace and keywords; that instance is what
# the statement binds. A base whose metaclass is type is a metaclass
# conflict (CalculateMetaclass), raised before Meta is called.
from harness import assert_eq

log = []

class Meta:
    def __init__(self, name, bases, ns, **kw):
        for _ in (): pass
        if kw.get("fail"): raise LookupError(name)
        self.made = (name, bases, sorted(k for k in ns if not k.startswith("__")), kw)
        log.append(name)

class Base: pass

def run():
    class C(metaclass=Meta, x=1):
        a = 1
        def f(self): pass
    class D(metaclass=Meta): pass
    try:
        class G(Base, metaclass=Meta): pass
    except TypeError as e:
        conflict = str(e)
    try:
        class E(metaclass=Meta, fail=True): pass
    except LookupError as e:
        failed = e.args
    return type(C).__name__, C.made, D.made, conflict, failed

assert_eq(run(), ("Meta", ("C", (), ["a", "f"], {"x": 1}), ("D", (), [], {}),
                  "metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases",
                  ("E",)))
assert_eq(log, ["C", "D"])
