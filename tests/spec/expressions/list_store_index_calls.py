# spec: PLS-315 25.5.4, 25.5.1
# description: an item assignment to, a deletion from, or an augmented
# assignment of an item of a list or a list's subclass, by an instance with
# a Python __index__, calls __index__ once and uses the int it returns; a
# non-int result, an index outside the index-size range, naming the key's
# type, or outside the list, raises; inside functions as at module level.
from harness import *

log = []

class X:
    def __init__(self, i): self.i = i
    def __index__(self):
        for _ in (): pass
        log.append(self.i)
        return self.i

class Big:
    def __index__(self):
        for _ in (): pass
        return 1 << 70

class Text:
    def __index__(self):
        for _ in (): pass
        return "s"

class L(list): pass

def stores():
    s = [0, 1, 2, 3]
    s[X(1)] = 9
    k = X(-1)
    s[k] = 8
    del s[X(0)]
    t = L([5, 6])
    t[X(0)] = 7
    del t[X(1)]
    x = s[X(0)] = 4
    holder = [s]
    holder[0][X(2)] += 100
    return [s, t, x, log[:]]

assert_eq(stores(), [[4, 2, 108], [7], 4, [1, -1, 0, 0, 1, 0, 2, 2]])
log.clear()
s = [1, 2]
s[X(0)] = 5
del s[X(1)]
assert_eq((s, log), ([5], [0, 1]))

def errors():
    s = [1, 2]
    out = []
    for key in (Big(), Text(), X(5)):
        try: s[key] = 0
        except (IndexError, TypeError) as e: out.append((type(e).__name__, str(e)))
        try: del s[key]
        except (IndexError, TypeError) as e: out.append((type(e).__name__, str(e)))
    return out

assert_eq(errors(), [
    ("IndexError", "cannot fit 'Big' into an index-sized integer"),
    ("IndexError", "cannot fit 'Big' into an index-sized integer"),
    ("TypeError", "Text.__index__() must return an int, not str"),
    ("TypeError", "Text.__index__() must return an int, not str"),
    ("IndexError", "list assignment index out of range"),
    ("IndexError", "list assignment index out of range"),
])
