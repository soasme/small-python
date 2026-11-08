# spec: PLS-315 19.3.26, 7.2.4
# description: min() and max() of a list or tuple, or of two or more
# arguments, keep the first least or greatest item, comparing each later
# item with the best so far by < or >, which calls the item's Python __lt__
# or __gt__, which may loop, or the best's reflected method when the best's
# class is a subclass of the item's or the item declines; NotImplemented
# from both raises TypeError, an exception propagates, and items added or
# removed meanwhile are seen as they are read, inside functions as at
# module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Rank:
    def __init__(self, tag, v): self.tag, self.v = tag, v
    def __lt__(self, other):
        spin()
        log.append((self.tag, "<", getattr(other, "tag", other)))
        if self.tag == "bad":
            raise KeyError("lt")
        if self.tag == "grow":
            items.append(Rank("added", -5))
        if self.tag == "shrink":
            del items[2:]
        return self.v < getattr(other, "v", other)
    def __gt__(self, other):
        spin()
        log.append((self.tag, ">", getattr(other, "tag", other)))
        return self.v > getattr(other, "v", other)

class Sub(Rank): pass

class Declines:
    def __lt__(self, other): return NotImplemented
    def __gt__(self, other): return NotImplemented

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

class Arity:
    def __lt__(self): spin()

def get(*values): return list(values) or items

def tags(r): return r.tag if isinstance(r, Rank) else r

def results():
    global items
    del log[:]
    a, b, c, d = Rank("a", 3), Rank("b", 1), Rank("c", 1), Rank("d", 5)
    items = [a, b, c, d]
    out = [tags(min(items)), tags(max(get())), tags(min(a, b)), tags(max(b, c, get(d)[0])), tags(min((d, a))),
           tags(min(get(a, Sub("s", 0)))), tags(min([Sub("t", 5), a])), tags(max(get(2, Rank("r", 4)))), tags(min([0, Rank("z", 4)])),
           tags(min(get(3, 1, 2, Rank("w", 0))))]
    out += [error(lambda: min([Rank("bad", 0), a])), error(lambda: min(get(a, Rank("bad", 0)))),
            error(lambda: min(get(Declines(), Declines()))), tags(min(get(a))), error(lambda: min([])),
            error(lambda: min(get(Arity(), Arity())))]
    items = [Rank("x", 2), Rank("grow", 1)]
    out.append(tags(min(get())))
    items = [Rank("y", 2), Rank("shrink", 1), Rank("gone", 0)]
    out.append(tags(min(get())))
    out.append(list(log))
    return out

expected = ["b", "d", "b", "d", "a", "s", "a", "r", 0, "w", None, ("KeyError", "'lt'"),
            ("TypeError", "'<' not supported between instances of 'Declines' and 'Declines'"), "a",
            ("ValueError", "min() iterable argument is empty"),
            ("TypeError", "Arity.__lt__() takes 1 positional argument but 2 were given"), "added", "shrink",
            [("b", "<", "a"), ("c", "<", "b"), ("d", "<", "b"), ("b", ">", "a"), ("c", ">", "a"), ("d", ">", "a"),
             ("b", "<", "a"), ("c", ">", "b"), ("d", ">", "b"), ("a", "<", "d"), ("s", "<", "a"), ("t", ">", "a"),
             ("r", ">", 2), ("z", "<", 0), ("w", "<", 1), ("a", "<", "bad"), ("bad", "<", "a"), ("grow", "<", "x"),
             ("added", "<", "grow"), ("shrink", "<", "y")]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
