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
