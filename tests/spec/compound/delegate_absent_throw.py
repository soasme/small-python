# spec: PLS-315 13.16.3, 27.2.2
# description: throw() of an exception, an instance or a class, into a
# generator suspended in a yield from of an iterator instance whose class
# has no throw method raises it at the yield from, a class instantiated
# there, and close() alike when it has no close: the generator's handler
# may loop and yield, throw() giving its value, while close() raises
# RuntimeError. A __getattr__ of the iterator is asked for the method
# first. Inside functions as at module level.
from harness import *

log = []
class Endless:
    def __iter__(self): return self
    def __next__(self):
        for _ in range(2): pass
        return 1
class Hooked(Endless):
    def __getattr__(self, name):
        log.append(("getattr", name))
        raise AttributeError(name)
class Exit(GeneratorExit): pass
class Made(Exception):
    def __init__(self): log.append("made"); super().__init__("m")
def outer(it):
    try:
        yield from it
    except BaseException as e:
        for _ in range(2): pass
        log.append(("caught", type(e).__name__, str(e)))
        yield "handled"
    finally:
        log.append("finally")
def run(it, how):
    g = outer(it); out = [next(g)]
    try:
        out.append(g.throw(how) if how is not None else g.close())
    except BaseException as e:
        out.append(type(e).__name__)
    return out
def throws():
    del log[:]
    return [run(Endless(), ValueError("v")), run(Endless(), KeyError), run(Endless(), Made), run(Hooked(), ValueError),
            run(Endless(), None), run(Endless(), Exit), run(Hooked(), None)], list(log)

expected = ([[1, 'handled'], [1, 'handled'], [1, 'handled'], [1, 'handled'], [1, 'RuntimeError'], [1, 'handled'], [1, 'RuntimeError']],
 [('caught', 'ValueError', 'v'), 'finally', ('caught', 'KeyError', ''), 'finally', 'made', ('caught', 'Made', 'm'), 'finally',
  ('getattr', 'throw'), ('caught', 'ValueError', ''), 'finally', ('caught', 'GeneratorExit', ''), 'finally',
  ('caught', 'Exit', ''), 'finally', ('getattr', 'close'), ('caught', 'GeneratorExit', ''), 'finally'])

def main():
    return throws()

assert_eq(main(), expected)
assert_eq(throws(), expected)
