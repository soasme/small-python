# spec: PLS-315 24.1.1, 23.1.5, 7.7.8
# description: bytes.join and bytearray.join of an iterable instance call
# its __iter__, which may loop, list its items as list() does (an iterator
# that is its own iterable is asked again, then its length hint), then
# join them; a generator is consumed alike. A TypeError getting the
# iterator becomes "can only join an iterable", for str.join too, while an
# iterator that is not iterable and an item that is not bytes-like raise
# their own errors. Bound, unbound and in a loop, the method call on a
# builtin receiver, as bytearray.extend and list.__init__ are; inside
# functions as at module level.
from harness import *

log = []
class It:
    def __init__(self, items): self.items = items
    def __iter__(self):
        for _ in (): pass
        log.append("iter"); return iter(self.items)
class Own:
    def __init__(self, items): self.items = list(items)
    def __iter__(self):
        for _ in (): pass
        log.append("iter"); return self
    def __next__(self):
        if not self.items: raise StopIteration
        return self.items.pop(0)
    def __len__(self):
        for _ in (): pass
        log.append("len"); return len(self.items)
class R:
    def __iter__(self):
        for _ in (): pass
        return 5
class Bare:
    def __next__(self): raise StopIteration
class H:
    def __iter__(self):
        for _ in (): pass
        return Bare()
def gen():
    yield b"x"
    yield memoryview(b"y")
def joins():
    del log[:]
    out = []
    for sep in (b"-", bytearray(b"+")):
        out += [sep.join(It([b"a", bytearray(b"b")])), sep.join(Own([b"c", b"d"])), sep.join(gen())]
        for bad in (R(), H(), It([b"a", 1]), Own(["s"])):
            try: sep.join(bad)
            except TypeError as e: out.append(str(e))
    for sep in ("-",):
        for bad in (R(), H()):
            try: sep.join(bad)
            except TypeError as e: out.append(str(e))
    out += [bytes.join(b"-", It([b"a", b"b"])), bytearray.join(bytearray(b"+"), gen())]
    for x in (Own([1]), Own([2])):
        b = bytearray(); b.extend(x); out.append(b)
        l = [9]; l.__init__(Own(["c"])); out.append(l)
    b = bytearray(); bytearray.extend(b, Own([3])); out.append(b)
    return out, log

expected = ([b'a-b', b'c-d', b'x-y', 'can only join an iterable', "'Bare' object is not iterable", 'sequence item 1: expected a bytes-like object, int found', 'sequence item 0: expected a bytes-like object, str found', bytearray(b'a+b'), bytearray(b'c+d'), bytearray(b'x+y'), 'can only join an iterable', "'Bare' object is not iterable", 'sequence item 1: expected a bytes-like object, int found', 'sequence item 0: expected a bytes-like object, str found', 'can only join an iterable', "'Bare' object is not iterable", b'a-b', bytearray(b'x+y'), bytearray(b'\x01'), ['c'], bytearray(b'\x02'), ['c'], bytearray(b'\x03')], ['iter', 'iter', 'iter', 'len', 'iter', 'iter', 'iter', 'len', 'iter', 'iter', 'iter', 'len', 'iter', 'iter', 'iter', 'len', 'iter', 'iter', 'len', 'iter', 'len', 'iter', 'len', 'iter', 'len', 'iter', 'len'])
assert_eq(joins(), expected)

def nested():
    return joins()

assert_eq(nested(), expected)
