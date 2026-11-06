# spec: PLS-315 7.3.4, 13.3.1
# description: An attribute reference that fails with AttributeError calls
# the class's __getattr__ with the name, found before the lookup ran; its
# value is the reference's. An AttributeError it raises names the
# attribute and object; other exceptions pass unchanged. A __getattribute__
# of the class's own runs first. Each holds at module level and inside a
# function.
from harness import *

class A:
    x = 1
    def __getattr__(self, k):
        for i in range(2): pass
        if k == 'bad': raise AttributeError('nope')
        if k == 'kerr': raise KeyError(k)
        return k * 2

class P:
    @property
    def p(self): raise AttributeError('inner')
    def __getattr__(self, k): return ('fallback', k)

class G:
    def __getattribute__(self, k):
        if k == 'g': return 'ga'
        raise AttributeError(k)
    def __getattr__(self, k): return 'gg'

def referenced():
    a = A()
    out = [a.x, a.zz, a.abc]
    try:
        a.bad
    except AttributeError as e:
        out.append((str(e), e.name, e.obj is a))
    try:
        a.kerr
    except KeyError as e:
        out.append(e.args)
    out.append(P().p)
    out.append((G().g, G().h))
    a.y = 5
    out.append(a.y)
    return out

assert referenced() == [1, 'zzzz', 'abcabc', ('nope', 'bad', True), ('kerr',), ('fallback', 'p'), ('ga', 'gg'), 5], referenced()

a = A()
assert (a.mod, A().x) == ('modmod', 1)
try:
    a.bad
except AttributeError as e:
    assert (str(e), e.name, e.obj is a) == ('nope', 'bad', True)
else:
    raise AssertionError('no AttributeError')

# The __getattr__ found before the lookup is the one called.
class Swapping:
    @property
    def p(self):
        Swapping.__getattr__ = lambda self, k: 'second'
        raise AttributeError('p')
    def __getattr__(self, k): return 'first'

assert (Swapping().p, Swapping().q) == ('first', 'second')
