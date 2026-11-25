# spec: PLS-315 16.4.2
# description: a class body reads __name__ for __module__ as its own load,
# before its statements: with no __name__ in its globals or builtins, the
# NameError is raised in the body's frame, which the traceback shows at
# the class statement's line, under the frame running the class statement.
from harness import assert_eq

def frames(e):
    out, tb = [], e.__traceback__
    while tb:
        out.append((tb.tb_frame.f_code.co_name, tb.tb_lineno)); tb = tb.tb_next
    return out

def run(source):
    try:
        exec(source, {"__builtins__": {"__build_class__": __build_class__}})
    except NameError as e:
        return str(e), frames(e)[1:]

assert_eq(run("class Z:\n    pass"), ("name '__name__' is not defined", [("<module>", 1), ("Z", 1)]))
assert_eq(run("x = 1\nclass Y:\n    a = 1\n    b = 2"), ("name '__name__' is not defined", [("<module>", 2), ("Y", 2)]))
assert_eq(run("def f():\n    class W: pass\nf()"), ("name '__name__' is not defined", [("<module>", 3), ("f", 2), ("W", 2)]))
