# spec: PLS-315 9.3.1, 9.3.2, 19.3.14, 19.3.15
# description: name loads that call a namespace's Python __getitem__ or
# compare a key that is not a str by its Python __eq__ run those calls in
# order: exec() and eval() code with a dict subclass's globals or a
# mapping's locals, at module level, in its functions, comprehensions and
# returns; a class body whose __prepare__ namespace records conditional
# or future annotations (exec()'s globals a dict); a KeyError passes the
# name on to the builtins,
# a missing name raises NameError. Inside functions and generators as at
# module level.
from harness import *
log = []
class Globals(dict):
    def __getitem__(self, key):
        for _ in (): pass
        log.append(("g", key))
        return super().__getitem__(key)
class Locals:
    def __init__(self, **items): self.items = items
    def __getitem__(self, key):
        for _ in (): pass
        log.append(("l", key))
        return self.items[key]
    def __setitem__(self, key, value): self.items[key] = value
class Key:
    def __init__(self, text): self.text = text
    def __hash__(self): return hash(self.text)
    def __eq__(self, other):
        for _ in (): pass
        log.append(("eq", self.text))
        return self.text == other
class Namespace(dict):
    def __getitem__(self, key):
        for _ in (): pass
        log.append(("ns", key))
        return super().__getitem__(key)
class Meta(type):
    @classmethod
    def __prepare__(mcls, name, bases): return Namespace()
def run(f):
    del log[:]
    try: result = f()
    except NameError as error: result = ("NameError", str(error))
    return result, list(log)
def cases():
    g = Globals(y=1, Meta=Meta)
    exec("def f(): return y\ndef c(): return [y for _ in (1, 2)]\n", g)
    return [run(lambda: exec("a = y + 1\nb = len\n", g)), run(lambda: dict.__getitem__(g, "f")()), run(lambda: dict.__getitem__(g, "c")()),
            run(lambda: eval("y", g)), run(lambda: eval("y * 2", {}, Locals(y=3))), run(lambda: eval("len", {}, Locals()) is len),
            run(lambda: exec("q = y", {}, Locals(y=4))), run(lambda: eval("missing", g)),
            run(lambda: eval("v", {Key("v"): 5})), run(lambda: eval("v", {}, {Key("v"): 6})),
            run(lambda: exec("def h(): return w\nr = h()", {Key("w"): 7, "__builtins__": __builtins__})),
            run(lambda: exec("class E(metaclass=Meta):\n    a = y\n    if a:\n        x: int = 1\n", g)),
            run(lambda: exec("from __future__ import annotations\nclass F(metaclass=Meta):\n    z: int = 2\n", {"Meta": Meta}))]
def gen():
    yield cases()
expected = [(None, [('g', 'y'), ('g', 'len')]),
            (1, [('g', 'y')]),
            ([1, 1], [('g', 'y'), ('g', 'y')]),
            (1, [('g', 'y')]),
            (6, [('l', 'y')]),
            (True, [('l', 'len')]),
            (None, [('l', 'y')]),
            (('NameError', "name 'missing' is not defined"), [('g', 'missing')]),
            (5, [('eq', 'v')]),
            (6, [('eq', 'v')]),
            (None, [('eq', 'w')]),
            (None, [('g', 'Meta'), ('ns', '__name__'), ('ns', 'y'), ('ns', 'a')]),
            (None, [('ns', '__name__'), ('ns', '__annotations__'), ('ns', '__annotations__')])]
assert_eq(cases(), expected)
assert_eq(next(gen()), expected)
def outer():
    return cases()
assert_eq(outer(), expected)
