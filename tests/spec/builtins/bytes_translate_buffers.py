# spec: PLS-315 24.3
# description: bytes.translate and bytearray.translate read the table and
# the deleted bytes by their buffers, a memoryview's or a Python
# __buffer__'s, which may loop: first the table's buffer, then its length,
# then the deleted bytes' buffer. An argument without a buffer raises
# TypeError, not the table length's ValueError.
from harness import *

log = []
class Exporting:
    def __init__(self, data): self.data = data
    def __buffer__(self, flags):
        for _ in (): pass
        log.append(self.data[:1])
        return memoryview(self.data)

table = bytes(range(256))[::-1]
assert_eq(b"zab".translate(None, memoryview(b"a")), b"zb")
assert_eq(b"zab".translate(None, Exporting(b"a")), b"zb")
assert_eq(b"zab".translate(memoryview(table)), b"\x85\x9e\x9d")
assert_eq(b"zab".translate(Exporting(table)), b"\x85\x9e\x9d")
assert_eq(b"zab".translate(None, delete=Exporting(b"b")), b"za")
assert_eq(bytearray(b"zab").translate(Exporting(table), Exporting(b"z")), bytearray(b"\x9e\x9d"))
assert_eq(log, [b"a", table[:1], b"b", table[:1], b"z"])

assert_raises(TypeError, lambda: b"zab".translate(1), message="a bytes-like object is required, not 'int'")
assert_raises(TypeError, lambda: b"zab".translate("x"), message="a bytes-like object is required, not 'str'")
assert_raises(TypeError, lambda: b"zab".translate(None, "a"), message="a bytes-like object is required, not 'str'")
assert_raises(ValueError, lambda: b"zab".translate(b"ab", 1), message="translation table must be 256 characters long")
assert_raises(TypeError, lambda: bytearray(b"zab").translate(table, 1), message="a bytes-like object is required, not 'int'")
