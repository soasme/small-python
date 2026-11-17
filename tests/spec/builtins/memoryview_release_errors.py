# spec: PLS-315 24.4.1, 24.4.2
# description: an exception a Python __release_buffer__ raises is
# unraisable: bytes() and bytearray() of the exporter still return the
# copy, release(), __exit__() and leaving a with block return normally,
# and an exception leaving the with block's body propagates unchanged,
# with no context. Inside functions as at module level.
from harness import *

log = []

class Failing:
    def __init__(self): self.data = bytearray(b"ab")
    def __buffer__(self, flags): return memoryview(self.data)
    def __release_buffer__(self, view):
        for _ in range(2): pass
        log.append(bytes(view))
        raise KeyError("release")

def releases():
    del log[:]
    out = [bytes(Failing()), bytearray(Failing())]
    m = memoryview(Failing())
    out += [m.release(), m.release()]
    out.append(memoryview(Failing()).__exit__(None, None, None))
    with memoryview(Failing()) as w:
        out.append(w.tobytes())
    try:
        with memoryview(Failing()):
            raise IndexError("body")
    except IndexError as e:
        out += [e.args, e.__context__]
    return out + [len(log)]

expected = [b"ab", bytearray(b"ab"), None, None, None, b"ab", ("body",), None, 6]

def main():
    return releases()

assert_eq(main(), expected)
assert_eq(releases(), expected)
