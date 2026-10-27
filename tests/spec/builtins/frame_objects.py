# spec: PLS-315 28.3, 9.2
# description: Frame object attributes, the frame locals proxy, clear, and repr.
from harness import *

def current():
    try:
        raise ValueError
    except ValueError as e:
        return e.__traceback__.tb_frame
def function_frame(a):
    b = a + 1
    frame = current().f_back
    return frame
frame = function_frame(1)
assert_eq(type(frame).__name__, "frame")
assert_eq(frame.f_code.co_name, "function_frame")
assert_is(frame.f_globals, globals())
assert_is(frame.f_builtins, host.module_cache()["builtins"].__dict__)
assert_eq(type(frame.f_lineno), int)
assert_eq(type(frame.f_lasti), int)
assert_is(frame.f_generator, None)
assert_true(repr(frame).startswith("<frame at "))
assert_true(repr(frame).endswith(", code function_frame>"))
assert_true(", file '" in repr(frame))

# f_locals of a function frame reads and writes the variables.
def proxy_demo():
    x = 1
    locals_proxy = current().f_back.f_locals
    assert_eq(type(locals_proxy).__name__, "FrameLocalsProxy")
    assert_eq(locals_proxy["x"], 1)
    locals_proxy["x"] = 2
    return x
assert_eq(proxy_demo(), 2)
# A module frame's f_locals is the locals mapping itself.
assert_is(current().f_back.f_locals, globals())
e = assert_raises(ValueError, setattr, frame, "f_lineno", 1)
assert_eq(str(e), "f_lineno can only be set in a trace function")
assert_raises(TypeError, setattr, frame, "f_trace_lines", 1)
frame.f_trace_lines = False

# A generator's frame: f_back is None, f_generator while it runs.
def gen():
    f = current().f_back
    yield f.f_generator
g = gen()
assert_is(next(g), g)
assert_is(g.gi_frame.f_back, None)
e = assert_raises(RuntimeError, g.gi_frame.clear)
assert_eq(str(e), "cannot clear an suspended frame")
def running():
    current().f_back.clear()
e = assert_raises(RuntimeError, running)
assert_eq(str(e), "cannot clear an executing frame")
# clear on a finished frame releases its locals.
def finished():
    big = [1]
    return current().f_back
done = finished()
done.clear()
assert_eq(dict(done.f_locals), {})
# clear on an unstarted generator's frame finalizes it.
log = []
def unstarted():
    try:
        yield
    finally:
        log.append("final")
u = unstarted()
u.gi_frame.clear()
assert_eq(log, [])
assert_raises(StopIteration, next, u)
