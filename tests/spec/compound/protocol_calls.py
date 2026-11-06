# spec: PLS-315 16.1.2, 16.4, 20.5.1, 15.5, 15.3, 14.2
# description: Decorators apply from the last to the first, each called with
# what the one below gave; a property's getter is called with the instance
# and takes precedence over its __dict__; with calls __enter__, binds its
# value, and calls __exit__ on every way out of the body.
from harness import *

log = []
def note(f):
    for i in range(1): pass
    log.append(f.__name__)
    return f
def tag(t):
    def apply(f):
        for i in range(1): pass
        log.append(t)
        f.tag = t
        return f
    return apply

@note
@tag('inner')
def decorated(): return 1

assert log == ['inner', 'decorated'] and decorated.tag == 'inner'

def nested():
    @tag('local')
    def g(): return 2
    @note
    class C: pass
    return g.tag, g(), C.__name__

assert nested() == ('local', 2, 'C')

def replacing():
    def wrap(f):
        for i in range(1): pass
        return lambda: ('wrapped', f())
    @wrap
    def h(): return 3
    return h()

assert replacing() == ('wrapped', 3)

class Shape:
    def __init__(self): self._side = 3
    @property
    def area(self):
        for i in range(1): pass
        return self._side * self._side
    @property
    def broken(self):
        raise KeyError('broken')

class Fallback(Shape):
    def __getattr__(self, name): return 'fallback ' + name
    @property
    def missing(self):
        raise AttributeError('missing')

def properties():
    s = Shape()
    out = [s.area]
    s.__dict__['area'] = 'shadow'
    out.append(s.area)
    try:
        s.broken
    except KeyError as e:
        out.append(e.args)
    out.append(Fallback().missing)
    Shape.area = 'plain'
    out.append(s.area)
    return out

assert properties() == [9, 9, ('broken',), 'fallback missing', 'shadow']

events = []
class Manager:
    def __init__(self, name): self.name = name
    def __enter__(self):
        for i in range(1): pass
        events.append(('enter', self.name))
        return self.name
    def __exit__(self, kind, value, traceback):
        events.append(('exit', self.name, kind and kind.__name__))
        return self.name == 'swallow'

class Failing:
    def __enter__(self): raise KeyError('enter')
    def __exit__(self, *args): events.append('never')

def managed():
    with Manager(1) as a, Manager(2) as b:
        events.append((a, b))
    with Manager('swallow'):
        raise ValueError
    try:
        with Manager(3):
            raise KeyError
    except KeyError:
        events.append('caught')
    try:
        with Failing():
            events.append('body')
    except KeyError as e:
        events.append(e.args)
    for i in range(2):
        with Manager(i):
            if i: break
            continue
    def leaving():
        with Manager('return') as v:
            return v
    events.append(leaving())
    return events

assert managed() == [('enter', 1), ('enter', 2), (1, 2), ('exit', 2, None), ('exit', 1, None),
                     ('enter', 'swallow'), ('exit', 'swallow', 'ValueError'), ('enter', 3), ('exit', 3, 'KeyError'),
                     'caught', ('enter',), ('enter', 0), ('exit', 0, None), ('enter', 1), ('exit', 1, None),
                     ('enter', 'return'), ('exit', 'return', None), 'return'], events

# A for loop calls its iterable's __iter__, which must give an iterator; a
# store to a subscript calls __setitem__ with the key and the value.
calls = []
class Counted:
    def __init__(self, n): self.n = n
    def __iter__(self):
        for i in range(1): pass
        calls.append('iter')
        return iter(range(self.n))

class Yielding:
    def __iter__(self):
        yield 'a'
        yield 'b'

class NotIterator:
    def __iter__(self): return 5

class Table:
    def __init__(self): self.d = {}
    def __setitem__(self, key, value):
        for i in range(1): pass
        calls.append((key, value))
        self.d[key] = value

def loops_and_stores():
    out = [x for x in Counted(2)]
    for x in Yielding():
        out.append(x)
    try:
        for x in NotIterator():
            pass
    except TypeError as e:
        out.append(str(e))
    t = Table()
    k = 'k'
    t[k] = 1
    t['j'] = t.d['k'] + 1
    u = v = Table()
    u[1] = v[2] = 'both'
    out.append(sorted(t.d.items()))
    out.append(sorted(u.d.items()))
    return out

assert loops_and_stores() == [0, 1, 'a', 'b', 'NotIterator.__iter__() must return an iterator, not int',
                              [('j', 2), ('k', 1)], [(1, 'both'), (2, 'both')]], loops_and_stores()
assert calls[:5] == ['iter', ('k', 1), ('j', 2), (1, 'both'), (2, 'both')], calls

table = Table()
table['module'] = 'level'
assert table.d == {'module': 'level'}
