# spec: PLS-315 13.3.1, 13.3.4, 10.2.1
# description: A class read as an attribute of a class, an instance or a
# namespace, each computed, and called there runs its Python __new__ and
# __init__, which
# may loop, as a call of the class does: the instance __new__ returns is
# initialized only when it is the class's; a metaclass's Python __call__
# replaces both; so does an instance's Python __call__ for an instance
# read as the attribute. An exception from any of them, or from binding
# their arguments, propagates.
from harness import *

log = []
def spin():
    for _ in range(2): pass
class Meta(type):
    def __call__(cls, *args):
        spin(); log.append(("meta", args)); return "made"
class Holder:
    class Plain:
        def __init__(self, x):
            spin(); log.append(("init", x)); self.x = x
    class Fresh:
        def __new__(cls, x):
            spin(); log.append(("new", x))
            return 42 if x == "other" else super().__new__(cls)
        def __init__(self, x):
            spin(); log.append(("init", x))
    class Failing:
        def __init__(self): spin(); raise LookupError("init")
    class Called(metaclass=Meta): pass
class Handler:
    def __call__(self, *args):
        spin(); log.append(("call", args)); return len(args)
class Strict:
    def __call__(self, a): spin(); log.append(("strict", a))
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
h = Holder()
class Namespace: pass
ns = Namespace(); ns.Plain = Holder.Plain; ns.handler = Handler(); ns.strict = Strict()
box = [Holder, h, ns]
def get(): return h
def cases():
    return [run(lambda: box[0].Plain(1).x), run(lambda: get().Plain(2).x), run(lambda: box[2].Plain(3).x),
            run(lambda: type(get().Fresh("a")).__name__), run(lambda: box[1].Fresh("other")),
            run(lambda: box[0].Failing()), run(lambda: box[0].Called(1, 2)), run(lambda: box[2].handler(1, 2, 3)),
            run(lambda: box[2].strict(1, 2))]
expected = [(1, [("init", 1)]), (2, [("init", 2)]), (3, [("init", 3)]), ("Fresh", [("new", "a"), ("init", "a")]),
            (42, [("new", "other")]), (("LookupError", "init"), []), ("made", [("meta", (1, 2))]), (3, [("call", (1, 2, 3))]),
            (("TypeError", "Strict.__call__() takes 2 positional arguments but 3 were given"), [])]
assert_eq(cases(), expected)
assert_eq([run(lambda: box[0].Plain(1).x), run(lambda: get().Plain(2).x)], expected[:2])
