# spec: PLS-315 25.1.4, 19.3.34, 19.3.26
# description: A sort, min or max key may be a class, whose new instance
# initialized from each item is that item's key, a bound method or a
# callable instance, called once per item in order; an __init__ returning
# anything but None raises TypeError, an exception from it leaves the list
# as it was, and a key whose class changes its call while sorting is
# called as it now is. min and max compare instance keys with the best
# one's by the key's Python method, then on NotImplemented by the best
# key's reflected one, raising TypeError when both decline. So do calls
# passing their arguments by * and **, a str subclass naming the keyword.
from harness import *

log = []

def spin():
    for _ in range(3): pass

class Rank:
    def __init__(self, v):
        spin()
        log.append(("init", v))
        self.v = v % 3
    def __lt__(self, other): return self.v < other.v

class Weigher:
    def __init__(self, w): self.w = w
    def weigh(self, v):
        spin()
        log.append(("weigh", v))
        return v * self.w
    def __call__(self, v):
        spin()
        log.append(("call", v))
        return -v

class Bad:
    def __init__(self, v): return v

class Failing:
    def __init__(self, v):
        if v == 2: raise KeyError(v)
        self.v = v

class Changing:
    def __init__(self, v):
        log.append(("changing", v))
        del Changing.__init__
        self.v = v
    def __lt__(self, other): return self.v < other.v

class Switch:
    def __call__(self, v):
        log.append(("switch", v))
        Switch.__call__ = abs
        return v

class Name(str): pass

class Picky:
    def __init__(self, v): spin(); self.v = v
    def __lt__(self, other):
        spin()
        log.append(("lt", self.v, other.v))
        if self.v == 9: raise KeyError(9)
        return NotImplemented if 0 in (self.v, other.v) else self.v < other.v
    def __gt__(self, other):
        log.append(("gt", self.v, other.v))
        return NotImplemented

class Lazy(Picky):
    def __gt__(self, other): return NotImplemented

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    xs = [5, 3, 4]
    xs.sort(key=Rank)
    w = Weigher(-1)
    out = [xs, sorted([1, 3, 2], key=w.weigh), sorted([1, 3, 2], key=w), sorted([4, 2, 9], key=Rank, reverse=True),
           max([1, 3, 2], key=w.weigh), min([1, 3, 2], key=w), max(1, 3, 2, key=w), min([7], key=Rank)]
    ys = [3, 2, 1]
    out += [error(lambda: sorted([1, 2], key=Bad)), error(lambda: ys.sort(key=Failing)), ys,
            error(lambda: sorted([2, 1, 3], key=Changing)), sorted([-3, 2, -1], key=Switch()),
            max([3, 1, 2], key=Picky), min([2, 1], key=Picky), error(lambda: max([1, 0], key=Picky)),
            error(lambda: min([1, 9], key=Picky)), error(lambda: min([1, 0], key=Lazy))]
    zs = [2, 3, 1]
    zs.sort(*(), **{"key": w.weigh})
    out += [zs, sorted(*[[5, 3]], **{Name("key"): Rank}), max(*[[1, 3]], **{"key": w})]
    out.append(list(log))
    return out

expected = [[3, 4, 5], [3, 2, 1], [3, 2, 1], [2, 4, 9], 1, 3, 1, 7,
            ("TypeError", "__init__() should return None, not 'int'"), ("KeyError", "2"), [3, 2, 1],
            ("TypeError", "Changing() takes no arguments"), [-3, -1, 2], 3, 1,
            ("TypeError", "'>' not supported between instances of 'Picky' and 'Picky'"), ("KeyError", "9"),
            ("TypeError", "'<' not supported between instances of 'Lazy' and 'Lazy'"), [3, 2, 1], [3, 5], 1,
            [("init", 5), ("init", 3), ("init", 4), ("weigh", 1), ("weigh", 3), ("weigh", 2), ("call", 1), ("call", 3),
             ("call", 2), ("init", 4), ("init", 2), ("init", 9), ("weigh", 1), ("weigh", 3), ("weigh", 2), ("call", 1),
             ("call", 3), ("call", 2), ("call", 1), ("call", 3), ("call", 2), ("init", 7), ("changing", 2), ("switch", -3),
             ("gt", 1, 3), ("lt", 3, 1), ("gt", 2, 3), ("lt", 3, 2), ("lt", 1, 2), ("gt", 0, 1), ("lt", 1, 0), ("lt", 9, 1),
             ("lt", 0, 1), ("weigh", 2), ("weigh", 3), ("weigh", 1), ("init", 5), ("init", 3), ("call", 1), ("call", 3)]]

def main():
    return results()

assert_eq(main(), expected)
Switch.__call__ = lambda self, v: (log.append(("switch", v)), setattr(Switch, "__call__", abs), v)[2]
def changing_init(self, v):
    log.append(("changing", v))
    del Changing.__init__
    self.v = v
Changing.__init__ = changing_init
assert_eq(results(), expected)
