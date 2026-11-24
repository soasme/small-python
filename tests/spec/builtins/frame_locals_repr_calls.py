# spec: PLS-315 28.3, 19.3.32, 7.5.6
# description: repr(), str() and format() of a FrameLocalsProxy, called
# directly, through a call with unpacked arguments or as a container's item,
# show its snapshot's items, each local's Python __repr__ called, which may
# loop, and raise; the proxy as its own local shows as {...}.
from harness import *

log = []
class R:
    def __init__(self, fail=False): self.fail = fail
    def __repr__(self):
        for _ in range(2): pass
        log.append("repr")
        if self.fail: raise LookupError("repr")
        return "r"
def call(f, *args, **kwargs): return f(*args, **kwargs)

def shown():
    r = R()
    d = host.frame().f_locals
    return [repr(d), str(d), format(d), f"{d}|{d!r}", call(repr, d), str([d]), call(str, (d,))], log[:]
def failing():
    r = R(True)
    d = host.frame().f_locals
    try:
        call(repr, d)
    except LookupError as e:
        return str(e)
text = "{'r': r, 'd': {...}}"
expected = ([text, text, text, text + "|" + text, text, "[" + text + "]", "(" + text + ",)"], ["repr"] * 8)
assert_eq(shown(), expected)
assert_eq(failing(), "repr")
def gen():
    del log[:]
    yield shown()
assert_eq(next(gen()), expected)
