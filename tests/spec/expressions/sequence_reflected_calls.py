# spec: PLS-315 7.6.2
# description: A built-in sequence, or an instance of a subclass of one
# whose classes define neither the operator's method nor its reflected
# one, has no method of + or * (or any operator but % of a str or bytes):
# the other operand's Python reflected method is called first and may
# loop; its result is the operation's, its exception propagates, and when
# it returns NotImplemented the sequence protocol answers, repeating by
# __index__ or raising its TypeError. Inside functions as at module level.
from harness import *

log = []

class R:
    def __init__(self, n=2, declines=False): self.n, self.declines = n, declines
    def __index__(self): return self.n
    def _reflect(self, name, other):
        for _ in range(2): pass
        log.append((name, type(other).__name__))
        if self.n < 0: raise LookupError(name)
        return NotImplemented if self.declines else name
    def __radd__(self, other): return self._reflect("radd", other)
    def __rmul__(self, other): return self._reflect("rmul", other)
    def __rsub__(self, other): return self._reflect("rsub", other)
    def __rmod__(self, other): return self._reflect("rmod", other)

class S(str): pass
class Q(list): pass
class T(str): __radd__ = lambda s, o: "T"

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    out = [[1] * R(), "ab" * R(), (1,) + R(), b"x" * R(), bytearray(b"y") + R(), (1,) - R(), [1] % R(),
           S("a") + R(), Q([2]) * R(), S("a") + T("b")]
    out += [[1] * R(3, True), error(lambda: "s" + R(2, True)), error(lambda: [0] * R(-1))]
    return out + [list(log)]

expected = ['rmul', 'rmul', 'radd', 'rmul', 'radd', 'rsub', 'rmod', 'radd', 'rmul', 'T', [1, 1, 1],
            ('TypeError', 'can only concatenate str (not "R") to str'), ('LookupError', 'rmul'),
            [('rmul', 'list'), ('rmul', 'str'), ('radd', 'tuple'), ('rmul', 'bytes'), ('radd', 'bytearray'),
             ('rsub', 'tuple'), ('rmod', 'list'), ('radd', 'S'), ('rmul', 'Q'), ('rmul', 'list'), ('radd', 'str'),
             ('rmul', 'list')]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
