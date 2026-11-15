# spec: PLS-315 19.3.26, 7.2.5
# description: min() and max() with a key compare each item's key with the
# best key by the key's Python __lt__ or __gt__, or, when its class has
# only object's, by the best key's reflected method first; they test the
# truth of the result by its Python __bool__, which may loop, a true one
# making the item the best. Keys of no comparison raise TypeError, and a
# __bool__ that returns no bool raises TypeError. Iterables and several
# arguments, inside functions and generators as at module level.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class Truth:
    def __init__(self, value): self.value = value
    def __bool__(self):
        spin(); log.append(("bool", self.value))
        return self.value
class Lt:
    def __init__(self, n): self.n = n
    def __lt__(self, other):
        spin(); log.append(("lt", self.n, other.n))
        return Truth(self.n < other.n)
class Gt:
    def __init__(self, n): self.n = n
    def __gt__(self, other):
        spin(); log.append(("gt", self.n, other.n))
        return Truth(self.n > other.n)
class Plain:
    def __init__(self, n): self.n = n

def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def main():
    check(lambda: max([1, 3, 2], key=Lt), 3, [("lt", 1, 3), ("bool", True), ("lt", 3, 2), ("bool", False)])
    check(lambda: min([3, 1, 2], key=Lt), 1, [("lt", 1, 3), ("bool", True), ("lt", 2, 1), ("bool", False)])
    check(lambda: max([1, 3, 2], key=Gt), 3, [("gt", 3, 1), ("bool", True), ("gt", 2, 3), ("bool", False)])
    check(lambda: min([3, 1, 2], key=Gt), 1, [("gt", 3, 1), ("bool", True), ("gt", 1, 2), ("bool", False)])
    check(lambda: (max(1, 3, key=Lt), min(3, 1, key=Gt)), (3, 1), [("lt", 1, 3), ("bool", True), ("gt", 3, 1), ("bool", True)])
    def gen():
        yield max([2, 5], key=Lt)
    check(lambda: list(gen()), [5], [("lt", 2, 5), ("bool", True)])
    assert_raises(TypeError, lambda: max([1, 2], key=Plain), message="'>' not supported between instances of 'Plain' and 'Plain'")
    assert_raises(TypeError, lambda: max([1, 2], key=lambda n: Lt(n) if n == 1 else Lt(Truth(1))),
                  message="'<' not supported between instances of 'int' and 'Truth'")
main()

check(lambda: max([1, 3], key=Lt), 3, [("lt", 1, 3), ("bool", True)])
