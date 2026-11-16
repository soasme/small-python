# spec: PLS-315 25.5.2, 7.5.4
# description: A sequence repetition's count with __index__ whose int
# does not fit an index raises OverflowError naming the count's type, as
# ToIndexSize states: for list, tuple, str, bytes and bytearray, either
# operand order, in place, and through the explicit __mul__, __rmul__ and
# __imul__ methods, whether __index__ loops or not.
from harness import *

class Flat:
    def __index__(self):
        return 1 << 70

class Looping:
    def __index__(self):
        for _ in ():
            pass
        return 1 << 70

def message(f):
    try:
        f()
    except OverflowError as e:
        return str(e)
    return "no error"

def results():
    out = []
    for x in (Flat(), Looping(), 1 << 70):
        for s in ([1], (1,), "a", b"a", bytearray(b"a")):
            out.append(message(lambda: s * x))
            out.append(message(lambda: x * s))
            out.append(message(lambda: s.__mul__(x)))
            out.append(message(lambda: s.__rmul__(x)))
        for s in ([1], bytearray(b"a")):
            def inplace():
                t = s
                t *= x
            out.append(message(inplace))
            out.append(message(lambda: s.__imul__(x)))
    return out

expected = ["cannot fit 'Flat' into an index-sized integer", "cannot fit 'Flat' into an index-sized integer",
            "cannot fit 'Flat' into an index-sized integer", "cannot fit 'Flat' into an index-sized integer",
            "cannot fit 'Flat' into an index-sized integer", "cannot fit 'Flat' into an index-sized integer",
            "cannot fit 'Flat' into an index-sized integer", "cannot fit 'Flat' into an index-sized integer",
            "cannot fit 'Flat' into an index-sized integer", "cannot fit 'Flat' into an index-sized integer",
            "cannot fit 'Flat' into an index-sized integer", "cannot fit 'Flat' into an index-sized integer",
            "cannot fit 'Flat' into an index-sized integer", "cannot fit 'Flat' into an index-sized integer",
            "cannot fit 'Flat' into an index-sized integer", "cannot fit 'Flat' into an index-sized integer",
            "cannot fit 'Flat' into an index-sized integer", "cannot fit 'Flat' into an index-sized integer",
            "cannot fit 'Flat' into an index-sized integer", "cannot fit 'Flat' into an index-sized integer",
            "cannot fit 'Flat' into an index-sized integer", "cannot fit 'Flat' into an index-sized integer",
            "cannot fit 'Flat' into an index-sized integer", "cannot fit 'Flat' into an index-sized integer",
            "cannot fit 'Looping' into an index-sized integer", "cannot fit 'Looping' into an index-sized integer",
            "cannot fit 'Looping' into an index-sized integer", "cannot fit 'Looping' into an index-sized integer",
            "cannot fit 'Looping' into an index-sized integer", "cannot fit 'Looping' into an index-sized integer",
            "cannot fit 'Looping' into an index-sized integer", "cannot fit 'Looping' into an index-sized integer",
            "cannot fit 'Looping' into an index-sized integer", "cannot fit 'Looping' into an index-sized integer",
            "cannot fit 'Looping' into an index-sized integer", "cannot fit 'Looping' into an index-sized integer",
            "cannot fit 'Looping' into an index-sized integer", "cannot fit 'Looping' into an index-sized integer",
            "cannot fit 'Looping' into an index-sized integer", "cannot fit 'Looping' into an index-sized integer",
            "cannot fit 'Looping' into an index-sized integer", "cannot fit 'Looping' into an index-sized integer",
            "cannot fit 'Looping' into an index-sized integer", "cannot fit 'Looping' into an index-sized integer",
            "cannot fit 'Looping' into an index-sized integer", "cannot fit 'Looping' into an index-sized integer",
            "cannot fit 'Looping' into an index-sized integer", "cannot fit 'Looping' into an index-sized integer",
            "cannot fit 'int' into an index-sized integer", "cannot fit 'int' into an index-sized integer",
            "cannot fit 'int' into an index-sized integer", "cannot fit 'int' into an index-sized integer",
            "cannot fit 'int' into an index-sized integer", "cannot fit 'int' into an index-sized integer",
            "cannot fit 'int' into an index-sized integer", "cannot fit 'int' into an index-sized integer",
            "cannot fit 'int' into an index-sized integer", "cannot fit 'int' into an index-sized integer",
            "cannot fit 'int' into an index-sized integer", "cannot fit 'int' into an index-sized integer",
            "cannot fit 'int' into an index-sized integer", "cannot fit 'int' into an index-sized integer",
            "cannot fit 'int' into an index-sized integer", "cannot fit 'int' into an index-sized integer",
            "cannot fit 'int' into an index-sized integer", "cannot fit 'int' into an index-sized integer",
            "cannot fit 'int' into an index-sized integer", "cannot fit 'int' into an index-sized integer",
            "cannot fit 'int' into an index-sized integer", "cannot fit 'int' into an index-sized integer",
            "cannot fit 'int' into an index-sized integer", "cannot fit 'int' into an index-sized integer"]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
