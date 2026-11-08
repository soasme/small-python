# spec: PLS-315 19.3.35, 7.6.2
# description: sum() adds each item to the total with +: the total's
# __add__ first, which may loop, then on NotImplemented the item's
# __radd__ unless the classes are the same, and an item of a subclass that
# overrides __radd__ goes first; a number total declines to an instance's
# __radd__. The items come from a list, tuple, generator or iterable
# instance, items appended during a call are added, the float total
# before an instance is compensated, a start instance is the first total,
# and a method's exceptions propagate, as do sum()'s own errors, inside functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Operand:
    def __init__(self, tag): self.tag = tag
    def __add__(self, other):
        spin()
        log.append(("add", self.tag))
        if self.tag == "bad": raise KeyError("add")
        return NotImplemented if self.tag == "no" else Operand(self.tag + "+")
    def __radd__(self, other):
        spin()
        log.append(("radd", self.tag, other if not isinstance(other, Operand) else other.tag))
        if self.tag == "grow": items.append(Operand("late"))
        return NotImplemented if self.tag == "rno" else Operand(self.tag + "r")

class Derived(Operand):
    def __radd__(self, other):
        spin()
        log.append(("derived", self.tag))
        return Operand("derived")

class Other:
    def __radd__(self, other):
        spin()
        log.append(("other", type(other).__name__))
        return 7

class Plain: pass

class Arity:
    def __radd__(self): spin()

class Iterable:
    def __iter__(self): return iter([Operand("i"), Operand("j")])

def generate():
    yield Operand("g")
    yield 1
    yield Operand("h")

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def tag(v): return v.tag if isinstance(v, Operand) else v

items = []

def results():
    global items
    del log[:]
    items = [1, Operand("grow")]
    out = [tag(sum([Operand("a")])), tag(sum((1, 2, Operand("b")))), tag(sum([Operand("c"), 3])),
           tag(sum([0.25, 1e100, 1.0, -1e100, Operand("f")])), tag(sum([Operand("s")], Operand("t"))),
           tag(sum(generate())), tag(sum(Iterable())), tag(sum(items)), sum([Other()], Operand("no")),
           tag(sum([Derived("e")], Operand("x"))),
           error(lambda: sum([Operand("y")], Operand("no"))), error(lambda: sum([Operand("rno")])),
           error(lambda: sum([1], Operand("bad"))), error(lambda: sum([Plain()])), error(lambda: sum([1, "a"])),
           error(lambda: sum([Arity()], Operand("no"))), error(lambda: sum(["a"], "")), error(lambda: sum())]
    out.append(list(log))
    return out

expected = ["ar", "br", "cr+", "fr", "t+", "gr++", "ir+", "growr+", 7, "derived",
            ("TypeError", "unsupported operand type(s) for +: 'Operand' and 'Operand'"),
            ("TypeError", "unsupported operand type(s) for +: 'int' and 'Operand'"),
            ("KeyError", "'add'"),
            ("TypeError", "unsupported operand type(s) for +: 'int' and 'Plain'"),
            ("TypeError", "unsupported operand type(s) for +: 'int' and 'str'"),
            ("TypeError", "Arity.__radd__() takes 1 positional argument but 2 were given"),
            ("TypeError", "sum() can't sum strings [use ''.join(seq) instead]"),
            ("TypeError", "sum() takes at least 1 positional argument (0 given)"),
            [("radd", "a", 0), ("radd", "b", 3), ("radd", "c", 0), ("add", "cr"), ("radd", "f", 1.25),
             ("add", "t"), ("radd", "g", 0), ("add", "gr"), ("add", "gr+"),
             ("radd", "i", 0), ("add", "ir"), ("radd", "grow", 1), ("add", "growr"),
             ("add", "no"), ("other", "Operand"), ("derived", "e"),
             ("add", "no"), ("radd", "rno", 0), ("add", "bad"), ("add", "no")]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
