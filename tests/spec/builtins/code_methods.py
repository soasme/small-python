# spec: PLS-315 28.2, 28.7
# description: replace, __replace__, co_lines and co_positions are method
# descriptors in the code type's namespace, listed by dir, bound to a code
# object as builtin methods, callable through the type, and checking
# their instance and arguments as methods do. Inside functions as at
# module level.
from harness import *

def methods():
    co = compile("x = 1", "m", "exec")
    T = type(co)
    names = ("replace", "__replace__", "co_lines", "co_positions")
    out = [[n in dir(co) for n in names], [n in T.__dict__ for n in names], [type(T.__dict__[n]).__name__ for n in names],
           [type(getattr(co, n)).__name__ for n in names], repr(T.__dict__["replace"]), co.__replace__.__qualname__,
           T.replace(co, co_name="z").co_name, T.__replace__(co, co_name="y").co_name, co.__replace__(co_name="w").co_name]
    for bad in (lambda: T.replace(1), lambda: T.co_lines(co, 1), lambda: co.replace(1), lambda: T.co_positions()):
        out.append(str(assert_raises(TypeError, bad)))
    return out

expected = [[True] * 4, [True] * 4, ["method_descriptor"] * 4, ["builtin_function_or_method"] * 4,
            "<method 'replace' of 'code' objects>", "code.__replace__", "z", "y", "w",
            "descriptor 'replace' for 'code' objects doesn't apply to a 'int' object",
            "code.co_lines() takes no arguments (1 given)", "replace() takes no positional arguments",
            "unbound method code.co_positions() needs an argument"]

def main():
    return methods()

assert_eq(main(), expected)
assert_eq(methods(), expected)
