# spec: PLS-315 24.2, 24.3, 23.1.4
# description: A bytearray's pop() and insert() index, the byte of its
# insert(), append() and remove() and its searches' start and end, given an object with a Python __index__, convert by it
# before the array is read, in order: the conversion may resize the
# array, which the method then sees; its exception propagates, a non-int
# result raises TypeError, and None is an absent bound. Inside functions
# as at module level, bound and unbound.
from harness import *

log = []
class X:
    def __init__(self, v, grow=None): self.v = v; self.grow = grow
    def __index__(self):
        for _ in range(2): pass
        log.append(self.v)
        if self.grow is not None: self.grow[:] = b"zzzzzzzz"
        if self.v == "raise": raise LookupError("x")
        return self.v
def t(f):
    try: r = f()
    except Exception as e: r = type(e).__name__ + ": " + str(e)
    if isinstance(r, bytearray): r = ("ba", bytes(r))
    out = (r, log[:]); del log[:]; return out
def results():
    ba = bytearray(b"abcab")
    def fresh(): ba[:] = b"abcab"; return ba
    return [t(lambda: fresh().pop(X(1))), t(lambda: bytes(ba)), t(lambda: fresh().insert(X(1), 120)), t(lambda: bytes(ba)),
            t(lambda: fresh().find(b"b", X(2))), t(lambda: fresh().rfind(b"b", X(0), X(4))), t(lambda: fresh().count(b"ab", X(1))),
            t(lambda: fresh().index(b"b", X(2))), t(lambda: fresh().rindex(b"a", None, X(3))), t(lambda: fresh().startswith(b"b", X(1))),
            t(lambda: fresh().endswith(b"a", X(0), X(4))), t(lambda: fresh().find(98, X(2))), t(lambda: fresh().find("b", X(2))),
            t(lambda: fresh().find(b"z", X(0, ba))), t(lambda: bytes(ba)), t(lambda: fresh().pop(X(0, ba))), t(lambda: bytes(ba)),
            t(lambda: fresh().insert(X(0, ba), 121)), t(lambda: bytes(ba)), t(lambda: fresh().insert(X(0), 300)),
            t(lambda: fresh().insert(X(0), X(65))), t(lambda: bytearray().pop(X(0))), t(lambda: fresh().pop(X(9))),
            t(lambda: fresh().pop(X("raise"))), t(lambda: fresh().find(b"a", X("s"))), t(lambda: bytearray.pop(fresh(), X(1))),
            t(lambda: fresh().index(b"q", X(0))), t(lambda: fresh().find(b"a", 1.5, X(2))),
            t(lambda: fresh().append(X(65))), t(lambda: bytes(ba)), t(lambda: fresh().remove(X(99))), t(lambda: bytes(ba)),
            t(lambda: fresh().append(X(300))), t(lambda: fresh().append(X(1 << 80))), t(lambda: fresh().remove(X("s"))),
            t(lambda: fresh().insert(X(1), X("raise"))), t(lambda: fresh().insert(1.5, X(1))), t(lambda: fresh().remove(X(-1))),
            t(lambda: fresh().append(X(0, ba))), t(lambda: bytes(ba)),
            t(lambda: flat(fresh(), "count")), t(lambda: bytes(ba)), t(lambda: flat(fresh(), "find")), t(lambda: fresh().find(b"b", 1, 2, 3))]

class Flat:
    # No loop: __index__ may run without leaving the C call.
    def __init__(self, ba): self.ba = ba
    def __index__(self):
        self.ba[:] = b"xbxb"
        return 2

def flat(ba, name):
    return getattr(ba, name)(b"b", Flat(ba))

expected = [(98, [1]), (b'acab', []), (None, [1]), (b'axbcab', []), (4, [2]), (1, [0, 4]), (1, [1]), (4, [2]), (0, [3]),
            (True, [1]), (True, [0, 4]), (4, [2]),
            ("TypeError: argument should be integer or bytes-like object, not 'str'", [2]), (0, [0]), (b'zzzzzzzz', []),
            (122, [0]), (b'zzzzzzz', []), (None, [0]), (b'yzzzzzzzz', []),
            ('ValueError: byte must be in range(0, 256)', [0]), (None, [0, 65]),
            ('IndexError: pop from empty bytearray', [0]), ('IndexError: pop index out of range', [9]),
            ('LookupError: x', ['raise']), ('TypeError: X.__index__() must return an int, not str', ['s']), (98, [1]),
            ('ValueError: subsection not found', [0]),
            ('TypeError: slice indices must be integers or have an __index__ method', []), (None, [65]),
            (b'abcabA', []), (None, [99]), (b'abab', []), ('ValueError: byte must be in range(0, 256)', [300]),
            ('ValueError: byte must be in range(0, 256)', [1208925819614629174706176]),
            ('TypeError: X.__index__() must return an int, not str', ['s']), ('LookupError: x', [1, 'raise']),
            ("TypeError: 'float' object cannot be interpreted as an integer", []),
            ('ValueError: byte must be in range(0, 256)', [-1]), (None, [0]), (b'zzzzzzzz\x00', []), (1, []),
            (b'xbxb', []), (3, []), ('TypeError: find expected at most 3 arguments, got 4', [])]


def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
