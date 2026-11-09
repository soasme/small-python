# spec: PLS-315 16.4.1, 16.4.2
# description: A class statement replaces each base that is not a class
# and has __mro_entries__ by the tuple it returns given the original
# bases, in order, keeping other bases, whether it is a method, a
# callable instance or a generic alias's; the original bases are kept as
# __orig_bases__, a result that is not a tuple raises TypeError, and an
# exception propagates, whether the body calls or only assigns, inside
# functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Base: pass
class Other: pass

class Entry:
    def __init__(self, *entries): self.entries = entries
    def __mro_entries__(self, bases):
        spin()
        log.append((len(bases), [b.__name__ for b in self.entries]))
        return self.entries

class Caller:
    def __call__(self, bases): return (Other,)

class Called:
    __mro_entries__ = Caller()

class Bad:
    def __mro_entries__(self, bases): return [Base]

class Raise:
    def __mro_entries__(self, bases):
        spin()
        raise KeyError("entries")

def error(make):
    try:
        return make()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    first = Entry(Base, Other)
    class A(first, Entry()):
        x = 1
    class B(Base, Entry(Other)):
        spin()
    class C(Called()): pass
    class D(list[int]):
        y = 2
    def bad():
        class E(Bad()): pass
    def raised():
        class F(Base, Raise()): spin()
    return [[k.__name__ for k in A.__mro__], A.__orig_bases__[0] is first, len(A.__orig_bases__), [k.__name__ for k in B.__bases__],
            C.__bases__ == (Other,), D.__bases__ == (list,), D.__orig_bases__ == (list[int],), D([3]) + [D.y],
            error(bad), error(raised), "__orig_bases__" in Base.__dict__, list(log)]

expected = [['A', 'Base', 'Other', 'object'], True, 2, ['Base', 'Other'], True, True, True, [3, 2],
            ('TypeError', '__mro_entries__ must return a tuple'), ('KeyError', "'entries'"), False,
            [(2, ['Base', 'Other']), (2, []), (2, ['Other'])]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
