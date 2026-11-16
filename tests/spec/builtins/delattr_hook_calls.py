# spec: PLS-315 19.3.11, 7.3.9
# description: delattr() of an instance and a str calls its class's
# Python __delattr__, which may loop, given the name, or a property's
# deleter or a data descriptor's __delete__ given the instance, as del
# does; their exceptions propagate, a property without a deleter raises
# AttributeError, and a non-str name raises TypeError. Inside functions
# as at module level.
from harness import *

log = []
class H:
    def __delattr__(self, n):
        for _ in range(2): pass
        log.append(("del", n))
        if n == "bad": raise LookupError(n)
        object.__delattr__(self, n)
class P:
    @property
    def p(self): return 1
    @p.deleter
    def p(self): log.append("deleter")
class D:
    def __get__(self, i, o): return 1
    def __set__(self, i, v): pass
    def __delete__(self, i): log.append(("delete", type(i).__name__))
class Q:
    d = D()
class RO:
    @property
    def r(self): return 1
class S(str): pass
def t(f):
    try: r = f()
    except Exception as e: r = type(e).__name__ + ": " + str(e)
    out = (r, log[:]); del log[:]; return out
def results():
    h = H(); h.x = 1
    plain = H.__new__(Q)
    return [t(lambda: delattr(h, "x")), t(lambda: (delattr(h, "x"), 1)), t(lambda: delattr(h, "bad")), t(lambda: delattr(P(), "p")),
            t(lambda: delattr(Q(), "d")), t(lambda: delattr(RO(), "r")), t(lambda: delattr(h, S("y"))), t(lambda: delattr(h)),
            t(lambda: [delattr(P(), "p"), delattr(Q(), "d")]), t(lambda: delattr(plain, "zz")), t(lambda: delattr(h, 1))]

expected = [(None, [('del', 'x')]), ("AttributeError: 'H' object has no attribute 'x'", [('del', 'x')]),
            ('LookupError: bad', [('del', 'bad')]), (None, ['deleter']), (None, [('delete', 'Q')]),
            ("AttributeError: property 'r' of 'RO' object has no deleter", []),
            ("AttributeError: 'H' object has no attribute 'y'", [('del', 'y')]),
            ('TypeError: delattr expected 2 arguments, got 1', []), ([None, None], ['deleter', ('delete', 'Q')]),
            ("AttributeError: 'Q' object has no attribute 'zz'", []),
            ("TypeError: attribute name must be string, not 'int'", [])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
