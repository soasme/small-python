# spec: PLS-315 25.1.4, 19.3.34, 7.5.1
# description: sorted() and list.sort() take reverse's truth by its Python
# __bool__, or __len__ without one, once, after sorted() collects its items
# and before list.sort empties its list or any key call; a __bool__ that
# returns no bool or raises fails the sort, the list unchanged.
from harness import *

log = []
class R:
    def __init__(self, v, lst=None): self.v = v; self.lst = lst
    def __bool__(self):
        for _ in (): pass
        log.append(("bool", None if self.lst is None else list(self.lst)))
        return self.v
class L:
    def __init__(self, n): self.n = n
    def __len__(self): log.append("len"); return self.n
class Bad:
    def __bool__(self): return 1
class Raise:
    def __bool__(self): raise KeyError("r")
class Items:
    def __iter__(self): log.append("iter"); yield 3; yield 1; yield 2
def key(x): log.append(("key", x)); return x

def run(f):
    try: result = f()
    except Exception as e: result = (type(e).__name__, str(e))
    out = (result, list(log))
    log.clear()
    return out

assert_eq(run(lambda: sorted(Items(), key=key, reverse=R(True))),
          ([3, 2, 1], ["iter", ("bool", None), ("key", 3), ("key", 1), ("key", 2)]))
assert_eq(run(lambda: sorted([3, 1, 2], reverse=R(False))), ([1, 2, 3], [("bool", None)]))
assert_eq(run(lambda: sorted([3, 1, 2], reverse=L(2))), ([3, 2, 1], ["len"]))
assert_eq(run(lambda: sorted([3, 1, 2], reverse=L(0))), ([1, 2, 3], ["len"]))
assert_eq(run(lambda: sorted([3, 1, 2], reverse=Bad())), (("TypeError", "Bad.__bool__() must return a bool, not int"), []))
assert_eq(run(lambda: sorted([3, 1, 2], key=key, reverse=Raise())), (("KeyError", "'r'"), []))
assert_eq(run(lambda: sorted([], reverse=R(True))), ([], [("bool", None)]))
lst = [3, 1, 2]
assert_eq(run(lambda: (lst.sort(reverse=R(True, lst)), lst)), ((None, [3, 2, 1]), [("bool", [3, 1, 2])]))
lst = [5, 4, 6]
assert_eq(run(lambda: lst.sort(key=key, reverse=Raise())), (("KeyError", "'r'"), []))
assert_eq(run(lambda: lst.sort(key=key, reverse=Bad())), (("TypeError", "Bad.__bool__() must return a bool, not int"), []))
assert_eq(lst, [5, 4, 6])
assert_eq(run(lambda: (lst.sort(key=key, reverse=L(1)), lst)), ((None, [6, 5, 4]), ["len", ("key", 5), ("key", 4), ("key", 6)]))
class Grow:
    def __bool__(self): lst.append(9); return True
lst = [2, 1]
assert_eq(run(lambda: (lst.sort(reverse=Grow()), lst)), ((None, [9, 2, 1]), []))
