# spec: PLS-315 25.5.3, 7.2.5, 7.2.4
# description: == and != of two lists or two tuples compare their items in
# order by RichCompareBool, calling an item's Python __eq__, which may loop,
# until a pair is unequal; identical items call nothing, and lists of
# different lengths or sequences of different kinds compare no items, while
# tuples of different lengths compare their common items first. A
# subclass's reflected __eq__ comes first, NotImplemented falls back to the
# other operand's and then to identity, an __eq__'s result is tested for
# truth, and exceptions from __eq__ or that test propagate. Items the
# comparison adds or removes are seen as it reads them, and an unequal pair
# left past an end compares the lengths, also in a comparison chain, inside
# functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Item:
    def __init__(self, tag, key=0): self.tag, self.key = tag, key
    def __eq__(self, other):
        spin()
        log.append((self.tag, getattr(other, "tag", other)))
        if self.tag == "bad":
            raise KeyError("eq")
        if self.tag == "grow":
            left.append(9)
        if self.tag == "shrink":
            del right[-1]
        return getattr(other, "key", other) == self.key

class Sub(Item):
    def __eq__(self, other):
        log.append(("sub", self.tag))
        return Item.__eq__(self, other)

class Declines:
    def __init__(self, tag): self.tag = tag
    def __eq__(self, other):
        spin()
        log.append(("declines", self.tag))
        return NotImplemented

class Clears:
    def __init__(self, side): self.side = side
    def __eq__(self, other):
        spin()
        (left if self.side == "left" else right).clear()
        return NotImplemented

class Arity:
    def __eq__(self): spin()

class Truth:
    def __init__(self, value): self.value = value
    def __bool__(self):
        spin()
        if self.value == "bad":
            raise ValueError("bool")
        return self.value

class Odd:
    def __init__(self, result): self.result = result
    def __eq__(self, other):
        spin()
        return Truth(self.result)

def arity():
    a, b = [Arity()], [1]
    return a == b

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    global left, right
    del log[:]
    a, b, same = Item("a"), Item("b"), Item("same")
    left, right = [1, a, "s", b], [1, Item("x"), "s", Item("y")]
    out = [left == right, left != right]
    right[3] = Item("z", 1)
    out += [left == right, left != right]
    out += [[same] == [same], (a, b) == (Item("p"), Item("q")), (a,) != (Item("r", 1),),
            [a] == (a,), [a] == [a, b], [a, 2] == [Item("t"), 3], (a,) == (Item("o"), 1), (Item("o2", 1),) != (a, 1)]
    out += [[Item("u")] == [Sub("v")], [Declines("d")] == [Declines("e")],
            [d := Declines("f")] == [d], [Odd(False)] == [1], [Odd(True)] != [1]]
    out += [error(lambda: [Item("bad")] == [1]), error(lambda: [Odd("bad")] == [1]), error(arity)]
    left, right = [Item("grow"), 2], [0, 2]
    out += [left == right, len(left)]
    left, right = [Item("shrink"), 1], [0, 1]
    out += [left == right, right]
    left, right = [Item("w"), Item("w2"), 3], [0, 0, 3]
    x, y = left, right
    out += [x == y, x != y]
    left, right = [Clears("right")], [Clears("left")]
    out += [left == right, left, right]
    left, right = [Clears("right"), 1], [Clears("left"), 2]
    out += [left != right]
    p, q, r = [Item("c1")], [Item("c2")], [Item("c3", 1)]
    t1, t2, t3 = (Item("c4"),), (Item("c5"),), (Item("c6"),)
    out += [p == q == q, p == q != r, p == r == q, t1 == t2 == t3, [1] < [2] == [2], "yes" if p == q == q else "no"]
    out.append(list(log))
    return out

expected = [True, False, False, True,
            True, True, True, False, False, False, False, True,
            True, False, True, False, False,
            ("KeyError", "'eq'"), ("ValueError", "bool"),
            ("TypeError", "Arity.__eq__() takes 1 positional argument but 2 were given"),
            False, 3, False, [0], True, False, True, [], [], False,
            True, True, False, True, True, "yes",
            [("a", "x"), ("b", "y"), ("a", "x"), ("b", "y"), ("a", "x"), ("b", "z"), ("a", "x"), ("b", "z"),
             ("a", "p"), ("b", "q"), ("a", "r"), ("a", "t"), ("a", "o"), ("o2", "a"), ("sub", "v"), ("v", "u"),
             ("declines", "d"), ("declines", "e"), ("bad", 1), ("grow", 0), ("shrink", 0),
             ("w", 0), ("w2", 0), ("w", 0), ("w2", 0),
             ("c1", "c2"), ("c1", "c2"), ("c2", "c3"), ("c1", "c3"), ("c4", "c5"), ("c5", "c6"), ("c1", "c2")]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
