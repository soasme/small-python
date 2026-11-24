# spec: PLS-315 19.3.26, 7.2.4
# description: min() and max() without a key compare each item with the
# best so far by item < best or item > best. When only the best has a
# Python method, the item's builtin one declines and the best's reflected
# method is called; its NotImplemented makes the TypeError name the
# operation as written, the item first; a true result makes the item the
# best. Inside functions as at module level.
from harness import *
log = []
class Declines:
    def __lt__(self, other): log.append(("lt", type(other).__name__)); return NotImplemented
    def __gt__(self, other): log.append(("gt", type(other).__name__)); return NotImplemented
class Ranked:
    def __init__(self, rank): self.rank = rank
    def __lt__(self, other): return self.rank < other
    def __gt__(self, other): return self.rank > other
def messages():
    found = []
    for call in (lambda: max([Declines(), 5]), lambda: min([Declines(), 5]), lambda: max([5, Declines()]), lambda: min([5, Declines()])):
        log.clear()
        try: call()
        except TypeError as e: found.append((str(e), list(log)))
    return found
expected = [("'>' not supported between instances of 'int' and 'Declines'", [("lt", "int")]),
            ("'<' not supported between instances of 'int' and 'Declines'", [("gt", "int")]),
            ("'>' not supported between instances of 'Declines' and 'int'", [("gt", "int")]),
            ("'<' not supported between instances of 'Declines' and 'int'", [("lt", "int")])]
assert_eq(messages(), expected)
log.clear()
try: max(Declines(), 5)
except TypeError as e: top = (str(e), list(log))
assert_eq(top, expected[0])
three = Ranked(3)
assert_eq([max([three, 5]), max([three, 1]) is three, min([three, 1]), min([three, 5]) is three], [5, True, 1, True])
