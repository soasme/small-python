# spec: PLS-315 28.2, 8.4
# description: co_names lists global, builtin, and attribute names in the order the code first uses them; module and class code also list the names they bind.
from harness import *

def names(code):
    # Names the implementation stores itself are implementation-defined.
    return tuple(name for name in code.co_names if not name.startswith("__"))

# A value is used before the name it is stored in.
def stores():
    global g, u, w, z, e, y, f, o, p, a
    g = h
    a.b.c = d
    for u in v: w += u
    print(z := 3)
    try: pass
    except E as e: pass
    match s:
        case P(x=y) | [y]: pass
    @dec
    def f(arg=default): pass
    from m import n as o, p
    import a.b.c
assert_eq(stores.__code__.co_names,
          ("h", "g", "d", "a", "b", "c", "v", "u", "w", "print", "z", "E", "e", "s", "P", "y",
           "dec", "default", "f", "m", "n", "o", "p", "a.b.c"))

# Module code names what it binds; an inlined comprehension's variable is local.
module = compile("import a.b.c as d\nx = [i for i in y if i]\nk = x if t else q\n"
                 "class K: pass\ndef f(): pass\ndel k\n*s, r = __debug__", "<m>", "exec")
assert_eq(names(module), ("a.b.c", "b", "c", "d", "y", "x", "t", "q", "k", "K", "f", "s", "r"))
assert_eq(compile("a.b + c", "<e>", "eval").co_names, ("a", "b", "c"))
assert_eq(compile("x = 1", "<s>", "single").co_names, ("x",))

# Class code names its namespace; a free name from a function is not one.
def outer():
    v = 1
    class Inner:
        a = v
        b = glob
        def m(self): pass
        try: raise ValueError
        except ValueError as error: code = error.__traceback__.tb_frame.f_code
    return Inner.code
glob = 0
assert_eq(names(outer()), ("a", "glob", "b", "m", "ValueError", "error", "tb_frame", "f_code", "code"))

# A generator expression's first iterable belongs to the enclosing code.
it = ()
def genexp():
    return (x.attr + y for x in it if x)
assert_eq(genexp.__code__.co_names, ("it",))
assert_eq(genexp().gi_code.co_names, ("attr", "y"))
