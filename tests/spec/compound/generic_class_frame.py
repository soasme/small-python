# spec: PLS-315 16.7, 16.3, 18.1.3, 28.9
# description: a generic class is made in a frame of its type parameters'
# scope, a function's: its bases, keywords and body run in it, so the
# body's frame's f_back is it and an exception from any of them, or from
# making the class, has a traceback entry for it at the class's line.
# Its code is named <generic parameters of C>, qualified by the enclosing
# scope, and starts where the class does, at its first decorator. A
# class without type parameters has no such frame. Inside functions, as
# at module level, and nested in a class.
from harness import *

def entries(e):
    out, tb = [], e.__traceback__
    while tb:
        out.append((tb.tb_frame.f_code.co_name, tb.tb_lineno - first))
        tb = tb.tb_next
    return out

def raised(make):
    try: make()
    except Exception as e: return entries(e)

def fails(): raise LookupError
first = fails.__code__.co_firstlineno

def in_base():
    class C[T](fails()): pass
def in_keyword():
    class C[T](metaclass=fails()): pass
def in_body():
    class C[T]:
        fails()
def in_making():
    class C[T](object): pass
def plain():
    class C(dict):
        fails()

assert_eq(raised(in_base), [("raised", -3), ("in_base", 4), ("<generic parameters of C>", 4), ("fails", 0)])
assert_eq(raised(in_keyword), [("raised", -3), ("in_keyword", 6), ("<generic parameters of C>", 6), ("fails", 0)])
assert_eq(raised(in_body), [("raised", -3), ("in_body", 8), ("<generic parameters of C>", 8), ("C", 9), ("fails", 0)])
assert_eq(raised(in_making), [("raised", -3), ("in_making", 11), ("<generic parameters of C>", 11)])
assert_eq(raised(plain), [("raised", -3), ("plain", 13), ("C", 14), ("fails", 0)])

# The body's f_back and its code, read through a traceback.
def body_back():
    try: fails()
    except LookupError as e: return e.__traceback__.tb_frame.f_back.f_back

def deco(cls): return cls

def make():
    @deco
    @deco
    class Made[T](
        dict
    ):
        back = body_back()
        code = back.f_code
        line = back.f_lineno
    return Made

Made = make()
assert_eq((Made.code.co_name, Made.code.co_qualname, Made.code.co_firstlineno - first, Made.line - first),
          ("<generic parameters of Made>", "make.<locals>.<generic parameters of Made>", 30, 32))
assert_eq(Made.back.f_back.f_code.co_name, "make")

class Outer:
    class Inner[T]:
        code = body_back().f_code
    code = body_back().f_code

assert_eq((Outer.Inner.code.co_qualname, Outer.code.co_name), ("Outer.<generic parameters of Inner>", "<module>"))

class Top[T]:
    code = body_back().f_code

assert_eq((Top.code.co_name, Top.code.co_qualname, Top.__type_params__[0].__name__),
          ("<generic parameters of Top>", "<generic parameters of Top>", "T"))
