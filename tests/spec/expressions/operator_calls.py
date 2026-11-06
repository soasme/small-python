# spec: PLS-315 7.6.2, 13.3.2, 13.7, 13.10
# description: A binary operator calls the left operand's method, then the
# right one's reflected method when that declines, unless the right
# operand's class is a subclass overriding it, which goes first; a
# subscription calls __getitem__; a comparison calls the rich comparison
# method the same way, == falling back to identity, and a chain or a test
# takes its result's truth. What any of them raises reaches the caller.
from harness import *

log = []
class V:
    def __init__(self, v): self.v = v
    def __add__(self, other):
        for i in range(1): pass
        log.append(('add', self.v))
        return V(self.v + (other.v if isinstance(other, V) else other))
    def __sub__(self, other): return NotImplemented
    def __mul__(self, other): return NotImplemented
    def __getitem__(self, key):
        for i in range(1): pass
        return ('item', self.v, key)

class W(V):
    def __radd__(self, other):
        log.append('W radd')
        return 'W first'

class N:
    def __rsub__(self, other): return ('N rsub', other.v)

class D:
    def __or__(self, other): return NotImplemented

class Raising:
    def __add__(self, other): raise KeyError('add')
    def __getitem__(self, key): raise IndexError(key)

def operations():
    a, b = V(1), V(2)
    xs = [a, b]
    out = [(a + b).v, (a + 5).v, a[3], xs[0][1], (xs[0] + xs[1]).v, a - N(), V(1) + W(2)]
    for left, right in ((a, 2), (a, b), (D(), {}.keys())):
        try:
            left * right if not isinstance(left, D) else left | right
        except TypeError as e:
            out.append(str(e))
    try:
        a[1, 2] + 1
    except TypeError as e:
        out.append(str(e))
    r = Raising()
    for attempt in (lambda: r + 1, lambda: r[7], lambda: Raising()[8]):
        try:
            attempt()
        except (KeyError, IndexError) as e:
            out.append(e.args)
    return out

assert operations() == [3, 6, ('item', 1, 3), ('item', 1, 1), 3, ('N rsub', 1), 'W first',
                        "unsupported operand type(s) for *: 'V' and 'int'",
                        "unsupported operand type(s) for *: 'V' and 'V'", "'D' object is not iterable",
                        'can only concatenate tuple (not "int") to tuple', ('add',), (7,), (8,)], operations()
assert log == [('add', 1), ('add', 1), ('add', 1), 'W radd'], log

order = []
class K:
    def __init__(self, v): self.v = v
    def __eq__(self, other):
        for i in range(1): pass
        order.append(('eq', self.v))
        return isinstance(other, K) and self.v == other.v
    def __lt__(self, other):
        order.append(('lt', self.v))
        return self.v < other.v
    def __gt__(self, other): return NotImplemented
    __hash__ = None

class SubK(K):
    def __eq__(self, other):
        order.append('sub eq')
        return 'sub'

class Truth:
    def __init__(self, t): self.t = t
    def __bool__(self):
        order.append(('bool', self.t))
        return self.t

class Fuzzy:
    def __lt__(self, other): return Truth(True)
    def __le__(self, other): return Truth(False)

class Declining:
    def __eq__(self, other): return NotImplemented

def comparisons():
    a, b, c = K(1), K(2), K(3)
    out = [a == K(1), a != b, a < b, b < a, a == 1, K(1) == SubK(1), a < b < c, a < c < b, b > a]
    if a < b: out.append('yes')
    if not b < a: out.append('no')
    d = Declining()
    out += [Declining() == Declining(), d == d, d != d]
    fuzzy = Fuzzy()
    if fuzzy < 1: out.append('truthy')
    if fuzzy <= 1: out.append('never')
    out.append(type(fuzzy < 1).__name__)
    try:
        a < 1
    except AttributeError as e:
        out.append('lt raised')
    return out

assert comparisons() == [True, True, True, False, False, 'sub', True, False, True, 'yes', 'no', False, True, False,
                         'truthy', 'Truth', 'lt raised'], comparisons()
assert order[:12] == [('eq', 1), ('eq', 1), ('lt', 1), ('lt', 2), ('eq', 1), 'sub eq', ('lt', 1), ('lt', 2),
                      ('lt', 1), ('lt', 3), ('lt', 1), ('lt', 1)], order
