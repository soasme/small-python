# spec: PLS-315 24.3
# description: a bytes %b or %s takes a bytearray's contents, and a
# bytearray subclass instance's without calling its __bytes__ or its
# __buffer__, for a bytes or a bytearray format. Inside functions as at
# module level.
from harness import *

log = []

class Own(bytearray):
    def __bytes__(self):
        for _ in (): pass
        log.append("bytes")
        return b"no"
    def __buffer__(self, flags):
        log.append("buffer")
        return memoryview(b"no")

class Plain(bytearray): pass

def formatted():
    del log[:]
    return [b"%b|%s" % (Own(b"yes"), Plain(b"p")), bytearray(b"%b") % (Own(b"ba"),),
            b"%(k)b" % {b"k": Own(b"key")}, b"%b" % (bytearray(b"exact"),), log[:]]

expected = [b"yes|p", bytearray(b"ba"), b"key", b"exact", []]

def main():
    return formatted()

assert_eq(main(), expected)
assert_eq(formatted(), expected)
# A Python __buffer__ without __release_buffer__ gives %b its copy in a
# function, and one returning bytes is a TypeError.
class OnlyBuffer:
    def __buffer__(self, flags):
        for _ in (): pass
        return memoryview(b"ab")
class BytesBuffer:
    def __buffer__(self, flags):
        for _ in (): pass
        return b"no"
def only_buffers():
    out = [b"%b" % (OnlyBuffer(),), b"<%b|%b>" % (OnlyBuffer(), OnlyBuffer()), bytearray(b"%b") % (OnlyBuffer(),), b"%s" % OnlyBuffer()]
    try: b"%b" % (BytesBuffer(),)
    except TypeError as e: out.append(str(e))
    return out
assert_eq(only_buffers(), [b"ab", b"<ab|ab>", bytearray(b"ab"), b"ab", "BytesBuffer.__buffer__() must return a memoryview, not bytes"])
