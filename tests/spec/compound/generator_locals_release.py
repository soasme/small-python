# spec: PLS-315 27.2.4, 27.2.3
# description: A finished generator releases its local variables when it
# ends, by a return, an exception, a throw or a refused throw, though the
# generator lives on; a frame object of it that is still referenced, a
# traceback's or a gi_frame read before the end, keeps them until it is
# released. Such a frame keeps the code and the line the generator ended
# at, its f_generator is None, and it does not keep the generator
# reachable.
from harness import *

log = []
class Noted:
    def __init__(self, name): self.name = name
    def __del__(self): log.append(self.name)

def gen(name, end):
    local = Noted(name)
    yield 1
    if end == "raise": raise ValueError(name)
    return name

def leaf():
    yield 1

def delegating(name):
    local = Noted(name)
    yield from leaf()

def nested(name):
    local = Noted(name)
    yield from delegating(name + " inner")

# Each ending releases the locals at once, the generator kept.
g = gen("return", "return"); next(g)
try: next(g)
except StopIteration as e: assert_eq(e.value, "return")
assert_eq(log, ["return"])
del log[:]
g = gen("raise", "raise"); next(g)
try: next(g)
except ValueError: pass
assert_eq(log, ["raise"])
del log[:]
g = gen("throw", "return"); next(g)
try: g.throw(KeyError)
except KeyError: pass
assert_eq(log, ["throw"])
del log[:]
g = delegating("refused"); next(g)
try: g.throw(1)
except TypeError: pass
assert_eq(log, ["refused"])
del log[:]
g = nested("outer"); next(g)
try: g.throw(1)
except TypeError: pass
assert_eq(sorted(log), ["outer", "outer inner"])
del log[:]

# A traceback's frame keeps them, with the code and the last line; the
# generator dies without it.
g = gen("kept", "raise"); next(g)
try: next(g)
except ValueError as e: kept = e
frame = kept.__traceback__.tb_next.tb_frame
assert_eq((log, frame.f_generator, frame.f_code is g.gi_code, frame.f_lineno, g.gi_frame), ([], None, True, 19, None))
assert_eq(sorted(frame.f_locals), ["end", "local", "name"])
weak = host.weak_reference(g)
del g
assert_eq((weak() is None, log), (True, []))
del kept, frame
assert_eq(log, ["kept"])
del log[:]

# So does a gi_frame read while the generator ran.
g = gen("read", "return"); frame = g.gi_frame; next(g)
try: next(g)
except StopIteration: pass
assert_eq((log, frame.f_generator), ([], None))
del frame
assert_eq(log, ["read"])
del log[:]

# Inside a function, as at module level.
def inside():
    g = gen("inside", "raise"); next(g)
    try: next(g)
    except ValueError: pass
    return list(log)
assert_eq(inside(), ["inside"])
