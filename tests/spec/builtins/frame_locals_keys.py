# spec: PLS-315 28.3, 19.3.25, 26.5
# description: A frame locals proxy's keys: hashed first, equal non-str keys standing for variables, extra locals in locals(), reversed, the constructor, match, and frame attribute deletion.
from harness import *

def current():
    try:
        raise ValueError
    except ValueError as e:
        return e.__traceback__.tb_frame.f_back

class Unhashable(str):
    __hash__ = None

class Impostor:
    def __hash__(self):
        return hash("x")
    def __eq__(self, other):
        return other == "x"

def keys():
    x = 1
    p = current().f_locals
    for key in (Unhashable("x"), []):
        for thunk in (lambda: p[key], lambda: p.get(key), lambda: key in p, lambda: p.pop(key), lambda: p.setdefault(key, 1)):
            assert_raises(TypeError, thunk)
        assert_raises(TypeError, p.__setitem__, key, 1)
    p[Impostor()] = 2
    assert_eq(x, 2)
    assert_eq(p[Impostor()], 2)
    assert_eq(sorted(p), ["key", "p", "thunk", "x"])
    p["extra"] = 3
    assert_eq(locals()["extra"], 3)
    assert_eq(eval("extra"), 3)
    assert_eq(list(p)[-1], "extra")
    assert_eq(reversed(p), list(p)[::-1])
    match p:
        case {"x": value, **rest}:
            assert_eq((value, sorted(rest)), (2, ["extra", "key", "p", "thunk"]))
        case _:
            fail("a FrameLocalsProxy is a mapping")
keys()

def made():
    y = 5
    return current()
Proxy = type(made().f_locals)
assert_eq(Proxy(made()), {"y": 5})
assert_raises(TypeError, Proxy, message="FrameLocalsProxy expected 1 argument, got 0")
assert_raises(TypeError, Proxy, 1, 2, message="FrameLocalsProxy expected 1 argument, got 2")
assert_raises(TypeError, Proxy, 123, message="expect frame, not int")
assert_raises(TypeError, Proxy, frame=made(), message="FrameLocalsProxy expected 1 argument, got 0")

f = made()
for name in ("f_lineno", "f_trace_opcodes"):
    assert_raises(AttributeError, delattr, f, name, message=f"attribute '{name}' of 'frame' objects cannot be deleted")
assert_raises(TypeError, delattr, f, "f_trace_lines", message="can't delete numeric/char attribute")
assert_raises(ValueError, setattr, f, "f_lineno", "3", message="lineno must be an integer")
assert_raises(ValueError, setattr, f, "f_lineno", True, message="lineno must be an integer")
assert_raises(ValueError, setattr, f, "f_lineno", 3, message="f_lineno can only be set in a trace function")
