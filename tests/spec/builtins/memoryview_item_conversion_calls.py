# spec: PLS-315 24.4.2, 7.5.3
# description: storing an instance into a memoryview's item checks the
# view and indexes the key first, then converts the value by its Python
# __index__ for an integer format, __float__ (or __index__) for a real
# one and __bool__ for '?', which may loop: a result out of range is an
# invalid value, a TypeError (raised or of the result) an invalid type
# for numbers, a view released during the conversion forbids the write,
# and other exceptions propagate. Inside functions, for targets and
# generators.
from harness import *

log = []
class V:
    def __init__(self, r, view=None): self.r = r; self.view = view
    def __index__(self):
        for _ in (): pass
        log.append(("index", self.r))
        if self.view is not None: self.view.release()
        if self.r == "raise": raise LookupError("v")
        if self.r == "type": raise TypeError("t")
        return self.r
class F:
    def __init__(self, r): self.r = r
    def __float__(self):
        for _ in (): pass
        log.append(("float", self.r))
        return self.r
class B:
    def __init__(self, r): self.r = r
    def __bool__(self):
        for _ in (): pass
        log.append(("bool", self.r))
        return self.r
def t(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return (r, log[:])
def store(view, key, value):
    view[key] = value
    return view.tolist()
def cases():
    ba = bytearray(4)
    v = memoryview(ba)
    out = [t(lambda: store(v, 1, V(7))), t(lambda: store(v, -1, V(255))), t(lambda: store(v, 0, V(256))),
           t(lambda: store(v, 0, V("raise"))), t(lambda: store(v, 0, V("type"))), t(lambda: store(v, 0, V("s"))),
           t(lambda: store(v, 9, V(1))), t(lambda: store(memoryview(b"ab"), 0, V(1)))]
    w = memoryview(bytearray(8)).cast("d")
    out += [t(lambda: store(w, 0, F(2.5))), t(lambda: store(w, 0, V(3))), t(lambda: store(w, 0, F("x")))]
    q = memoryview(bytearray(2)).cast("?")
    out += [t(lambda: store(q, 1, B(True))), t(lambda: store(q, 1, B(1)))]
    i = memoryview(bytearray(8)).cast("i")
    out += [t(lambda: store(i, 1, V(-5))), t(lambda: store(i, 0, V(2**40)))]
    z = memoryview(bytearray(1)).cast("B", ())
    out += [t(lambda: store(z, ..., V(9))), t(lambda: store(z, (), V(8)))]
    r = memoryview(bytearray(2))
    out += [t(lambda: store(r, 0, V(1, r))), t(lambda: (r.release(), store(r, 0, V(1))))]
    def g():
        for v[0] in [V(3), V(4)]: yield v.tolist()
    out += [t(lambda: list(g()))]
    return out

expected = [
    ([0, 7, 0, 0], [('index', 7)]),
    ([0, 7, 0, 255], [('index', 255)]),
    (('ValueError', "memoryview: invalid value for format 'B'"), [('index', 256)]),
    (('LookupError', 'v'), [('index', 'raise')]),
    (('TypeError', "memoryview: invalid type for format 'B'"), [('index', 'type')]),
    (('TypeError', "memoryview: invalid type for format 'B'"), [('index', 's')]),
    (('IndexError', 'index out of bounds on dimension 1'), []),
    (('TypeError', 'cannot modify read-only memory'), []),
    ([2.5], [('float', 2.5)]),
    ([3.0], [('index', 3)]),
    (('TypeError', "memoryview: invalid type for format 'd'"), [('float', 'x')]),
    ([False, True], [('bool', True)]),
    (('TypeError', 'B.__bool__() must return a bool, not int'), [('bool', 1)]),
    ([0, -5], [('index', -5)]),
    (('ValueError', "memoryview: invalid value for format 'i'"), [('index', 1099511627776)]),
    (9, [('index', 9)]),
    (8, [('index', 8)]),
    (('ValueError', 'operation forbidden on released memoryview object'), [('index', 1)]),
    (('ValueError', 'operation forbidden on released memoryview object'), []),
    ([[3, 7, 0, 255], [4, 7, 0, 255]], [('index', 3), ('index', 4)]),
]
assert_eq(cases(), expected)

# A native __float__ or __index__ converts it as well.
class NativeF:
    __float__ = (2.5).__float__
class NativeI:
    __index__ = (3).__index__
class NativeBad:
    __float__ = "x".__str__
native_view = memoryview(bytearray(16)).cast('d')
native_view[0] = NativeF()
native_view[1] = NativeI()
assert_eq(native_view.tolist(), [2.5, 3.0])
with assert_raises(TypeError, message="memoryview: invalid type for format 'd'"):
    native_view[0] = NativeBad()
