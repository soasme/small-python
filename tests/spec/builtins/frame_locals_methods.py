# spec: PLS-315 28.3, 9.2.1
# description: The mapping methods of a function frame's locals proxy: lookups, removal, copies, comparison, union and update.
from harness import *

def current():
    try:
        raise ValueError
    except ValueError as e:
        return e.__traceback__.tb_frame.f_back

def demo():
    x = 1
    p = current().f_locals
    Proxy = type(p)
    assert_raises(TypeError, Proxy.keys, 1, message="descriptor 'keys' for 'FrameLocalsProxy' objects doesn't apply to a 'int' object")
    assert_raises(TypeError, p.get, message="get expected 1 or 2 arguments")
    assert_raises(TypeError, p.pop, message="pop expected at least 1 argument, got 0")
    assert_raises(TypeError, p.pop, 1, 2, 3, message="pop expected at most 2 arguments, got 3")
    assert_raises(KeyError, lambda: p["nope"], message="\"local variable ''nope'' is not defined\"")
    assert_eq(p.setdefault("y", 5), 5)
    assert_eq(p.get("zz", 7), 7)
    assert_true("x" in p)
    assert_false("zz" in p)
    assert_raises(ValueError, p.pop, "x", message="cannot remove local variables from FrameLocalsProxy")
    p["extra"] = 3
    assert_eq(p.pop("extra"), 3)
    assert_eq(p.pop("extra", 9), 9)
    assert_raises(KeyError, p.pop, "extra")
    assert_eq(sorted(p.copy()), ["Proxy", "p", "x", "y"])
    assert_eq(type(p.copy()), dict)
    assert_true(repr(p).startswith("{'x': 1, 'Proxy': <class "))
    assert_true(p == p)
    assert_false(p == {"x": 1})
    assert_true(p != 3)
    assert_is(p.__eq__(3), NotImplemented)
    assert_is(p.__or__(3), NotImplemented)
    union = p | {"q": 1}
    assert_eq((type(union), union["q"], union["x"]), (dict, 1, 1))
    assert_eq(({} | p)["x"], 1)
    assert_raises(TypeError, p.update, 3, message="update() argument must be dict or another FrameLocalsProxy")
    assert_is(p.update({"q": 2}), None)
    assert_eq(p["q"], 2)
demo()
