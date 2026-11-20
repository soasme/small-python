# spec: PLS-315 20.6, 20.7
# description: the repr of a staticmethod or classmethod shows its
# object's repr, through a Python __repr__ that may loop, raise, return a
# str subclass, or return no str; a builtin type's class method shows as
# its function.
from harness import *

class Cb:
    def __init__(s, r): s.r = r
    def __call__(s): pass
    def __repr__(s):
        for _ in (): pass
        if isinstance(s.r, BaseException): raise s.r
        return s.r
class Sub(str): pass
def t(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))

def cases(w):
    return [t(lambda: repr(w(Cb("cb")))), t(lambda: repr(w(Cb(Sub("s"))))), t(lambda: repr(w(Cb(3)))),
            t(lambda: repr(w(Cb(RuntimeError("no"))))), t(lambda: repr(w(len))), [repr(w(Cb("x")))]]
assert_eq(cases(staticmethod), ["<staticmethod(cb)>", "<staticmethod(s)>", ("TypeError", "Cb.__repr__() must return a str, not int"),
                                ("RuntimeError", "no"), "<staticmethod(<built-in function len>)>", ["<staticmethod(x)>"]])
assert_eq(cases(classmethod), ["<classmethod(cb)>", "<classmethod(s)>", ("TypeError", "Cb.__repr__() must return a str, not int"),
                               ("RuntimeError", "no"), "<classmethod(<built-in function len>)>", ["<classmethod(x)>"]])
assert_eq(type(repr(staticmethod(Cb(Sub("s"))))), str)
assert_eq(repr(dict.__dict__["fromkeys"]), "<method 'fromkeys' of 'dict' objects>")
assert_eq(repr(staticmethod(Cb("top"))), "<staticmethod(top)>")
