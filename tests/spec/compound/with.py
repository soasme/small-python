# spec: PLS-315 15.5, 7.9
# description: with statements and their __enter__/__exit__ calls.
from harness import *


class ContextManager:
    def __enter__(self):
        print('Entrada')
        ls.append(1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ls.append(2)
        print('Wiedersehen')

    def __str__(self):
        ls.append(3)
        return "c'est moi!"

ls = []
with ContextManager() as c:
    print(c)
assert ls == [1, 3, 2]

class ContextManager2:
    def __enter__(self):
        print('Ni hau')
        ls.append(4)
        return ls

    def __exit__(self, exc_type, exc_val, exc_tb):
        ls.append(5)
        print('Ajuus')

ls = []
with ContextManager2() as c:
    print(c)
    assert c == [4]
assert ls == [4, 5]

# Double context manager:
ls = []
with ContextManager() as c1, ContextManager2() as c2:
    print(c1)
    assert c2 == [1, 4, 3]
assert ls == [1, 4, 3, 5, 2]

# Context manager in return:

ls = []
def foo():
    with ContextManager():
        return
foo()
assert ls == [1, 2]

# Exception handling context manager:
class assertRaises:
    def __init__(self, tp):
        self.tp = tp

    def __enter__(self):
        print('Entering danger zone, but handling RuntimeError')

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is self.tp:
            print("Exception captured!")
            return True


with assertRaises(RuntimeError):
    raise RuntimeError('w00t')

# __exit__ runs at the line where its item's expression begins.
class ExitRaises:
    def __enter__(self): pass
    def __exit__(self, *exc): raise RuntimeError()
class Quiet:
    def __enter__(self): pass
    def __exit__(self, *exc): pass
def exit_line(body, code=None):
    try:
        body()
    except RuntimeError as e:
        code = code or body.__code__
        tb = e.__traceback__
        while tb.tb_frame.f_code is not code: tb = tb.tb_next
        return tb.tb_lineno - code.co_firstlineno
def first():
    with ExitRaises(), Quiet() as q:
        x = 1
        y = 2
def second():
    with (Quiet(),
          ExitRaises()):
        x = 1
def after_error():
    with ExitRaises():
        x = 1
        1 / 0
def gen_body():
    with Quiet(), \
         ExitRaises():
        yield 1
        x = 2
assert_eq((exit_line(first), exit_line(second), exit_line(after_error)), (1, 2, 1))
assert_eq(exit_line(lambda: list(gen_body()), gen_body.__code__), 2)
# A suspended body that raises reaches __exit__ at the item's line too.
def gen_raises():
    with ExitRaises():
        yield 1
        1 / 0
assert_eq(exit_line(lambda: list(gen_raises()), gen_raises.__code__), 1)
# A manager that does not suppress lets the error leave from its own line.
class Passes:
    def __enter__(self): pass
    def __exit__(self, *exc): return False
def gen_passes():
    with Passes():
        yield 1
        1 / 0
try:
    list(gen_passes())
except ZeroDivisionError as e:
    tb = e.__traceback__
    while tb.tb_frame.f_code is not gen_passes.__code__: tb = tb.tb_next
    assert_eq(tb.tb_lineno - gen_passes.__code__.co_firstlineno, 3)

# Inside a function, an __exit__ that loops sees how the body left: it
# ends normally, returns, breaks, or raises, which a true result
# suppresses; an exception __exit__ raises replaces the body's, whose
# frame line stays the line that raised it.
class Exiting:
    def __init__(self, suppress=False, fail=False): self.suppress, self.fail, self.seen = suppress, fail, []
    def __enter__(self): return self
    def __exit__(self, kind, value, tb):
        for _ in range(2): pass
        self.seen.append(kind)
        if self.fail: raise KeyError("exit")
        return self.suppress
def flows():
    out = []
    def returning(m):
        with m: return "returned"
    m = Exiting(); out.append(returning(m)); out.append(m.seen)
    m = Exiting()
    for i in range(3):
        with m:
            if i == 1: break
    out.append((i, m.seen))
    m = Exiting(suppress=True)
    with m: 1 / 0
    out.append(m.seen)
    for m in (Exiting(), Exiting(fail=True)):
        try:
            with m:
                raise ValueError("body")
        except Exception as e:
            out.append((type(e), m.seen, type(e.__context__)))
    def raising():
        with Exiting():
            1 / 0
    try:
        raising()
    except ZeroDivisionError as e:
        frame = e.__traceback__.tb_next.tb_frame
        out.append(frame.f_lineno - frame.f_code.co_firstlineno)
    return out
assert_eq(flows(), ["returned", [None], (1, [None, None]), [ZeroDivisionError],
                    (ValueError, [ValueError], type(None)), (KeyError, [ValueError], ValueError), 2])
