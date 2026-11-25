# spec: PLS-315 19.3.10, 19.3.14, 19.3.15, 24.4.1
# description: compile, eval and exec take any bytes-like source: a
# memoryview, a slice of one, or an instance whose Python __buffer__, which
# may loop, returns one, released after; the source is decoded as a file's
# bytes. A source with no buffer, or whose buffer fails, raises the
# builtin's TypeError in place of the buffer's exception.
from harness import *

log = []
class Exporting:
    def __init__(self, data): self.data = data
    def __buffer__(self, flags):
        for _ in (): pass
        return memoryview(self.data)
    def __release_buffer__(self, view): log.append("released")
class Failing:
    def __buffer__(self, flags):
        for _ in (): pass
        raise ValueError("no buffer")
class NotView:
    def __buffer__(self, flags): return 1

ns = {}
exec(memoryview(b"x = 1"), ns)
exec(Exporting(b"y = x + 1"), ns)
assert_eq((ns["x"], ns["y"], log), (1, 2, ["released"]))
assert_eq(eval(memoryview(b"  3 * 2")), 6)
assert_eq(eval(memoryview(b"abc + 7")[4:]), 7)
assert_eq(eval(compile(Exporting(b"40 + 2"), "f", "eval")), 42)
assert_eq(eval(memoryview(b"# -*- coding: latin-1 -*-\n'\xe9'")), "\xe9")
assert_raises(SyntaxError, lambda: eval(memoryview(b"1\0")), message="source code string cannot contain null bytes")

released = memoryview(b"1"); released.release()
assert_raises(TypeError, lambda: exec(Failing()), message="exec() arg 1 must be a string, bytes or code object")
assert_raises(TypeError, lambda: eval(NotView()), message="eval() arg 1 must be a string, bytes or code object")
assert_raises(TypeError, lambda: compile(Failing(), "f", "exec"), message="compile() arg 1 must be a string, bytes or AST object")
assert_raises(TypeError, lambda: exec(released), message="exec() arg 1 must be a string, bytes or code object")
try: exec(Failing())
except TypeError as e: assert_eq((e.__context__, e.__cause__), (None, None))
