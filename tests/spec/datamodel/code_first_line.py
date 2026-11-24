# spec: PLS-315 28.2, 16.4.2
# description: a decorated function's code starts at its first
# decorator's line, as a decorated class's __firstlineno__ does; an
# unstarted generator's or coroutine's frame is at that line, and a throw
# into it raises there. An annotate function starts at its own def.
from harness import *
def deco(f): return f
base = deco.__code__.co_firstlineno
@deco
@deco
def f(x: int): pass
@deco
def g():
    yield 1
@deco
async def co(): pass
@deco
class C:
    @deco
    def m(self): pass
def plain(): pass
c = co()
assert_eq([f.__code__.co_firstlineno - base, f.__annotate__.__code__.co_firstlineno - base, g.__code__.co_firstlineno - base,
           g().gi_frame.f_lineno - base, c.cr_frame.f_lineno - base, C.__firstlineno__ - base, C.m.__code__.co_firstlineno - base,
           plain.__code__.co_firstlineno - base], [2, 4, 5, 5, 8, 10, 12, 14])
c.close()
try:
    g().throw(KeyError)
except KeyError as e:
    assert_eq(e.__traceback__.tb_next.tb_lineno - base, 5)
