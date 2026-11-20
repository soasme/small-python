# spec: PLS-315 7.6.2
# description: int's and float's __divmod__, called explicitly, return
# NotImplemented for an operand they do not support, an instance or a
# float for int, never calling the operand's __rdivmod__; supported ones,
# bool and int or float subclasses, divide; divmod() of such a number and
# an instance then reaches the instance's __rdivmod__ once.
from harness import assert_eq

log = []

class Op:
    def __rdivmod__(self, other):
        for _ in (): pass
        log.append(("rdivmod", other))
        return ("r", other)
    def __index__(self): return 3
    def __float__(self): return 2.0

class Int(int): pass
class F(float): pass

def run(f):
    del log[:]
    try: result = f()
    except Exception as e: result = (type(e).__name__, str(e))
    return result, log[:]

cases = [
    (lambda: int.__divmod__(7, Op()), (NotImplemented, [])),
    (lambda: float.__divmod__(1.5, Op()), (NotImplemented, [])),
    (lambda: Int(7).__divmod__(Op()), (NotImplemented, [])),
    (lambda: F(7.5).__divmod__(Op()), (NotImplemented, [])),
    (lambda: int.__divmod__(7, 2.0), (NotImplemented, [])),
    (lambda: int.__divmod__(7, "a"), (NotImplemented, [])),
    (lambda: float.__divmod__(1.5, 2), ((0.0, 1.5), [])),
    (lambda: int.__divmod__(7, True), ((7, 0), [])),
    (lambda: int.__divmod__(7, Int(2)), ((3, 1), [])),
    (lambda: float.__divmod__(7.5, F(2)), ((3.0, 1.5), [])),
    (lambda: int.__divmod__(7, 0), (("ZeroDivisionError", "division by zero"), [])),
    (lambda: divmod(Int(7), Op()), (("r", 7), [("rdivmod", 7)])),
    (lambda: divmod(F(7.5), Op()), (("r", 7.5), [("rdivmod", 7.5)])),
    (lambda: divmod(7, Op()), (("r", 7), [("rdivmod", 7)])),
]
for i, (f, expected) in enumerate(cases):
    assert_eq(run(f), expected, str(i))

def inside():
    return [run(f) for f, _ in cases]
assert_eq(inside(), [e for _, e in cases])
