# spec: PLS-315 24.4.1, 24.4.2
# description: release(), __exit__() and leaving a with block of a view
# of an object with a Python __buffer__ and __release_buffer__ call
# __release_buffer__ once with the view __buffer__ returned, the view
# already released; the method may loop, its result is ignored and
# release() returns None, a second release calling nothing. Unbound
# memoryview.release() alike. Inside functions as at module level.
from harness import *

log = []

class Exporter:
    def __init__(self, name): self.name, self.data = name, bytearray(b"ab")
    def __buffer__(self, flags):
        self.view = memoryview(self.data)
        return self.view
    def __release_buffer__(self, view):
        for _ in range(2): pass
        log.append((self.name, view is self.view, repr(outer[0]).startswith("<released")))
        return "ignored"

outer = [None]

def viewed(name):
    e = Exporter(name)
    outer[0] = memoryview(e)
    return outer[0]

def releases():
    del log[:]
    m = viewed("release")
    out = [m.release(), m.release()]
    m = viewed("with")
    with m as w:
        out.append(bytes(w))
    m = viewed("exit")
    out.append(m.__exit__(None, None, None))
    m = viewed("unbound")
    out.append(memoryview.release(m))
    try:
        bytes(m)
    except ValueError as e:
        out.append(str(e))
    return out + [list(log)]

expected = [None, None, b"ab", None, None, "operation forbidden on released memoryview object",
            [("release", True, True), ("with", True, True), ("exit", True, True), ("unbound", True, True)]]

def main():
    return releases()

assert_eq(main(), expected)
assert_eq(releases(), expected)
