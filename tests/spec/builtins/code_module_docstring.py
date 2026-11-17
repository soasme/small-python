# spec: PLS-315 28.2
# description: the code of a module compiled in exec mode starts
# co_consts with its docstring, as a function's code does, without the
# docstring flag a function's code has; a module without one does not
# start with a docstring, and an optimization level of 2 drops it.
# Inside functions as at module level.
from harness import *

def firsts():
    out = []
    for source, optimize in (('"doc"\nv = 1\n', 0), ('"""two\n   lines"""\n', 0), ("v = 1\n", 0), ('"doc"\n', 2), ('v = 1\n"doc"\n', 0)):
        co = compile(source, "m", "exec", optimize=optimize)
        out.append((type(co.co_consts).__name__, co.co_consts[:1] in (("doc",), ("two\nlines",)), co.co_flags & 0x4000000))
    def f():
        "fdoc"
    return out + [f.__code__.co_consts[0], compile('"doc"\n', "m", "exec").co_consts[0], compile('"""a\n  b"""', "m", "exec").co_consts[0]]

expected = [("tuple", True, 0), ("tuple", True, 0), ("tuple", False, 0), ("tuple", False, 0), ("tuple", False, 0),
            "fdoc", "doc", "a\nb"]

def main():
    return firsts()

assert_eq(main(), expected)
assert_eq(firsts(), expected)
