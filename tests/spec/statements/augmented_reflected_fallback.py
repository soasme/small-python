# spec: PLS-315 14.3, 26.1
# description: When y's reflected __radd__ or __rmul__ declines with
# NotImplemented, list += y extends the list by y's items, asking its
# Python __iter__ (a generator or an iterator class) and length hint, and
# list *= y and bytearray *= y repeat by y's Python __index__; the
# target keeps the list's or bytearray's identity, in a name, attribute
# or subscript target, inside a generator as at module level. Errors
# from __iter__, an item, __index__, or an __index__ returning a non-int
# propagate, the list left as extended so far.
from harness import assert_eq

log = []
class R:
    def __init__(self, kind): self.kind = kind
    def __radd__(self, other):
        log.append(("radd", type(other).__name__))
        return NotImplemented
    __rmul__ = __radd__
    def __iter__(self):
        for _ in range(1): pass
        log.append("iter")
        if self.kind == "iter-fails": raise KeyError("iter")
        if self.kind == "class": return Items()
        return self.items()
    def items(self):
        yield 7
        if self.kind == "item-fails": raise LookupError("item")
        yield 8
    def __length_hint__(self):
        log.append("hint")
        return 2
    def __index__(self):
        for _ in range(1): pass
        log.append("index")
        if self.kind == "index-fails": raise KeyError("index")
        if self.kind == "index-str": return "2"
        return 3
class Items:
    def __init__(self): self.n = 0
    def __iter__(self): return self
    def __next__(self):
        for _ in range(1): pass
        self.n += 1
        if self.n > 2: raise StopIteration
        log.append(("next", self.n))
        return self.n
class Box: pass
def run(target, op, kind, make=list):
    del log[:]
    a = make([1]) if make is list else make(b"x")
    b, box, seq = a, Box(), [None]
    box.v = a; seq[0] = a
    try:
        if target == "name":
            if op == "+": a += R(kind)
            else: a *= R(kind)
            got = a
        elif target == "attr":
            if op == "+": box.v += R(kind)
            else: box.v *= R(kind)
            got = box.v
        else:
            if op == "+": seq[0] += R(kind)
            else: seq[0] *= R(kind)
            got = seq[0]
        r = (got, got is b)
    except Exception as e:
        r = (type(e).__name__, str(e)[:40], b)
    return r, log[:]
def generated(*args):
    yield run(*args)
assert_eq(run('name', '+', 'gen'), (([1, 7, 8], True), [('radd', 'list'), 'iter', 'hint']))
assert_eq(run('name', '+', 'class'), (([1, 1, 2], True), [('radd', 'list'), 'iter', 'hint', ('next', 1), ('next', 2)]))
assert_eq(run('name', '+', 'iter-fails'), (('KeyError', "'iter'", [1]), [('radd', 'list'), 'iter']))
assert_eq(run('name', '+', 'item-fails'), (('LookupError', 'item', [1, 7]), [('radd', 'list'), 'iter', 'hint']))
assert_eq(run('name', '*', 'gen'), (([1, 1, 1], True), [('radd', 'list'), 'index']))
assert_eq(run('name', '*', 'gen', bytearray), ((bytearray(b'xxx'), True), [('radd', 'bytearray'), 'index']))
assert_eq(run('name', '*', 'index-fails'), (('KeyError', "'index'", [1]), [('radd', 'list'), 'index']))
assert_eq(run('name', '*', 'index-fails', bytearray), (('KeyError', "'index'", bytearray(b'x')), [('radd', 'bytearray'), 'index']))
assert_eq(run('name', '*', 'index-str'), (('TypeError', 'R.__index__() must return an int, not st', [1]), [('radd', 'list'), 'index']))
assert_eq(run('name', '*', 'index-str', bytearray), (('TypeError', 'R.__index__() must return an int, not st', bytearray(b'x')), [('radd', 'bytearray'), 'index']))
assert_eq(run('attr', '+', 'gen'), (([1, 7, 8], True), [('radd', 'list'), 'iter', 'hint']))
assert_eq(run('attr', '+', 'class'), (([1, 1, 2], True), [('radd', 'list'), 'iter', 'hint', ('next', 1), ('next', 2)]))
assert_eq(run('attr', '+', 'iter-fails'), (('KeyError', "'iter'", [1]), [('radd', 'list'), 'iter']))
assert_eq(run('attr', '+', 'item-fails'), (('LookupError', 'item', [1, 7]), [('radd', 'list'), 'iter', 'hint']))
assert_eq(run('attr', '*', 'gen'), (([1, 1, 1], True), [('radd', 'list'), 'index']))
assert_eq(run('attr', '*', 'gen', bytearray), ((bytearray(b'xxx'), True), [('radd', 'bytearray'), 'index']))
assert_eq(run('attr', '*', 'index-fails'), (('KeyError', "'index'", [1]), [('radd', 'list'), 'index']))
assert_eq(run('attr', '*', 'index-fails', bytearray), (('KeyError', "'index'", bytearray(b'x')), [('radd', 'bytearray'), 'index']))
assert_eq(run('attr', '*', 'index-str'), (('TypeError', 'R.__index__() must return an int, not st', [1]), [('radd', 'list'), 'index']))
assert_eq(run('attr', '*', 'index-str', bytearray), (('TypeError', 'R.__index__() must return an int, not st', bytearray(b'x')), [('radd', 'bytearray'), 'index']))
assert_eq(run('item', '+', 'gen'), (([1, 7, 8], True), [('radd', 'list'), 'iter', 'hint']))
assert_eq(run('item', '+', 'class'), (([1, 1, 2], True), [('radd', 'list'), 'iter', 'hint', ('next', 1), ('next', 2)]))
assert_eq(run('item', '+', 'iter-fails'), (('KeyError', "'iter'", [1]), [('radd', 'list'), 'iter']))
assert_eq(run('item', '+', 'item-fails'), (('LookupError', 'item', [1, 7]), [('radd', 'list'), 'iter', 'hint']))
assert_eq(run('item', '*', 'gen'), (([1, 1, 1], True), [('radd', 'list'), 'index']))
assert_eq(run('item', '*', 'gen', bytearray), ((bytearray(b'xxx'), True), [('radd', 'bytearray'), 'index']))
assert_eq(run('item', '*', 'index-fails'), (('KeyError', "'index'", [1]), [('radd', 'list'), 'index']))
assert_eq(run('item', '*', 'index-fails', bytearray), (('KeyError', "'index'", bytearray(b'x')), [('radd', 'bytearray'), 'index']))
assert_eq(run('item', '*', 'index-str'), (('TypeError', 'R.__index__() must return an int, not st', [1]), [('radd', 'list'), 'index']))
assert_eq(run('item', '*', 'index-str', bytearray), (('TypeError', 'R.__index__() must return an int, not st', bytearray(b'x')), [('radd', 'bytearray'), 'index']))
assert_eq(next(generated('name', '+', 'gen')), (([1, 7, 8], True), [('radd', 'list'), 'iter', 'hint']))
assert_eq(next(generated('item', '*', 'gen', bytearray)), ((bytearray(b'xxx'), True), [('radd', 'bytearray'), 'index']))
