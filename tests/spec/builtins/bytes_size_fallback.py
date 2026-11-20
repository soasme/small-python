# spec: PLS-315 24.1.1, 24.2
# description: bytes() and bytearray() of a source whose __index__ raises
# TypeError go on to its buffer, a Python __buffer__ (and
# __release_buffer__) called once, or to iterating it, a Python __iter__,
# generator or iterator class, each called once; __index__ is not called
# again. Other errors propagate. So do a bytes subclass's call and calls
# inside functions and generators.
from harness import *

log = []
def taken(f):
    try:
        r = f()
    except Exception as e:
        r = (type(e).__name__, str(e))
    got = list(log); log.clear()
    return r, got

class Sized:
    def __index__(self): log.append("index"); raise TypeError
class Exported(Sized):
    def __buffer__(self, flags): log.append("buffer"); return memoryview(b"xy")
class Released(Exported):
    def __release_buffer__(self, view): log.append("release")
class Wrong(Sized):
    def __buffer__(self, flags): log.append("buffer"); return 5
class Iterated(Sized):
    def __iter__(self): log.append("iter"); return iter([7, 8])
class Generated(Sized):
    def __iter__(self):
        log.append("iter")
        yield 1
        yield 2
class Large(Sized):
    def __iter__(self): log.append("iter"); return iter([300])
class Failing(Sized):
    def __iter__(self):
        log.append("iter")
        yield 1
        raise KeyError("k")
class Stepped(Sized):
    def __iter__(self): log.append("iter"); return self
    def __next__(self):
        log.append("next")
        if log.count("next") > 2: raise StopIteration
        return 5
class B(bytes): pass

assert_eq(taken(lambda: (bytes(Exported()), bytearray(Exported()))), ((b"xy", bytearray(b"xy")), ["index", "buffer", "index", "buffer"]))
assert_eq(taken(lambda: bytes(Released())), (b"xy", ["index", "buffer", "release"]))
assert_eq(taken(lambda: bytearray(Wrong())), (("TypeError", f"{fqname(Wrong)}.__buffer__() must return a memoryview, not int"), ["index", "buffer"]))
assert_eq(taken(lambda: (bytes(Iterated()), bytearray(Generated()))), ((b"\x07\x08", bytearray(b"\x01\x02")), ["index", "iter", "index", "iter"]))
assert_eq(taken(lambda: bytes(Large())), (("ValueError", "bytes must be in range(0, 256)"), ["index", "iter"]))
assert_eq(taken(lambda: bytearray(Failing())), (("KeyError", "'k'"), ["index", "iter"]))
assert_eq(taken(lambda: bytes(Stepped())), (b"\x05\x05", ["index", "iter", "next", "next", "next"]))
assert_eq(taken(lambda: (B(Generated()), type(B(Exported())).__name__)), ((b"\x01\x02", "B"), ["index", "iter", "index", "buffer"]))
assert_eq(taken(lambda: bytes(Sized())), (("TypeError", "cannot convert 'Sized' object to bytes"), ["index"]))

def inside():
    return bytes(Iterated()) + bytes(Generated()), [bytearray(Exported()) for _ in range(2)]
assert_eq(taken(inside), ((b"\x07\x08\x01\x02", [bytearray(b"xy")] * 2), ["index", "iter", "index", "iter", "index", "buffer", "index", "buffer"]))
def made():
    yield bytes(Generated())
    yield bytearray(Iterated())
assert_eq(taken(lambda: list(made())), ([b"\x01\x02", bytearray(b"\x07\x08")], ["index", "iter", "index", "iter"]))
