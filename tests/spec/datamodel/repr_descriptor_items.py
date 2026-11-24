# spec: PLS-315 3.3.1, 26, 27.1.5
# description: The repr of a list, tuple, dict or set shows an item whose
# class's __repr__ is a descriptor by reading it with its Python __get__,
# which may loop, and calling what it gives, item by item in order, by
# repr(), str() and format() alike, for an instance or a class whose
# metaclass holds it. An AttributeError from __get__ gives the default
# repr; any other exception propagates, as does a result that is not a str.
from harness import *

log = []
def spin():
    for _ in range(2): pass
class Showing:
    def __get__(self, obj, owner):
        spin(); tag = obj.__name__ if isinstance(obj, type) else obj.tag; log.append(tag)
        if tag == "attr": raise AttributeError("gone")
        if tag == "value": raise ValueError("get")
        if tag == "int": return lambda: 5
        return lambda: "<%s>" % tag
class Item:
    __repr__ = Showing()
    def __init__(self, tag): self.tag = tag
class Meta(type):
    __repr__ = Showing()
class Shown(metaclass=Meta): pass

def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def cases():
    a, b = Item("a"), Item("b")
    return [run(lambda: repr([a, (b,)])), run(lambda: str({a: b})), run(lambda: format((Shown, a))), run(lambda: repr({a})),
            run(lambda: f"{[b]}"), run(lambda: repr([Item("attr")]).startswith("[<Item object at ")),
            run(lambda: repr([a, Item("value"), b])), run(lambda: str([Item("int")]))]
expected = [("[<a>, (<b>,)]", ["a", "b"]), ("{<a>: <b>}", ["a", "b"]), ("(<Shown>, <a>)", ["Shown", "a"]), ("{<a>}", ["a"]),
            ("[<b>]", ["b"]), (True, ["attr"]), (("ValueError", "get"), ["a", "value"]),
            (("TypeError", "Item.__repr__() must return a str, not int"), ["int"])]
assert_eq(cases(), expected)
assert_eq(cases(), expected)
