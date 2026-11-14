# spec: PLS-315 7.6.2, 7.6.3, 7.6.4, 7.2.4, 7.8.3, 29.5.1
# description: binary, in-place and unary operators, comparisons and in of
# an instance of a builtin type's subclass call the Python methods its
# class defines before the builtin type, and of a class those of its
# metaclass, in the order of plain instances: a right operand's subclass
# overriding the reflected method goes first, also of a builtin left
# operand, but after a set's or dict's in-place operator, and the builtin's
# own operation follows a method that declines;
# | of classes whose metaclass keeps type's __or__ makes a union; an int's
# subclass indexes by its int; inside functions as at module level.
from harness import *

log = []
def note(*a): log.append(a)
class I(int):
    def __add__(self, o):
        for _ in range(1): pass
        note("I.add", o); return NotImplemented if o == 99 else ("I+", o)
    def __radd__(self, o): note("I.radd", o); return ("+I", o)
    def __sub__(self, o): note("I.sub", o); return NotImplemented
    def __eq__(self, o): note("I.eq", o); return NotImplemented if o == 5 else "eq"
    def __lt__(self, o): note("I.lt", o); return NotImplemented
    def __neg__(self): note("I.neg"); return "neg"
    def __invert__(self): return NotImplemented
    __hash__ = int.__hash__
class J(I):
    def __radd__(self, o): note("J.radd", o); return ("+J", o)
    def __gt__(self, o): note("J.gt", o); return "gt"
class S(str):
    def __mul__(self, o): note("S.mul", o); return NotImplemented
    def __rmod__(self, o): note("S.rmod", o); return "rmod"
    def __ne__(self, o): note("S.ne", o); return "ne"
    def __contains__(self, x): note("S.in", x); return 0
class L(list):
    def __iadd__(self, o): note("L.iadd", o); return NotImplemented
    def __add__(self, o): note("L.add", o); return "L+"
    def __eq__(self, o): note("L.eq"); return True
class F(float):
    def __pow__(self, o, m=None): note("F.pow", o); return "pow"
    def __rtruediv__(self, o): note("F.rdiv", o); return "rdiv"
class M(type):
    def __add__(cls, o): note("M.add", o); return "M+"
    def __radd__(cls, o): note("M.radd", o); return "+M"
    def __eq__(cls, o): note("M.eq"); return NotImplemented
    def __lt__(cls, o): note("M.lt"); return "lt"
    def __neg__(cls): note("M.neg"); return "Mneg"
    def __contains__(cls, x): note("M.in", x); return True
    __hash__ = type.__hash__
class C(metaclass=M): pass
class D(metaclass=M): pass
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
cases = [
    lambda: I(1) + 2, lambda: I(1) + 99, lambda: 2 + I(1), lambda: I(1) + J(2), lambda: J(2) + I(1), lambda: I(1) - 1,
    lambda: 1 - I(1), lambda: I(1) == 3, lambda: I(1) == 5, lambda: 3 == I(1), lambda: I(1) != 3, lambda: I(1) != 5,
    lambda: I(1) < 2, lambda: 2 < I(1), lambda: I(1) < J(1), lambda: J(1) > I(0), lambda: -I(1), lambda: ~I(1), lambda: +I(4),
    lambda: "%s" % S("x"), lambda: 2 % S("x"), lambda: S("a") != "a", lambda: "a" != S("a"),
    lambda: "a" in S("abc"), lambda: [1] + L([2]), lambda: L([2]) + [1], lambda: L([1]) == [1], lambda: [1] == L([2]),
    lambda: F(2.0) ** 2, lambda: 2 ** F(2.0), lambda: 1 / F(2.0), lambda: F(1.0) / 2,
    lambda: C + 1, lambda: 1 + C, lambda: C + D, lambda: C == D, lambda: C == C, lambda: C != D, lambda: C < D, lambda: D > C,
    lambda: -C, lambda: 3 in C, lambda: 3 not in C, lambda: (C | None).__args__, lambda: (int | D).__args__, lambda: C + I(1), lambda: I(1) + C,
]
def aug():
    del log[:]
    out = []
    l = L([1]); l += [2]; out.append(l)
    x = I(1); x += 5; out.append(x)
    c = C; c += 1; out.append(c)
    d = 1; d += C; out.append(d)
    return out, log[:]

def norm(v):
    if isinstance(v, type): return v.__name__
    if v is NotImplemented: return 'NotImplemented'
    if isinstance(v, (list, tuple)): return type(v)(norm(x) for x in v)
    return v

def results():
    return [norm(run(f)) for f in cases] + [norm(aug())]

expected = [(('I+', 2), [('I.add', 2)]),
 (100, [('I.add', 99)]),
 (('+I', 2), [('I.radd', 2)]),
 (('+J', 1), [('J.radd', 1)]),
 (('+I', 2), [('I.add', 1), ('I.eq', 99), ('I.radd', 2)]),
 (0, [('I.sub', 1)]),
 (0, []),
 ('eq', [('I.eq', 3)]),
 (False, [('I.eq', 5)]),
 ('eq', [('I.eq', 3)]),
 (True, []),
 (True, []),
 (True, [('I.lt', 2)]),
 (False, []),
 ('gt', [('J.gt', 1)]),
 ('gt', [('J.gt', 0)]),
 ('neg', [('I.neg',)]),
 ('NotImplemented', []),
 (4, []),
 ('rmod', [('S.rmod', '%s')]),
 ('rmod', [('S.rmod', 2)]),
 ('ne', [('S.ne', 'a')]),
 ('ne', [('S.ne', 'a')]),
 (False, [('S.in', 'a')]),
 ([1, 2], []),
 ('L+', [('L.add', [1])]),
 (True, [('L.eq',)]),
 (True, [('L.eq',)]),
 ('pow', [('F.pow', 2)]),
 (4.0, []),
 ('rdiv', [('F.rdiv', 1)]),
 (0.5, []),
 ('M+', [('M.add', 1)]),
 ('+M', [('M.radd', 1)]),
 ('M+', [('M.add', 'D')]),
 (False, [('M.eq',), ('M.eq',)]),
 (True, [('M.eq',), ('M.eq',)]),
 (True, [('M.eq',), ('M.eq',)]),
 ('lt', [('M.lt',)]),
 ('lt', [('M.lt',)]),
 ('Mneg', [('M.neg',)]),
 (True, [('M.in', 3)]),
 (False, [('M.in', 3)]),
 (('C', 'NoneType'), []),
 (('int', 'D'), []),
 ('M+', [('M.add', 1)]),
 (('I+', 'C'), [('I.add', 'C'), ('M.eq',)]),
 (['L+', ('I+', 5), 'M+', '+M'],
  [('L.iadd', [2]), ('L.add', [2]), ('I.add', 5), ('M.add', 1), ('M.radd', 1)])]

assert_eq(results(), expected)
assert_eq([norm(run(f)) for f in cases[:6]], expected[:6])

# An int's subclass indexes by its int, never calling its __index__.
class Indexed(int):
    def __index__(self): log.append("index"); return 0
class Textual(str):
    def __index__(self): log.append("tindex"); return 1
def indexed():
    del log[:]
    return [[10, 20, 30][Indexed(2)], "abc"[Indexed(1)], range(5)[Indexed(3)], [10, 20][Textual("x")], log[:]]
assert_eq(indexed(), [30, "b", 3, 20, ["tindex"]])

# A set's and a dict's in-place operators, number methods, come before the
# right operand's subclass's reflected method; a list's in-place += and *=,
# sequence methods, after it.
class OrSet(set):
    def __ror__(self, o):
        for _ in (): pass
        return "ror"
    def __rsub__(self, o):
        for _ in (): pass
        return "rsub"
    def __radd__(self, o):
        for _ in (): pass
        return "radd"
class OrDict(dict):
    def __ror__(self, o):
        for _ in (): pass
        return "dror"
class AddList(list):
    def __radd__(self, o):
        for _ in (): pass
        return "radd"
def in_place():
    s = alias = {1}
    s |= OrSet({2})
    out = [s is alias, s]
    s = {1, 2}
    s -= OrSet({2})
    d = {1: 1}
    d |= OrDict({2: 2})
    l = [1]
    l += AddList([2])
    return out + [s, d, l, {1} | OrSet({2})]
assert_eq(in_place(), [True, {1, 2}, {1}, {1: 1, 2: 2}, "radd", "ror"])
