# spec: PLS-315 9.2, 18.1.3, 28.3
# description: Frames, the execution context stack, and the line an operation reports.
from harness import *

def caught(thunk):
    try:
        thunk()
    except Exception as e:
        return e
    fail("nothing raised")

# Each call pushes a frame whose back is the caller's.
def inner():
    raise ValueError
def middle():
    inner()
e = caught(middle)
tb = e.__traceback__
names = []
while tb is not None:
    names.append(tb.tb_frame.f_code.co_name)
    tb = tb.tb_next
assert_eq(names, ["caught", "middle", "inner"])
frame = e.__traceback__.tb_next.tb_next.tb_frame
assert_eq(frame.f_back.f_code.co_name, "middle")
assert_eq(frame.f_back.f_back.f_code.co_name, "caught")
assert_is(frame.f_globals, globals())

# A binary operation, call, or subscription reports the line of its leftmost operand.
def line_of(source):
    try:
        exec(compile(source, "<spec>", "exec"), {})
    except Exception as e:
        tb = e.__traceback__
        while tb.tb_next is not None:
            tb = tb.tb_next
        return tb.tb_lineno
assert_eq(line_of("x = (1 +\n     None)\n"), 1)
assert_eq(line_of("x = (\n  None\n  + 1)\n"), 2)
assert_eq(line_of("x = (len\n     (1))\n"), 1)
assert_eq(line_of("x = ({}\n     ['k'])\n"), 1)
assert_eq(line_of("x = (1 <\n     None)\n"), 1)
# An attribute reference reports the line of the attribute name.
assert_eq(line_of("x = (None\n     .missing)\n"), 2)
# The line is set again after the operands: an operand's own error keeps its line.
assert_eq(line_of("x = (1 +\n     undefined)\n"), 2)

# A generator's frame is popped when it suspends and pushed when resumed.
def gen():
    yield inner_frame_back()
def inner_frame_back():
    try:
        raise ValueError
    except ValueError as e:
        return e.__traceback__.tb_frame.f_back.f_code.co_name
assert_eq(next(gen()), "gen")
g = gen()
assert_is(g.gi_frame.f_back, None)
