# spec: PLS-315 25.5.2, 25.1.3, 7.2.5
# description: index, count and remove of one item in a list, and index and
# count in a tuple, compare the items in order, each by RichCompareBool with
# the item on the left, calling an item's or the needle's Python __eq__,
# which may loop; identical items match without a call. index and remove
# stop at the first match, count compares every item, and a missing item
# raises ValueError. Exceptions from __eq__ propagate, items the comparisons
# add or remove are seen as they are read, and remove deletes nothing past
# the end, inside functions as at module level and for any call form.
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
            items.append(Item("added", 2))
        if self.tag == "shrink":
            del items[:]
        return getattr(other, "key", other) == self.key

class Arity:
    def __eq__(self): spin()

class Plain:
    def __init__(self, tag): self.tag = tag

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def get():
    return items

def results():
    global items
    del log[:]
    a, b = Item("a"), Item("b", 1)
    items = [1, a, "s", b, 2, Item("c", 1)]
    out = [items.index(1), items.index(a), items.count(1)]
    out += [get().index(1), get().count(0), items.index(1, 2), [Item("i", 5)].index(5)]
    t = (a, b, 3, Item("d", 1))
    out += [t.index(1), t.count(1), t.count(a), (1, 2).index(2)]
    out += [error(lambda: items.index(9)), error(lambda: t.index(Plain("q"))), error(lambda: items.remove(9)),
            error(lambda: [Item("bad")].count(1)), error(lambda: [Arity()].index(1))]
    for i in range(2):
        out.append([items.index(1), items.count(1)])
    items.remove(1)
    out.append([x if type(x) is not Item else x.tag for x in items])
    items = [Item("grow"), 2]
    out += [items.index(2), len(items)]
    items = [Item("shrink", 5), 5]
    out += [items.index(5), items]
    items = [Item("shrink", 5), 5]
    items.remove(5)
    out.append(items)
    out.append(list(log))
    return out

expected = [0, 1, 3, 0, 1, 3, 0, 1, 2, 1, 1,
            ("ValueError", "list.index(x): x not in list"), ("ValueError", "tuple.index(x): x not in tuple"),
            ("ValueError", "list.remove(x): x not in list"), ("KeyError", "'eq'"),
            ("TypeError", "Arity.__eq__() takes 1 positional argument but 2 were given"),
            [0, 3], [0, 3], ["a", "s", "b", 2, "c"], 1, 3, 0, [], [],
            [("a", 1), ("a", 1), ("b", 1), ("c", 1), ("a", 0), ("b", 0), ("c", 0), ("b", 1), ("i", 5),
             ("a", 1), ("b", 1), ("a", 1), ("b", 1), ("d", 1), ("b", "a"), ("a", 3), ("d", "a"),
             ("a", 9), ("b", 9), ("c", 9), ("a", "q"), ("b", "q"), ("d", "q"), ("a", 9), ("b", 9), ("c", 9),
             ("bad", 1), ("a", 1), ("b", 1), ("c", 1), ("a", 1), ("b", 1), ("c", 1),
             ("grow", 2), ("shrink", 5), ("shrink", 5)]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
